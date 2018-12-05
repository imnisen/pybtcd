import os
import btcutil
import wire
import bz2
from blockchain.utxo_viewpoint import UtxoViewpoint


# loadBlocks reads files containing bitcoin block data (gzipped but otherwise
# in the format bitcoind writes) from disk and returns them as an array of
# btcutil.Block.  This is largely borrowed from the test code in btcdb.
def load_blocks(filename: str) -> [btcutil.Block]:
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata", filename)
    network = wire.BitcoinNet.MainNet
    if filename.endswith(".bz2"):
        f = bz2.open(filename, 'rb')
    else:
        f = open(filename, 'rb')

    try:
        blocks = []
        while True:
            # read network
            b = f.read(4)
            if len(b) < 4:
                print("1")
                break

            net = wire.BitcoinNet.from_int(int.from_bytes(b, byteorder="little"))
            if net != network:
                break

            # read block len
            b = f.read(4)
            if len(b) < 4:
                print("2")
                break
            block_len = int.from_bytes(b, byteorder="little")

            # read block
            b = f.read(block_len)
            if len(b) < block_len:
                print("3")
                break

            try:
                block = btcutil.Block.from_bytes(b)
            except Exception as e:
                print('4')
                print(e)
                break

            blocks.append(block)
        return blocks

    finally:
        f.close()


# loadUtxoView returns a utxo view loaded from a file.
def load_utxo_view(filename: str) -> UtxoViewpoint:
    pass
