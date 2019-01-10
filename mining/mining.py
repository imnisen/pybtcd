import logging
import pyutil
import btcutil
import chainhash
import wire
import blockchain
import chaincfg
import txscript
from .policy import *

# MinHighPriority is the minimum priority value that allows a
# transaction to be considered high priority.
MinHighPriority = btcutil.SatoshiPerBitcoin * 144.0 / 250

# blockHeaderOverhead is the max number of bytes it takes to serialize
# a block header and max possible transaction count.
blockHeaderOverhead = wire.MaxBlockHeaderPayload + wire.MaxVarIntPayload

# CoinbaseFlags is added to the coinbase script of a generated block
# and is used to monitor BIP16 support as well as blocks that are
# generated via btcd.
CoinbaseFlags = "/P2SH/btcd/"

logger = logging.getLogger(__name__)


# Just for continue outer loop
class GetOutOfLoop(Exception):
    pass


# TxDesc is a descriptor about a transaction in a transaction source along with
# additional metadata.
class TxDesc:
    def __init__(self, tx: btcutil.Tx, added: int, height: int, fee: int, fee_per_kb: int):
        """

        :param btcutil.Tx tx:
        :param int time,Time added:
        :param int int32 height:
        :param int int64 fee:
        :param int int64 fee_per_kb:
        """
        # Tx is the transaction associated with the entry.
        self.tx = tx

        # Added is the time when the entry was added to the source pool.
        self.added = added

        # Height is the block height when the entry was added to the the source
        self.height = height

        # Fee is the total fee the transaction associated with the entry pays.
        self.fee = fee

        # FeePerKB is the fee the transaction pays in Satoshi per 1000 bytes.
        self.fee_per_kb = fee_per_kb


# TxSource represents a source of transactions to consider for inclusion in
# new blocks.
#
# The interface contract requires that all of these methods are safe for
# concurrent access with respect to the source.
class TxSource:
    # LastUpdated returns the last time a transaction was added to or
    # removed from the source pool.
    def last_updated(self) -> int:
        raise NotImplementedError

    # MiningDescs returns a slice of mining descriptors for all the
    # transactions in the source pool.
    def minint_descs(self) -> [TxDesc]:
        raise NotImplementedError

    # HaveTransaction returns whether or not the passed transaction hash
    # exists in the source pool.
    def have_transaction(self, hash: chainhash.Hash) -> bool:
        raise NotImplementedError


# txPrioItem houses a transaction along with extra information that allows the
# transaction to be prioritized and track dependencies on other transactions
# which have not been mined into a block yet.
class TxPrioItem:
    def __init__(self, tx: btcutil.Tx, fee: int, priority: float, fee_per_kb: int, depends_on: set):
        """

        :param btcutil.Tx *btcutil.Tx tx:
        :param int int64 fee:
        :param float float64 priority:
        :param int int64 fee_per_kb:
        :param set map[chainhash.Hash]struct{} depends_on:
        """

        self.tx = tx
        self.fee = fee
        self.priority = priority
        self.fee_per_kb = fee_per_kb
        self.depends_on = depends_on


# BlockTemplate houses a block that has yet to be solved along with additional
# details about the fees and the number of signature operations for each
# transaction in the block.
class BlockTemplate:
    def __init__(self, block: wire.MsgBlock, fees: [int], sig_op_costs: [int], height: int, valid_pay_address: bool,
                 witness_commitment: bytes):
        """
        
        :param wire.MsgBlock *wire.MsgBlock block:
        :param [int] []int64 fees:
        :param [int] []int64 sig_op_costs:
        :param int int32 height:
        :param bool bool valid_pay_address:
        :param bytes []byte witness_commitment:
        """
        # Block is a block that is ready to be solved by miners.  Thus, it is
        # completely valid with the exception of satisfying the proof-of-work
        # requirement.
        self.block = block

        # Fees contains the amount of fees each transaction in the generated
        # template pays in base units.  Since the first transaction is the
        # coinbase, the first entry (offset 0) will contain the negative of the
        # sum of the fees of all other transactions.
        self.fees = fees

        # SigOpCosts contains the number of signature operations each
        # transaction in the generated template performs.
        self.sig_op_costs = sig_op_costs

        # Height is the height at which the block template connects to the main
        # chain.
        self.height = height

        # ValidPayAddress indicates whether or not the template coinbase pays
        # to an address or is redeemable by anyone.  See the documentation on
        # NewBlockTemplate for details on which this can be useful to generate
        # templates without a coinbase payment address.
        self.valid_pay_address = valid_pay_address

        # WitnessCommitment is a commitment to the witness data (if any)
        # within the block. This field will only be populted once segregated
        # witness has been activated, and the block contains a transaction
        # which has witness data.
        self.witness_commitment = witness_commitment


