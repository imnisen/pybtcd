import btcutil
from blockchain.utxo_viewpoint import UtxoViewpoint


# loadBlocks reads files containing bitcoin block data (gzipped but otherwise
# in the format bitcoind writes) from disk and returns them as an array of
# btcutil.Block.  This is largely borrowed from the test code in btcdb.
def load_blocks(filename: str) -> [btcutil.Block]:
    pass



# loadUtxoView returns a utxo view loaded from a file.
def load_utxo_view(filename: str) -> UtxoViewpoint:
    pass