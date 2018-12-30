import chaincfg
from .sequence_lock import *
from .median_time import *
from .difficulty import *
from .process import *
from .merkle import *
from .weight import *


# isNullOutpoint determines whether or not a previous transaction output point
# is set.
def is_null_outpoint(outpoint: wire.OutPoint) -> bool:
    if outpoint.index == pyutil.MaxUint32 and outpoint.hash == zeroHash:
        return True
    return False


# ShouldHaveSerializedBlockHeight determines if a block should have a
# serialized block height embedded within the scriptSig of its
# coinbase transaction. Judgement is based on the block version in the block
# header. Blocks with version 2 and above satisfy this criteria. See BIP0034
# for further information.
def should_have_serialized_block_height(header: wire.BlockHeader) -> bool:
    return header.version >= serializedHeightVersion


# SequenceLockActive determines if a transaction's sequence locks have been
# met, meaning that all the inputs of a given transaction have reached a
# height or time sufficient for their relative lock-time maturity.
def sequence_lock_active(sequence_lock: SequenceLock, block_height: int, median_time_past: int) -> bool:
    # If either the seconds, or height relative-lock time has not yet
    # reached, then the transaction is not yet mature according to its
    # sequence locks.
    if sequence_lock.seconds >= median_time_past or sequence_lock.block_height >= block_height:
        return False

    return True


# IsFinalizedTransaction determines whether or not a transaction is finalized.
def is_finalized_transaction(tx: btcutil.Tx, block_height: int, block_time: int) -> bool:
    msg_tx = tx.get_msg_tx()

    # Lock time of zero means the transaction is finalized.
    lock_time = msg_tx.lock_time
    if lock_time == 0:
        return True

    # The lock time field of a transaction is either a block height at
    # which the transaction is finalized or a timestamp depending on if the
    # value is before the txscript.LockTimeThreshold.  When it is under the
    # threshold it is a block height.
    if lock_time < txscript.LockTimeThreshold:
        block_time_or_height = block_height
    else:
        block_time_or_height = block_time

    if lock_time < block_time_or_height:
        return True

    # At this point, the transaction's lock time hasn't occurred yet, but
    # the transaction might still be finalized if the sequence number
    # for all transaction inputs is maxed out.
    for tx_in in msg_tx.tx_ins:
        if tx_in.sequence != pyutil.MaxUint32:
            return False

    return False


# isBIP0030Node returns whether or not the passed node represents one of the
# two blocks that violate the BIP0030 rule which prevents transactions from
# overwriting old ones.
def is_bip003_node(node) -> bool:
    """
    :param BlockNode node:
    :return:
    """
    if node.height == 91842 and node.hash == block91842Hash:
        return True
    if node.height == 91880 and node.hash == block91880Hash:
        return True
    return False