# BlkTmplGenerator provides a type that can be used to generate block templates
# based on a given mining policy and source of transactions to choose from.
# It also houses additional state required in order to ensure the templates
# are built on top of the current best chain and adhere to the consensus rules.
class BlkTmplGenerator:
    def __init__(self, policy: Policy, chain_params: chaincfg.Params, tx_source: TxSource,
                 chain: blockchain.BlockChain, time_source: blockchain.MedianTimeSource,
                 sig_cache: txscript.SigCache, hash_cache: txscript.HashCache):
        """

        :param Policy *Policy policy:
        :param chaincfg.Params *chaincfg.Params chain_params:
        :param TxSource TxSource tx_source:
        :param blockchain.BlockChain *blockchain.BlockChain chain:
        :param blockchain.MedianTimeSource blockchain.MedianTimeSource time_source:
        :param txscript.SigCache *txscript.SigCache sig_cache:
        :param txscript.HashCache *txscript.HashCache hash_cache:
        """

        self.policy = policy
        self.chain_params = chain_params
        self.tx_source = tx_source
        self.chain = chain
        self.time_source = time_source
        self.sig_cache = sig_cache
        self.hash_cache = hash_cache

    # NewBlockTemplate returns a new block template that is ready to be solved
    # using the transactions from the passed transaction source pool and a coinbase
    # that either pays to the passed address if it is not nil, or a coinbase that
    # is redeemable by anyone if the passed address is nil.  The nil address
    # functionality is useful since there are cases such as the getblocktemplate
    # RPC where external mining software is responsible for creating their own
    # coinbase which will replace the one generated for the block template.  Thus
    # the need to have configured address can be avoided.
    #
    # The transactions selected and included are prioritized according to several
    # factors.  First, each transaction has a priority calculated based on its
    # value, age of inputs, and size.  Transactions which consist of larger
    # amounts, older inputs, and small sizes have the highest priority.  Second, a
    # fee per kilobyte is calculated for each transaction.  Transactions with a
    # higher fee per kilobyte are preferred.  Finally, the block generation related
    # policy settings are all taken into account.
    #
    # Transactions which only spend outputs from other transactions already in the
    # block chain are immediately added to a priority queue which either
    # prioritizes based on the priority (then fee per kilobyte) or the fee per
    # kilobyte (then priority) depending on whether or not the BlockPrioritySize
    # policy setting allots space for high-priority transactions.  Transactions
    # which spend outputs from other transactions in the source pool are added to a
    # dependency map so they can be added to the priority queue once the
    # transactions they depend on have been included.
    #
    # Once the high-priority area (if configured) has been filled with
    # transactions, or the priority falls below what is considered high-priority,
    # the priority queue is updated to prioritize by fees per kilobyte (then
    # priority).
    #
    # When the fees per kilobyte drop below the TxMinFreeFee policy setting, the
    # transaction will be skipped unless the BlockMinSize policy setting is
    # nonzero, in which case the block will be filled with the low-fee/free
    # transactions until the block size reaches that minimum size.
    #
    # Any transactions which would cause the block to exceed the BlockMaxSize
    # policy setting, exceed the maximum allowed signature operations per block, or
    # otherwise cause the block to be invalid are skipped.
    #
    # Given the above, a block generated by this function is of the following form:
    #
    #   -----------------------------------  --  --
    #  |      Coinbase Transaction         |   |   |
    #  |-----------------------------------|   |   |
    #  |                                   |   |   | ----- policy.BlockPrioritySize
    #  |   High-priority Transactions      |   |   |
    #  |                                   |   |   |
    #  |-----------------------------------|   | --
    #  |                                   |   |
    #  |                                   |   |
    #  |                                   |   |--- policy.BlockMaxSize
    #  |  Transactions prioritized by fee  |   |
    #  |  until <= policy.TxMinFreeFee     |   |
    #  |                                   |   |
    #  |                                   |   |
    #  |                                   |   |
    #  |-----------------------------------|   |
    #  |  Low-fee/Non high-priority (free) |   |
    #  |  transactions (while block size   |   |
    #  |  <= policy.BlockMinSize)          |   |
    #   -----------------------------------  --
    def new_block_template(self, pay_to_addrss: btcutil.Address) -> BlockTemplate:
        # Extend the most recently known best block.
        best = self.chain.best_snapshot()
        next_block_height = best.height + 1

        # Create a standard coinbase transaction paying to the provided
        # address.  NOTE: The coinbase value will be updated to include the
        # fees from the selected transactions later after they have actually
        # been selected.  It is created here to detect any errors early
        # before potentially doing a lot of work below.  The extra nonce helps
        # ensure the transaction is not a duplicate transaction (paying the
        # same value to the same public key address would otherwise be an
        # identical transaction for block version 1).
        extra_nonce = 0
        coinbase_script = standard_coinbase_script(next_block_height, extra_nonce)

        coinbase_tx = create_coinbase_tx(self.chain_params, coinbase_script, next_block_height, pay_to_addrss)

        coinbase_sig_op_cost = blockchain.count_sig_ops(coinbase_tx) * blockchain.WitnessScaleFactor

        # Get the current source transactions and create a priority queue to
        # hold the transactions which are ready for inclusion into a block
        # along with some priority related and fee metadata.  Reserve the same
        # number of items that are available for the priority queue.  Also,
        # choose the initial sort order for the priority queue based on whether
        # or not there is an area allocated for high-priority transactions.
        source_txns = self.tx_source.minint_descs()
        sorted_by_fee = self.policy.block_priority_size == 0
        priority_queue = new_tx_priority_queue(len(source_txns), sorted_by_fee)

        # Create a slice to hold the transactions to be included in the
        # generated block with reserved space.  Also create a utxo view to
        # house all of the input transactions so multiple lookups can be
        # avoided.
        block_txns = [coinbase_tx]
        block_utxos = blockchain.UtxoViewpoint()

        # dependers is used to track transactions which depend on another
        # transaction in the source pool.  This, in conjunction with the
        # dependsOn map kept with each dependent transaction helps quickly
        # determine which dependent transactions are now eligible for inclusion
        # in the block once each transaction has been included.
        dependers = {}

        # Create slices to hold the fees and number of signature operations
        # for each of the selected transactions and add an entry for the
        # coinbase.  This allows the code below to simply append details about
        # a transaction as it is selected for inclusion in the final block.
        # However, since the total fees aren't known yet, use a dummy value for
        # the coinbase fee which will be updated later.
        tx_fees = [-1]  # Updated once known
        tx_sig_op_costs = [coinbase_sig_op_cost]

        logger.info("Considering %d transactions for inclusion to new block" % len(source_txns))

        for tx_desc in source_txns:

            # Note:This try...catch... is a workaround of label...continue label pattern
            try:
                # A block can't have more than one coinbase or contain
                # non-finalized transactions.
                tx = tx_desc.tx
                if tx.is_coin_base():
                    logger.info("Skipping coinbase tx %s" % tx.hash())
                    continue

                if not blockchain.is_finalized_transaction(tx, next_block_height, self.time_source.adjusted_time()):
                    logger.info("Skipping coinbase tx %s" % tx.hash())
                    continue

                # Fetch all of the utxos referenced by the this transaction.
                # NOTE: This intentionally does not fetch inputs from the
                # mempool since a transaction which depends on other
                # transactions in the mempool must come after those
                # dependencies in the final generated block.
                try:
                    utxos = self.chain.fetch_utxo_view(tx)
                except Exception as e:
                    logger.info("Unable to fetch utxo view for tx %s: %s" % (tx.Hash(), e))
                    continue

                # Setup dependencies for any transactions which reference
                # other transactions in the mempool so they can be properly
                # ordered below.
                prio_item = TxPrioItem(tx=tx)  # TODO set default
                for tx_in in tx.get_msg_tx().tx_ins:
                    origin_hash = tx_in.previous_out_point.hash
                    entry = utxos.lookup_entry(tx_in.previous_out_point)
                    if entry is None or entry.is_spent():
                        if not self.tx_source.have_transaction(origin_hash):
                            logger.info("Skipping tx %s because it references unspent output %s which is not available"
                                        % (tx.Hash(), tx_in.previous_out_point))
                            raise GetOutOfLoop

                        # The transaction is referencing another
                        # transaction in the source pool, so setup an
                        # ordering dependency.
                        deps = dependers.get(origin_hash)
                        exists = origin_hash in dependers
                        if not exists:
                            deps = {}
                            dependers[origin_hash] = deps

                        deps[prio_item.tx.hash()] = prio_item
                        if prio_item.depends_on is None:
                            prio_item.depends_on = set()

                        prio_item.depends_on.add(origin_hash)

                        # Skip the check below. We already know the
                        # referenced transaction is available.
                        continue  # TOCHECK why ?.  there is no check below already

                # Calculate the final transaction priority using the input
                # value age sum as well as the adjusted transaction size.  The
                # formula is: sum(inputValue * inputAge) / adjustedTxSize
                prio_item.priority = calc_priority(tx.get_msg_tx(), utxos, next_block_height)

                # Calculate the fee in Satoshi/kB.
                prio_item.fee_per_kb = tx_desc.fee_per_kb
                prio_item.fee = tx_desc.fee

                # Add the transaction to the priority queue to mark it ready
                # for inclusion in the block unless it has dependencies.
                if prio_item.depends_on is None:
                    priority_queue.push(prio_item)  # TODO

                # Merge the referenced outputs from the input transactions to
                # this transaction into the block utxo view.  This allows the
                # code below to avoid a second lookup.
                merge_utxo_view(block_utxos, utxos)


            except GetOutOfLoop:
                # This try catch is just an workaround of continue the outer loop
                continue

        logger.info("Priority queue len %d, dependers len %d" % (priority_queue.len(), len(dependers)))  # TODO

        # The starting block size is the size of the block header plus the max
        # possible transaction count size, plus the size of the coinbase
        # transaction.
        block_weight = blockHeaderOverhead * blockchain.WitnessScaleFactor + blockchain.get_transaction_weight(
            coinbase_tx)
        block_sig_op_cost = coinbase_sig_op_cost
        total_fees = 0

        # Query the version bits state to see if segwit has been activated, if
        # so then this means that we'll include any transactions with witness
        # data in the mempool, and also add the witness commitment as an
        # OP_RETURN output in the coinbase transaction.
        segwit_state = self.chain.threshold_state(chaincfg.DeploymentSegwit)

        segwit_active = segwit_state == blockchain.ThresholdState.ThresholdActive

        witness_included = False

        # Choose which transactions make it into the block.
        while priority_queue.len() > 0:  # TODO
            # Grab the highest priority (or highest fee per kilobyte
            # depending on the sort order) transaction.
            prio_item = priority_queue.pop()  # TODO
            tx = prio_item.tx

            # If segregated witness has not been activated yet, then we
            # shouldn't include any witness transactions in the block.
            if not segwit_active and tx.has_witness():
                continue

            # Otherwise, Keep track of if we've included a transaction
            # with witness data or not. If so, then we'll need to include
            # the witness commitment as the last output in the coinbase
            # transaction.
            elif segwit_active and not witness_included and tx.has_witness():
                # If we're about to include a transaction bearing
                # witness data, then we'll also need to include a
                # witness commitment in the coinbase transaction.
                # Therefore, we account for the additional weight
                # within the block with a model coinbase tx with a
                # witness commitment.
                coinbase_copy = btcutil.Tx.from_msg_tx(coinbase_tx.get_msg_tx().copy())
                coinbase_copy.get_msg_tx().tx_ins[0].witness = b"a" * blockchain.CoinbaseWitnessDataLen
                coinbase_copy.get_msg_tx().add_tx_out(wire.TxOut(
                    pk_script=b"a" * blockchain.CoinbaseWitnessPkScriptLength,
                    value=0  # TODO check the default value
                ))

                # In order to accurately account for the weight
                # addition due to this coinbase transaction, we'll add
                # the difference of the transaction before and after
                # the addition of the commitment to the block weight.
                weight_diff = blockchain.get_transaction_weight(coinbase_copy) - blockchain.get_transaction_weight(
                    coinbase_tx)

                block_weight += weight_diff
                witness_included = True

            # Grab any transactions which depend on this one.
            deps = dependers.get(tx.hash())

            # Enforce maximum block size.  Also check for overflow.
            tx_weight = blockchain.get_transaction_weight(tx)
            block_plus_tx_weight = block_weight + tx_weight

            if block_plus_tx_weight < block_weight or \
                    block_plus_tx_weight > pyutil.MaxUint32 or \
                    block_plus_tx_weight >= self.policy.block_max_weight:
                logger.info("Skipping tx %s because it would exceed the max block weight" % tx.hash())
                log_skipped_deps(tx, deps)
                continue

            # Enforce maximum signature operation cost per block.  Also
            # check for overflow.
            try:
                sig_op_cost = blockchain.get_sig_op_cost(tx, is_coin_base_p=False, utxo_view=block_utxos,
                                                         bip16_p=True, seg_wit_p=segwit_active)
            except Exception as e:
                logger.info("Skipping tx %s due to error in GetSigOpCost: %s" % (tx.hash(), e))
                log_skipped_deps(tx, deps)
                continue

            if block_sig_op_cost + sig_op_cost > pyutil.MaxInt64 or block_sig_op_cost + sig_op_cost > blockchain.MaxBlockSigOpsCost:
                logger.info("Skipping tx %s because it would exceed the maximum sigops per block" % tx.hash())
                log_skipped_deps(tx, deps)
                continue

            # Skip free transactions once the block is larger than the
            # minimum block size.
            if sorted_by_fee and prio_item.fee_per_kb < self.policy.tx_min_free_fee and block_plus_tx_weight >= self.policy.block_min_weight:
                logger.info(
                    "Skipping tx %s with feePerKB %d < TxMinFreeFee %d and block weight %d >= minBlockWeight %d" % (
                        tx.hash(), prio_item.fee_per_kb, self.policy.tx_min_free_fee, block_plus_tx_weight,
                        self.policy.block_min_weight
                    ))
                log_skipped_deps(tx, deps)
                continue

            # Prioritize by fee per kilobyte once the block is larger than
            # the priority size or there are no more high-priority
            # transactions.
            if not sorted_by_fee and (
                    block_plus_tx_weight >= self.policy.block_priority_size or prio_item.priority <= MinHighPriority):
                logger.info(("Switching to sort by fees per " +
                             "kilobyte blockSize %d >= BlockPrioritySize " +
                             "%d || priority %.2f <= minHighPriority %.2f") % (
                                block_plus_tx_weight, self.policy.block_priority_size, prio_item.priority,
                                MinHighPriority
                            ))

                sorted_by_fee = True
                priority_queue.set_less_func(tx_pq_by_fee)  # TODO

                # Put the transaction back into the priority queue and
                # skip it so it is re-priortized by fees if it won't
                # fit into the high-priority section or the priority
                # is too low.  Otherwise this transaction will be the
                # final one in the high-priority section, so just fall
                # though to the code below so it is added now.
                if block_plus_tx_weight > self.policy.block_priority_size or prio_item.priority < MinHighPriority:
                    priority_queue.push(prio_item)
                    continue

            # Ensure the transaction inputs pass all of the necessary
            # preconditions before allowing it to be added to the block.
            try:
                blockchain.check_transaction_inputs(tx, next_block_height, block_utxos, self.chain_params)
            except Exception as e:
                logger.info("Skipping tx %s due to error in CheckTransactionInputs: %s" % (tx.hash(), e))
                log_skipped_deps(tx, deps)
                continue

            try:
                blockchain.validate_transaction_scripts(tx, block_utxos, txscript.StandardVerifyFlags, self.sig_cache,
                                                        self.hash_cache)

            except Exception as e:
                logger.info("Skipping tx %s due to error in ValidateTransactionScripts: %s" % (tx.hash(), e))
                log_skipped_deps(tx, deps)
                continue

            # Spend the transaction inputs in the block utxo view and add
            # an entry for it to ensure any transactions which reference
            # this one have it available as an input and can ensure they
            # aren't double spending.
            spend_transaction(block_utxos, tx, next_block_height)

            # Add the transaction to the block, increment counters, and
            # save the fees and signature operation counts to the block
            # template.
            block_txns.append(tx)
            block_weight += tx_weight
            block_sig_op_cost += sig_op_cost
            total_fees += prio_item.fee
            tx_fees.append(prio_item.fee)
            tx_sig_op_costs.append(sig_op_cost)

            logger.info("Adding tx %s (priority %.2f, feePerKB %.2f)" % (
                prio_item.tx.hash(), prio_item.priority, prio_item.fee_per_kb
            ))

            # Add transactions which depend on this one (and also do not
            # have any other unsatisified dependencies) to the priority
            # queue.
            for item in deps.values():
                # Add the transaction to the priority queue if there
                # are no more dependencies after this one.
                item.depends_on.remove(tx.hash())

                if len(item.depends_on) == 0:
                    priority_queue.push(item)

        # Now that the actual transactions have been selected, update the
        # block weight for the real transaction count and coinbase value with
        # the total fees accordingly.
        block_weight -= wire.MaxVarIntPayload - wire.var_int_serialize_size(
            len(block_txns)) * blockchain.WitnessScaleFactor
        coinbase_tx.get_msg_tx().tx_outs[0].value += total_fees
        tx_fees[0] = 0 - total_fees

        # If segwit is active and we included transactions with witness data,
        # then we'll need to include a commitment to the witness data in an
        # OP_RETURN output within the coinbase transaction.
        witness_commitment = bytes()
        if witness_included:
            # The witness of the coinbase transaction MUST be exactly 32-bytes
            # of all zeroes.
            witness_nonce = bytes(blockchain.CoinbaseWitnessDataLen)
            coinbase_tx.get_msg_tx().tx_ins[0].witness = wire.TxWitness(witness_nonce)

            # Next, obtain the merkle root of a tree which consists of the
            # wtxid of all transactions in the block. The coinbase
            # transaction will have a special wtxid of all zeroes.
            witness_merkle_tree = blockchain.build_merkle_tree_store(block_txns, witness=True)
            witness_merkle_root = witness_merkle_tree[-1]

            # The preimage to the witness commitment is:
            # witnessRoot || coinbaseWitness
            witness_preimage = witness_merkle_root.to_bytes() + witness_nonce  # 64 bytes = 32 bytes + 32 bytes

            # The witness commitment itself is the double-sha256 of the
            # witness preimage generated above. With the commitment
            # generated, the witness script for the output is: OP_RETURN
            # OP_DATA_36 {0xaa21a9ed || witnessCommitment}. The leading
            # prefix is referred to as the "witness magic bytes".
            witness_commitment = chainhash.double_hash_b(witness_preimage)
            witness_script = blockchain.WitnessMagicBytes + witness_commitment

            # Finally, create the OP_RETURN carrying witness commitment
            # output as an additional output within the coinbase.
            commitment_output = wire.TxOut(
                value=0,
                pk_script=witness_script
            )
            coinbase_tx.get_msg_tx().tx_outs.append(commitment_output)

        # Calculate the required difficulty for the block.  The timestamp
        # is potentially adjusted to ensure it comes after the median time of
        # the last several blocks per the chain consensus rules.
        ts = median_adjusted_time(best, self.time_source)
        req_difficulty = self.chain.calc_next_required_difficulty(ts)

        # Calculate the next expected block version based on the state of the
        # rule change deployments.
        next_block_version = self.chain.calc_next_block_version()

        # Create a new block ready to be solved.
        merkles = blockchain.build_merkle_tree_store(block_txns, witness=False)

        msg_block = wire.MsgBlock()

        msg_block.header = wire.BlockHeader(
            version=next_block_version,
            prev_block=best.hash,
            merkle_root=merkles[-1],
            timestamp=ts,
            bits=req_difficulty
        )

        for tx in block_txns:
            msg_block.add_transaction(tx.get_msg_tx())

        # Finally, perform a full check on the created block against the chain
        # consensus rules to ensure it properly connects to the current best
        # chain with no issues.
        block = btcutil.Block.from_msg_block(msg_block)
        block.set_height(next_block_height)

        self.chain.check_connect_block_template(block)

        logger.info(("Created new block template (%d transactions, %d in " +
                     "fees, %d signature operations cost, %d weight, target difficulty " +
                     "%064x)") % (
                        len(msg_block.transactions), total_fees, block_sig_op_cost, block_weight,
                        blockchain.compact_to_big(msg_block.header.bits)
                    ))

        return BlockTemplate(
            block=msg_block,
            fees=tx_fees,
            sig_op_costs=tx_sig_op_costs,
            height=next_block_height,
            valid_pay_address=pay_to_addrss is not None,
            witness_commitment=witness_commitment
        )

    # UpdateBlockTime updates the timestamp in the header of the passed block to
    # the current time while taking into account the median time of the last
    # several blocks to ensure the new time is after that time per the chain
    # consensus rules.  Finally, it will update the target difficulty if needed
    # based on the new time for the test networks since their target difficulty can
    # change based upon time.
    def update_block_time(self, msg_block: wire.MsgBlock):
        # The new timestamp is potentially adjusted to ensure it comes after
        # the median time of the last several blocks per the chain consensus
        # rules.
        new_time = median_adjusted_time(self.chain.best_snapshot(), self.time_source)
        msg_block.header.timestamp = new_time

        # Recalculate the difficulty if running on a network that requires it.
        if self.chain_params.reduce_min_difficulty:
            difficulty = self.chain.calc_next_required_difficulty(new_time)
            msg_block.header.bits = difficulty
        return

    # UpdateExtraNonce updates the extra nonce in the coinbase script of the passed
    # block by regenerating the coinbase script with the passed value and block
    # height.  It also recalculates and updates the new merkle root that results
    # from changing the coinbase script.
    def update_extra_nonce(self, msg_block: wire.MsgBlock, block_height: int, extra_nonce: int):
        coinbase_script = standard_coinbase_script(block_height, extra_nonce)

        if len(coinbase_script) > blockchain.MaxCoinbaseScriptLen:
            raise Exception("coinbase transaction script length of %d is out of range (min: %d, max: %d)" % (
                len(coinbase_script), blockchain.MinCoinbaseScriptLen, blockchain.MaxCoinbaseScriptLen
            ))

        msg_block.transactions[0].tx_ins[0].signature_script = coinbase_script

        # TODO(davec): A btcutil.Block should use saved in the state to avoid
        # recalculating all of the other transaction hashes.
        # block.Transactions[0].InvalidateCache()

        # Recalculate the merkle root with the updated extra nonce.
        block = btcutil.Block.from_msg_block(msg_block)
        merkles = blockchain.build_merkle_tree_store(block.get_transactions(), witness=False)
        msg_block.header.merkle_root = merkles[-1]
        return

    # BestSnapshot returns information about the current best chain block and
    # related state as of the current point in time using the chain instance
    # associated with the block template generator.  The returned state must be
    # treated as immutable since it is shared by all callers.
    #
    # This function is safe for concurrent access.
    def best_snapshot(self) -> blockchain.BestState:
        return self.chain.best_snapshot()

    # TxSource returns the associated transaction source.
    #
    # This function is safe for concurrent access.
    def get_tx_source(self) -> TxSource:
        return self.tx_source


