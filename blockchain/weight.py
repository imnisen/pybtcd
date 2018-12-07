import btcutil
from .utxo_viewpoint import *

# WitnessScaleFactor determines the level of "discount" witness data
# receives compared to "base" data. A scale factor of 4, denotes that
# witness data is 1/4 as cheap as regular non-witness data.
WitnessScaleFactor = 4


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


# TODO
# GetSigOpCost returns the unified sig op cost for the passed transaction
# respecting current active soft-forks which modified sig op cost counting.
# The unified sig op cost for a transaction is computed as the sum of: the
# legacy sig op count scaled according to the WitnessScaleFactor, the sig op
# count for all p2sh inputs scaled by the WitnessScaleFactor, and finally the
# unscaled sig op count for any inputs spending witness programs.
def get_sig_op_cost(tx: btcutil.Tx, is_coin_base_p: bool, utxo_view: UtxoViewpoint,
                    bip16_p: bool, seg_wit_p: bool) -> int:
    pass
