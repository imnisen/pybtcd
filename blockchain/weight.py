import btcutil

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