# TODO
class TxPriorityQueue:
    pass


# mergeUtxoView adds all of the entries in viewB to viewA.  The result is that
# viewA will contain all of its original entries plus all of the entries
# in viewB.  It will replace any entries in viewB which also exist in viewA
# if the entry in viewA is spent.
# Note: this method modify view_a
def merge_utxo_view(view_a: blockchain.UtxoViewpoint, view_b: blockchain.UtxoViewpoint):
    view_a_entries = view_a.get_entries()
    for outpoint, entry_b in view_b.get_entries().items():
        if outpoint not in view_a_entries or view_a_entries[outpoint] is None or view_a_entries[outpoint].is_spent():
            view_a_entries[outpoint] = entry_b
    return


# standardCoinbaseScript returns a standard script suitable for use as the
# signature script of the coinbase transaction of a new block.  In particular,
# it starts with the block height that is required by version 2 blocks and adds
# the extra nonce as well as additional coinbase flags.
def standard_coinbase_script(next_block_height: int, extra_nonce: int) -> bytes:
    return txscript.ScriptBuilder().add_int64(next_block_height). \
        add_int64(extra_nonce).add_data(CoinbaseFlags.encode()).script()


# createCoinbaseTx returns a coinbase transaction paying an appropriate subsidy
# based on the passed block height to the provided address.  When the address
# is nil, the coinbase transaction will instead be redeemable by anyone.
#
# See the comment for NewBlockTemplate for more information about why the nil
# address handling is useful.
def create_coinbase_tx(params: chaincfg.Params, coinbase_script: bytes, next_block_height: int,
                       addr: btcutil.Address) -> btcutil.Tx:
    # Create the script to pay to the provided payment address if one was
    # specified.  Otherwise create a script that allows the coinbase to be
    # redeemable by anyone.
    if addr is not None:
        pk_script = txscript.pay_to_addr_script(addr)
    else:
        script_builder = txscript.ScriptBuilder()
        pk_script = script_builder.add_op(txscript.OP_TRUE).script()

    tx = wire.MsgTx(version=wire.TxVersion)
    tx.add_tx_in(wire.TxIn(
        # Coinbase transactions have no inputs, so previous outpoint is
        # zero hash and max index.
        previous_out_point=wire.OutPoint(
            hash=chainhash.Hash(),
            index=wire.MaxPrevOutIndex
        ),
        signature_script=coinbase_script,
        sequence=wire.MaxTxInSequenceNum,
    ))

    tx.add_tx_out(wire.TxOut(
        value=blockchain.calc_block_subsidy(next_block_height, params),
        pk_script=pk_script
    ))

    return btcutil.Tx.from_msg_tx(tx)


