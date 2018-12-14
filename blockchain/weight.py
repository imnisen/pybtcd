import btcutil
from .utxo_viewpoint import *

# MaxBlockWeight defines the maximum block weight, where "block
# weight" is interpreted as defined in BIP0141. A block's weight is
# calculated as the sum of the of bytes in the existing transactions
# and header, plus the weight of each byte within a transaction. The
# weight of a "base" byte is 4, while the weight of a witness byte is
# 1. As a result, for a block to be valid, the BlockWeight MUST be
# less than, or equal to MaxBlockWeight.
MaxBlockWeight = 4000000

# MaxBlockBaseSize is the maximum number of bytes within a block
# which can be allocated to non-witness data.
MaxBlockBaseSize = 1000000

# MaxBlockSigOpsCost is the maximum number of signature operations
# allowed for a block. It is calculated via a weighted algorithm which
# weights segregated witness sig ops lower than regular sig ops.
MaxBlockSigOpsCost = 80000

# WitnessScaleFactor determines the level of "discount" witness data
# receives compared to "base" data. A scale factor of 4, denotes that
# witness data is 1/4 as cheap as regular non-witness data.
WitnessScaleFactor = 4

# MinTxOutputWeight is the minimum possible weight for a transaction
# output.
MinTxOutputWeight = WitnessScaleFactor * wire.MinTxOutPayload

# MaxOutputsPerBlock is the maximum number of transaction outputs there
# can be in a block of max weight size.
MaxOutputsPerBlock = MaxBlockWeight // MinTxOutputWeight


# GetBlockWeight computes the value of the weight metric for a given block.
# Currently the weight metric is simply the sum of the block's serialized size
# without any witness data scaled proportionally by the WitnessScaleFactor,
# and the block's serialized size including any witness data.
def get_block_weight(blk: btcutil.Block) -> int:
    msg_block = blk.get_msg_block()
    base_size = msg_block.serialize_size_stripped()
    total_size = msg_block.serialize_size()

    # (baseSize * 3) + totalSize
    return (base_size * (WitnessScaleFactor - 1)) + total_size


# GetTransactionWeight computes the value of the weight metric for a given
# transaction. Currently the weight metric is simply the sum of the
# transactions's serialized size without any witness data scaled
# proportionally by the WitnessScaleFactor, and the transaction's serialized
# size including any witness data.
def get_transaction_weight(tx: btcutil.Tx) -> int:
    msg_tx = tx.get_msg_tx()

    base_size = msg_tx.serialize_size_stripped()
    total_size = msg_tx.serialize_size()

    # (baseSize * 3) + totalSize
    return (base_size * (WitnessScaleFactor - 1)) + total_size


# GetSigOpCost returns the unified sig op cost for the passed transaction
# respecting current active soft-forks which modified sig op cost counting.
# The unified sig op cost for a transaction is computed as the sum of: the
# legacy sig op count scaled according to the WitnessScaleFactor, the sig op
# count for all p2sh inputs scaled by the WitnessScaleFactor, and finally the
# unscaled sig op count for any inputs spending witness programs.
def get_sig_op_cost(tx: btcutil.Tx, is_coin_base_p: bool, utxo_view: UtxoViewpoint,
                    bip16_p: bool, seg_wit_p: bool) -> int:
    num_sig_ops = count_sig_ops(tx) * WitnessScaleFactor
    if bip16_p:
        num_p2sh_sig_ops = count_p2sh_sig_ops(tx, is_coin_base_p, utxo_view)
        num_sig_ops += num_p2sh_sig_ops * WitnessScaleFactor

    if seg_wit_p and not is_coin_base_p:
        msg_tx = tx.get_msg_tx()
        for i, tx_in in enumerate(msg_tx.tx_ins):
            # Ensure the referenced output is available and hasn't
            # already been spent.
            utxo = utxo_view.lookup_entry(tx_in.previous_out_point)
            if utxo is None or utxo.is_spent():
                msg = ("output %s referenced from " +
                       "transaction %s:%d either does not " +
                       "exist or has already been spent") % (
                          tx_in.previous_out_point, tx.hash(), i
                      )

                raise RuleError(ErrorCode.ErrMissingTxOut, msg)

            witness = tx_in.witness
            sig_script = tx_in.signature_script
            pk_script = utxo.pk_script
            num_sig_ops += txscript.get_witness_sig_op_count(sig_script, pk_script, witness)
    return num_sig_ops