# CalcBlockSubsidy returns the subsidy amount a block at the provided height
# should have. This is mainly used for determining how much the coinbase for
# newly generated blocks awards as well as validating the coinbase for blocks
# has the expected value.
#
# The subsidy is halved every SubsidyReductionInterval blocks.  Mathematically
# this is: baseSubsidy / 2^(height/SubsidyReductionInterval)
#
# At the target block generation rate for the main network, this is
# approximately every 4 years.
def calc_block_subsidy(height: int, chain_params: chaincfg.Params) -> int:
    if chain_params.subsidy_reduction_interval == 0:
        return baseSubsidy

    # Equivalent to: baseSubsidy / 2^(height/subsidyHalvingInterval)
    return baseSubsidy >> (height // chain_params.subsidy_reduction_interval)


# CheckTransactionSanity performs some preliminary checks on a transaction to
# ensure it is sane.  These checks are context free.
def check_transaction_sanity(tx: btcutil.Tx):
    # A transaction must have at least one input.
    msg_tx = tx.get_msg_tx()
    if len(msg_tx.tx_ins) == 0:
        raise RuleError(ErrorCode.ErrNoTxInputs, "transaction has no inputs")

    # A transaction must have at least one output.
    if len(msg_tx.tx_outs) == 0:
        raise RuleError(ErrorCode.ErrNoTxOutputs, "transaction has no outputs")

    # A transaction must not exceed the maximum allowed block payload when
    # serialized.
    serialize_tx_size = msg_tx.serialize_size_stripped()
    if serialize_tx_size > MaxBlockBaseSize:
        msg = "serialized transaction is too big - got %d, max %d" % (serialize_tx_size, MaxBlockBaseSize)
        raise RuleError(ErrorCode.ErrTxTooBig, msg)

    # Ensure the transaction amounts are in range.  Each transaction
    # output must not be negative or more than the max allowed per
    # transaction.  Also, the total of all outputs must abide by the same
    # restrictions.  All amounts in a transaction are in a unit value known
    # as a satoshi.  One bitcoin is a quantity of satoshi as defined by the
    # SatoshiPerBitcoin constant.
    total_sato_shi = 0
    for tx_out in msg_tx.tx_outs:
        satoshi = tx_out.value
        if satoshi < 0:
            msg = "transaction output has negative value of %s" % (satoshi)
            raise RuleError(ErrorCode.ErrBadTxOutValue, msg)

        if satoshi > btcutil.MaxSatoshi:
            msg = "transaction output value of %s is value of %s" % (satoshi)
            raise RuleError(ErrorCode.ErrBadTxOutValue, msg)

        # Check amount overflow
        # Two's complement int64 overflow guarantees that any overflow
        # is detected and reported.  This is impossible for Bitcoin, but
        # perhaps possible if an alt increases the total money supply.
        # TOADD
        total_sato_shi += satoshi
        if total_sato_shi > btcutil.MaxSatoshi:
            msg = "total value of all transaction outputs is %s which is higher than max allowed value of %s" % (
                total_sato_shi, btcutil.MaxSatoshi)
            raise RuleError(ErrorCode.ErrBadTxOutValue, msg)

    # Check for duplicate transaction inputs.
    existing_tx_out = {}
    for tx_in in msg_tx.tx_ins:
        if tx_in.previous_out_point in existing_tx_out:
            msg = "transaction contains duplicate inputs"
            raise RuleError(ErrorCode.ErrDuplicateTxInputs, msg)
        existing_tx_out[tx_in.previous_out_point] = True

    # Coinbase script length must be between min and max length.
    if tx.is_coin_base():
        s_len = len(msg_tx.tx_ins[0].signature_script)
        if not MinCoinbaseScriptLen <= s_len <= MaxCoinbaseScriptLen:
            msg = "coinbase transaction script length " + \
                  "of %d is out of range (min: %d, max: %d)" % (s_len, MinCoinbaseScriptLen, MaxCoinbaseScriptLen)
            raise RuleError(ErrorCode.ErrBadCoinbaseScriptLen, msg)
    else:
        # Previous transaction outputs referenced by the inputs to this
        # transaction must not be null.
        for tx_in in msg_tx.tx_ins:
            if is_null_outpoint(tx_in.previous_out_point):
                msg = "transaction " + \
                      "input refers to previous output that " + \
                      "is null"
                raise RuleError(ErrorCode.ErrBadTxInput, msg)

    return


# checkProofOfWork ensures the block header bits which indicate the target
# difficulty is in min/max range and that the block hash is less than the
# target difficulty as claimed.
#
# The flags modify the behavior of this function as follows:
#  - BFNoPoWCheck: The check to ensure the block hash is less than the target
#    difficulty is not performed.
def _check_proof_of_work(header: wire.BlockHeader, pow_limit: int, flags: BehaviorFlags):
    # The target difficulty must be larger than zero.
    target = compact_to_big(header.bits)
    if target <= 0:
        msg = "block target difficulty of %064x is too low" % target
        raise RuleError(ErrorCode.ErrBadTxInput, msg)

    # The target difficulty must be less than the maximum allowed.
    if target > pow_limit:
        msg = "block target difficulty of %064x is higher than max of %064x" % (target, pow_limit)
        raise RuleError(ErrorCode.ErrUnexpectedDifficulty, msg)

    # The block hash must be less than the claimed target unless the flag
    # to avoid proof of work checks is set.
    if flags & BFNoPoWCheck != BFNoPoWCheck:
        # The block hash must be less than the claimed target.
        hash = header.block_hash()
        hash_num = hash_to_big(hash)
        if hash_num > target:
            msg = "block hash of %064x is higher than expected max of %064x" % (hash_num, target)
            raise RuleError(ErrorCode.ErrHighHash, msg)

    return


# CheckProofOfWork ensures the block header bits which indicate the target
# difficulty is in min/max range and that the block hash is less than the
# target difficulty as claimed.
def check_proof_of_work(block: btcutil.Block, pow_limit: int):
    return _check_proof_of_work(block.get_msg_block().header, pow_limit, BFNone)


# checkBlockHeaderSanity performs some preliminary checks on a block header to
# ensure it is sane before continuing with processing.  These checks are
# context free.
#
# The flags do not modify the behavior of this function directly, however they
# are needed to pass along to checkProofOfWork.
def check_block_header_sanity(header: wire.BlockHeader, pow_limit: int,
                              time_source: MedianTimeSource, flags: BehaviorFlags):
    # Ensure the proof of work bits in the block header is in min/max range
    # and the block hash is less than the target value described by the
    # bits.
    _check_proof_of_work(header, pow_limit, flags)

    # A block timestamp must not have a greater precision than one second.
    # This check is necessary because Go time.Time values support
    # nanosecond precision whereas the consensus rules only apply to
    # seconds and it's much nicer to deal with standard Go time values
    # instead of converting to seconds everywhere.
    # No need here

    # Ensure the block time is not too far in the future.
    max_timestamp = time_source.adjusted_time() + MaxTimeOffsetSeconds
    if header.timestamp > max_timestamp:
        msg = "block timestamp of %s is too far in the future" % header.timestamp
        raise RuleError(ErrorCode.ErrTimeTooNew, msg)

    return


# checkBlockSanity performs some preliminary checks on a block to ensure it is
# sane before continuing with block processing.  These checks are context free.
#
# The flags do not modify the behavior of this function directly, however they
# are needed to pass along to checkBlockHeaderSanity.
def check_block_sanity_noexport(block: btcutil.block, pow_limit: int,
                                time_source: MedianTimeSource, flags: BehaviorFlags):
    # Check block header
    msg_block = block.get_msg_block()
    header = msg_block.header
    check_block_header_sanity(header=header, pow_limit=pow_limit,
                              time_source=time_source, flags=flags)

    # A block must have at least one transaction.

    num_tx = len(msg_block.transactions)
    if num_tx == 0:
        raise RuleError(ErrorCode.ErrNoTransactions, "block does not contain any transactions")

    # A block must not have more transactions than the max block payload or
    # else it is certainly over the weight limit.
    if num_tx > MaxBlockBaseSize:
        msg = "block contains too many transactions - got %d, max %d" % (num_tx, MaxBlockBaseSize)
        raise RuleError(ErrorCode.ErrBlockTooBig, msg)

    # A block must not exceed the maximum allowed block payload when
    # serialized.
    serialize_size = msg_block.serialize_size_stripped()
    if serialize_size > MaxBlockBaseSize:
        msg = "serialized block is too big - got %d, max %d" % (serialize_size, MaxBlockBaseSize)
        raise RuleError(ErrorCode.ErrBlockTooBig, msg)

    # The first transaction in a block must be a coinbase.
    transactions = block.get_transactions()
    if not transactions[0].is_coin_base():
        raise RuleError(ErrorCode.ErrFirstTxNotCoinbase, "first transaction in block is not a coinbase")

    # A block must not have more than one coinbase.
    for i, tx in enumerate(transactions[1:]):
        if tx.is_coin_base():
            msg = "block contains second coinbase at index %d" % (i + 1)
            raise RuleError(ErrorCode.ErrMultipleCoinbases, msg)

    # Do some preliminary checks on each transaction to ensure they are
    #  sane before continuing.
    for tx in transactions:
        check_transaction_sanity(tx)

    # Build merkle tree and ensure the calculated merkle root matches the
    # entry in the block header.  This also has the effect of caching all
    # of the transaction hashes in the block to speed up future hash
    # checks.  Bitcoind builds the tree here and checks the merkle root
    # after the following checks, but there is no reason not to check the
    # merkle root matches here.
    merkles = build_merkle_tree_store(block.get_transactions(), witness=False)
    calculated_merkle_root = merkles[-1]
    if header.merkle_root != calculated_merkle_root:
        msg = ("block merkle root is invalid - block " +
               "header indicates %s, but calculated value is %s") % (header.merkle_root, calculated_merkle_root)
        raise RuleError(ErrorCode.ErrBadMerkleRoot, msg)

    # Check for duplicate transactions.  This check will be fairly quick
    # since the transaction hashes are already cached due to building the
    # merkle tree above.
    existing_tx_hash = {}
    for tx in transactions:
        the_hash = tx.hash()
        if existing_tx_hash.get(the_hash):
            msg = "block contains duplicate transaction %s" % the_hash
            raise RuleError(ErrorCode.ErrDuplicateTx, msg)

        existing_tx_hash[the_hash] = True

    # The number of signature operations must be less than the maximum
    # allowed per block.
    total_sig_ops = 0
    for tx in transactions:
        total_sig_ops += count_sig_ops(tx) * WitnessScaleFactor
        if total_sig_ops > MaxBlockSigOpsCost:
            msg = "block contains too many signature operations - got %s, max %s" % (total_sig_ops, MaxBlockSigOpsCost)
            raise RuleError(ErrorCode.ErrTooManySigOps, msg)

    return


# CheckBlockSanity performs some preliminary checks on a block to ensure it is
# sane before continuing with block processing.  These checks are context free.
def check_block_sanity(block: btcutil.block, pow_limit: int, time_source: MedianTimeSource):
    return check_block_sanity_noexport(block, pow_limit, time_source, BFNone)


# ExtractCoinbaseHeight attempts to extract the height of the block from the
# scriptSig of a coinbase transaction.  Coinbase heights are only present in
# blocks of version 2 or later.  This was added as part of BIP0034.
def extract_coin_base_height(coin_base_tx: btcutil.Tx) -> int:
    sig_script = coin_base_tx.get_msg_tx().tx_ins[0].signature_script
    if len(sig_script) < 1:
        msg = ("the coinbase signature script for blocks of " +
               "version %d or greater must start with the " +
               "length of the serialized block height") % serializedHeightVersion
        raise RuleError(ErrorCode.ErrMissingCoinbaseHeight, msg)

    # Detect the case when the block height is a small integer encoded with
    # as single byte.
    opcode = sig_script[0]
    if opcode == txscript.OP_0:
        return 0

    if txscript.OP_1 <= opcode <= txscript.OP_16:
        return opcode - (txscript.OP_1 - 1)

    # Otherwise, the opcode is the length of the following bytes which
    # encode in the block height.
    serialized_len = sig_script[0]

    if len(sig_script[1:]) < serialized_len:
        msg = ("the coinbase signature script for blocks of " +
               "version %d or greater must start with the " +
               "serialized block height") % serialized_len
        raise RuleError(ErrorCode.ErrMissingCoinbaseHeight, msg)

    # TOCHECK
    serialized_height_bytes = sig_script[1: serialized_len + 1]
    if len(serialized_height_bytes) > 8:
        serialized_height_bytes = serialized_height_bytes[:8]

    serialized_height = int.from_bytes(serialized_height_bytes, 'little')
    return serialized_height


# checkSerializedHeight checks if the signature script in the passed
# transaction starts with the serialized block height of wantHeight.
def check_serialized_height(coin_base_tx: btcutil.Tx, want_height: int):
    serialized_height = extract_coin_base_height(coin_base_tx)

    if serialized_height != want_height:
        msg = "the coinbase signature script serialized block height is %d when %d was expected" % (
            serialized_height, want_height)
        raise RuleError(ErrorCode.ErrBadCoinbaseHeight, msg)

    return


# CheckTransactionInputs performs a series of checks on the inputs to a
# transaction to ensure they are valid.  An example of some of the checks
# include verifying all inputs exist, ensuring the coinbase seasoning
# requirements are met, detecting double spends, validating all values and fees
# are in the legal range and the total output amount doesn't exceed the input
# amount, and verifying the signatures to prove the spender was the owner of
# the bitcoins and therefore allowed to spend them.  As it checks the inputs,
# it also calculates the total fees for the transaction and returns that value.
#
# NOTE: The transaction MUST have already been sanity checked with the
# CheckTransactionSanity function prior to calling this function.
def check_transaction_inputs(tx: btcutil.Tx, tx_height: int, utxo_view: UtxoViewpoint,
                             chain_params: chaincfg.Params) -> int:
    # Coinbase transactions have no inputs.
    if tx.is_coin_base():
        return 0

    total_satoshi_in = 0
    for tx_in_idx, tx_in in enumerate(tx.get_msg_tx().tx_ins):
        # Ensure the referenced input transaction is available.
        utxo = utxo_view.lookup_entry(tx_in.previous_out_point)
        if utxo is None or utxo.is_spent():
            msg = ("output %s referenced from " +
                   "transaction %s:%d either does not exist or " +
                   "has already been spent") % (
                      tx_in.previous_out_point, tx.hash(), tx_in_idx
                  )
            raise RuleError(ErrorCode.ErrMissingTxOut, msg)

        # Ensure the transaction is not spending coins which have not
        # yet reached the required coinbase maturity.
        if utxo.is_coin_base():
            origin_height = utxo.get_block_height()
            blocks_since_prev = tx_height - origin_height
            coinbase_maturity = chain_params.coinbase_maturity
            if blocks_since_prev < coinbase_maturity:
                msg = ("tried to spend coinbase " +
                       "transaction output %s from height %s " +
                       "at height %s before required maturity " +
                       "of %s blocks") % (
                          tx_in.previous_out_point, origin_height, tx_height, coinbase_maturity
                      )
                raise RuleError(ErrorCode.ErrImmatureSpend, msg)

        # Ensure the transaction amounts are in range.  Each of the
        # output values of the input transactions must not be negative
        # or more than the max allowed per transaction.  All amounts in
        # a transaction are in a unit value known as a satoshi.  One
        # bitcoin is a quantity of satoshi as defined by the
        # SatoshiPerBitcoin constant.
        origin_tx_satoshi = utxo.get_amount()
        if origin_tx_satoshi < 0:
            msg = "transaction output has negative value of %s" % btcutil.Amount(origin_tx_satoshi)
            raise RuleError(ErrorCode.ErrBadTxOutValue, msg)

        if origin_tx_satoshi > btcutil.MaxSatoshi:
            msg = "transaction output value of %s is higher than max allowed value of %s" % (
                btcutil.Amount(origin_tx_satoshi), btcutil.MaxSatoshi
            )
            raise RuleError(ErrorCode.ErrBadTxOutValue, msg)

        # The total of all outputs must not be more than the max
        # allowed per transaction.  Also, we could potentially overflow
        # the accumulator so check for overflow.
        total_satoshi_in += origin_tx_satoshi
        if total_satoshi_in > pyutil.MaxInt64 or total_satoshi_in > btcutil.MaxSatoshi:
            msg = ("total value of all transaction " +
                   "inputs is %v which is higher than max " +
                   "allowed value of %v") % (
                      total_satoshi_in, btcutil.MaxSatoshi
                  )
            raise RuleError(ErrorCode.ErrBadTxOutValue, msg)

    # Calculate the total output amount for this transaction.  It is safe
    # to ignore overflow and out of range errors here because those error
    # conditions would have already been caught by checkTransactionSanity.
    total_satoshi_out = 0
    for tx_out in tx.get_msg_tx().tx_outs:
        total_satoshi_out += tx_out.value

    # Ensure the transaction does not spend more than its inputs.
    if total_satoshi_in < total_satoshi_out:
        msg = ("total value of all transaction inputs for " +
               "transaction %v is %v which is less than the amount " +
               "spent of %v") % (
                  tx.hash(), total_satoshi_in, total_satoshi_out
              )
        raise RuleError(ErrorCode.ErrSpendTooHigh, msg)

    # NOTE: bitcoind checks if the transaction fees are < 0 here, but that
    # is an impossible condition because of the check above that ensures
    # the inputs are >= the outputs.
    tx_fee_in_satoshi = total_satoshi_in - total_satoshi_out
    return tx_fee_in_satoshi
