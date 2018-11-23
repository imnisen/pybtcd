import btcutil


# medianTimeBlocks is the number of previous blocks which should be
# used to calculate the median time used to validate block timestamps.
medianTimeBlocks = 11

def is_coin_base(tx: btcutil.Tx) -> bool:
    return # TODO