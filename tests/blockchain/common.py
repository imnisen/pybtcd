import os
import btcutil
import wire
import bz2
import chainhash
from blockchain.utxo_viewpoint import UtxoViewpoint
from blockchain.chainio import deserialize_utxo_entry


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
                # print("1")
                break

            net = wire.BitcoinNet.from_int(int.from_bytes(b, byteorder="little"))
            if net != network:
                break

            # read block len
            b = f.read(4)
            if len(b) < 4:
                # print("2")
                break
            block_len = int.from_bytes(b, byteorder="little")

            # read block
            b = f.read(block_len)
            if len(b) < block_len:
                # print("3")
                break

            try:
                block = btcutil.Block.from_bytes(b)
            except Exception as e:
                # print('4')
                print(e)
                break

            blocks.append(block)
        return blocks

    finally:
        f.close()


# loadUtxoView returns a utxo view loaded from a file.
def load_utxo_view(filename: str) -> UtxoViewpoint:
    # The utxostore file format is:
    # <tx hash><output index><serialized utxo len><serialized utxo>
    #
    # The output index and serialized utxo len are little endian uint32s
    # and the serialized utxo uses the format described in chainio.go.
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata", filename)
    network = wire.BitcoinNet.MainNet
    if filename.endswith(".bz2"):
        f = bz2.open(filename, 'rb')
    else:
        f = open(filename, 'rb')

    try:
        view = UtxoViewpoint()
        while True:
            # read hash of the utxo entry.
            b = f.read(chainhash.HashSize)
            if len(b) < chainhash.HashSize:
                # print("1")
                break
            hash = chainhash.Hash(b)

            # read output index of the utxo entry.
            b = f.read(4)
            if len(b) < 4:
                # print("2")
                break
            index = int.from_bytes(b, byteorder="little")

            # Num of serialized utxo entry bytes.
            b = f.read(4)
            if len(b) < 4:
                # print("3")
                break
            num_bytes = int.from_bytes(b, byteorder="little")

            b = f.read(num_bytes)
            if len(b) < num_bytes:
                # print("4")
                break

            # Deserialize it and add it to the view.
            entry = deserialize_utxo_entry(b)

            view.entries[wire.OutPoint(hash=hash, index=index)] = entry

        return view
    finally:
        f.close()
