import btcutil
import chainhash
import wire
import blockchain
import chaincfg
import txscript
from .policy import *


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
        pass  # TODO

    # UpdateBlockTime updates the timestamp in the header of the passed block to
    # the current time while taking into account the median time of the last
    # several blocks to ensure the new time is after that time per the chain
    # consensus rules.  Finally, it will update the target difficulty if needed
    # based on the new time for the test networks since their target difficulty can
    # change based upon time.
    def update_block_time(self, msg_block: wire.MsgBlock):
        pass  # TODO

    # UpdateExtraNonce updates the extra nonce in the coinbase script of the passed
    # block by regenerating the coinbase script with the passed value and block
    # height.  It also recalculates and updates the new merkle root that results
    # from changing the coinbase script.
    def update_extra_nonce(self, msg_block: wire.MsgBlock, block_height: int, extra_nonce: int):
        pass  # TODO

    # BestSnapshot returns information about the current best chain block and
    # related state as of the current point in time using the chain instance
    # associated with the block template generator.  The returned state must be
    # treated as immutable since it is shared by all callers.
    #
    # This function is safe for concurrent access.
    def best_snapshot(self) -> blockchain.BestState:
        pass  # TODO

    # TxSource returns the associated transaction source.
    #
    # This function is safe for concurrent access.
    def tx_source(self) -> TxSource:
        pass  # TODO