# newTxPriorityQueue returns a new transaction priority queue that reserves the
# passed amount of space for the elements.  The new priority queue uses either
# the txPQByPriority or the txPQByFee compare function depending on the
# sortByFee parameter and is already initialized for use with heap.Push/Pop.
# The priority queue can grow larger than the reserved space, but extra copies
# of the underlying array can be avoided by reserving a sane value.
def new_tx_priority_queue(reverse: int, sort_by_fee: bool) -> TxPriorityQueue:
    pass  # TODO


# logSkippedDeps logs any dependencies which are also skipped as a result of
# skipping a transaction while generating a block template at the trace level.
def log_skipped_deps(tx: btcutil.Tx, deps: dict):
    if not deps:
        return

    for item in deps.items():
        logger.info("Skipping tx %s since it depends on %s\n" % (item.tx.hash(), tx.hash()))

    return


# spendTransaction updates the passed view by marking the inputs to the passed
# transaction as spent.  It also adds all outputs in the passed transaction
# which are not provably unspendable as available unspent transaction outputs.
def spend_transaction(utxo_view: blockchain.UtxoViewpoint, tx: btcutil.Tx, height: int):
    for tx_in in tx.get_msg_tx().tx_ins:
        entry = utxo_view.lookup_entry(tx_in.previous_out_point)
        if entry is not None:
            entry.spend()

    utxo_view.add_tx_outs(tx, height)
    return


# MinimumMedianTime returns the minimum allowed timestamp for a block building
# on the end of the provided best chain.  In particular, it is one second after
# the median timestamp of the last several blocks per the chain consensus
# rules.
def minimum_median_time(chain_state: blockchain.BestState) -> int:
    return chain_state.median_time + 1


# medianAdjustedTime returns the current time adjusted to ensure it is at least
# one second after the median timestamp of the last several blocks per the
# chain consensus rules.
def median_adjusted_time(chain_state: blockchain.BestState, time_source: blockchain.MedianTimeSource) -> int:
    # The timestamp for the block must not be before the median timestamp
    # of the last several blocks.  Thus, choose the maximum between the
    # current time and one second after the past median time.  The current
    # timestamp is truncated to a second boundary before comparison since a
    # block timestamp does not supported a precision greater than one
    # second.
    new_timestamp = time_source.adjusted_time()
    min_timestamp = minimum_median_time(chain_state)
    if new_timestamp < min_timestamp:
        new_timestamp = min_timestamp
    return new_timestamp
