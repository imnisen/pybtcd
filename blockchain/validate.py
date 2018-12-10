import btcutil
import wire
import pyutil
import chainhash
import txscript
import chaincfg
from .sequence_lock import *
from .block_index import *
from .weight import *
from .process import *


# --- Some constant ---
# medianTimeBlocks is the number of previous blocks which should be
# used to calculate the median time used to validate block timestamps.
medianTimeBlocks = 11

# serializedHeightVersion is the block version which changed block
# coinbases to start with the serialized block height.
serializedHeightVersion = 2

# baseSubsidy is the starting subsidy amount for mined blocks.  This
# value is halved every SubsidyHalvingInterval blocks.
baseSubsidy = 50 * btcutil.SatoshiPerBitcoin

# MinCoinbaseScriptLen is the minimum length a coinbase script can be.
MinCoinbaseScriptLen = 2

# MaxCoinbaseScriptLen is the maximum length a coinbase script can be.
MaxCoinbaseScriptLen = 100

# zeroHash is the zero value for a chainhash.Hash and is defined as
# a package level variable to avoid the need to create a new instance
# every time a check is needed.
zeroHash = chainhash.Hash()

# block91842Hash is one of the two nodes which violate the rules
# set forth in BIP0030.  It is defined as a package level variable to
# avoid the need to create a new instance every time a check is needed.
block91842Hash = chainhash.Hash("00000000000a4d0a398161ffc163c503763b1f4360639393e0e4c8e300e0caec")

# block91880Hash is one of the two nodes which violate the rules
# set forth in BIP0030.  It is defined as a package level variable to
# avoid the need to create a new instance every time a check is needed.
block91880Hash = chainhash.Hash("00000000000743f190a18c5577a3c2d2a1f610ae9601ac046a38084ccb7cd721")


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


# IsCoinBaseTx determines whether or not a transaction is a coinbase.  A coinbase
# is a special transaction created by miners that has no inputs.  This is
# represented in the block chain by a transaction with a single input that has
# a previous output transaction index set to the maximum value along with a
# zero hash.
#
# This function only differs from IsCoinBase in that it works with a raw wire
# transaction as opposed to a higher level util transaction.
def is_coin_base_tx(msg_tx: wire.MsgTx) -> bool:
    # A coin base must only have one transaction input.
    if len(msg_tx.tx_ins) != 1:
        return False

        # The previous output of a coin base must have a max value index and
    # a zero hash.
    prev_out = msg_tx.tx_ins[0].previous_out_point
    if prev_out.index != pyutil.MaxUint32 or prev_out.hash != zeroHash:
        return False

    return True


# IsCoinBase determines whether or not a transaction is a coinbase.  A coinbase
# is a special transaction created by miners that has no inputs.  This is
# represented in the block chain by a transaction with a single input that has
# a previous output transaction index set to the maximum value along with a
# zero hash.
#
# This function only differs from IsCoinBaseTx in that it works with a higher
# level util transaction as opposed to a raw wire transaction.
def is_coin_base(tx: btcutil.Tx) -> bool:
    return is_coin_base_tx(tx.get_msg_tx())


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
def is_bip003_node(node: BlockNode) -> bool:
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
    return baseSubsidy >> (height / chain_params.subsidy_reduction_interval)


# CheckTransactionSanity performs some preliminary checks on a transaction to
# ensure it is sane.  These checks are context free.
def calc_transaction_sanity(tx: btcutil.Tx):
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
    for tx_in in msg_tx.tx_outs:
        if tx_in in existing_tx_out:
            msg = "transaction contains duplicate inputs"
            raise RuleError(ErrorCode.ErrDuplicateTxInputs, msg)
        existing_tx_out[tx_in] = True

    # Coinbase script length must be between min and max length.
    if is_coin_base(tx):
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
    pass
