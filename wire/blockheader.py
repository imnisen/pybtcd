import io
from chainhash.hashfuncs import *
from .common import *

# MaxBlockHeaderPayload is the maximum number of bytes a block header can be.
# Version 4 bytes + Timestamp 4 bytes + Bits 4 bytes + Nonce 4 bytes +
# PrevBlock and MerkleRoot hashes.
MaxBlockHeaderPayload = 16 + (HashSize * 2)


# BlockHeader defines information about a block and is used in the bitcoin
# block (MsgBlock) and headers (MsgHeaders) messages.
class BlockHeader:
    def __init__(self, version, prev_block, merkle_root, timestamp, bits, nonce):
        """

        :param int32 version:
        :param chainhash.Hash prev_block:
        :param chainhash.Hash merkle_root:
        :param uint32 timestamp:
        :param uint32 bits:
        :param uint32 nonce:
        """

        self.version = version
        self.prev_block = prev_block
        self.merkle_root = merkle_root
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce

    def block_hash(self):
        """BlockHash computes the block identifier hash for the given block header."""

        # Encode the header and double sha256 everything prior to the number of
        # transactions.
        s = io.BytesIO()
        write_block_header(s, pver=0, bh=self)
        return double_hash_h(s.getvalue())

    def btc_encode(self, s, pver, enc):
        write_block_header(s, pver, self)
        return

    # TOCHECK this btc_decode use return value , not change self structure
    # Also ,this class doesn't inherit class `Message`
    def btc_decode(self, s, pver, enc):
        return read_block_header(s, pver)

    def serialize(self, s):
        write_block_header(s, 0, self)
        return

    def deserialize(self, s):
        return read_block_header(s, 0)


def read_block_header(s, pver):
    version = read_element(s, "int32")
    prev_block = read_element(s, "chainhash.Hash")
    merkle_root = read_element(s, "chainhash.Hash")
    timestamp = read_element(s, "uint32Time")
    bits = read_element(s, "uint32")
    nonce = read_element(s, "uint32")
    return BlockHeader(version=version,
                       prev_block=prev_block,
                       merkle_root=merkle_root,
                       timestamp=timestamp,
                       bits=bits,
                       nonce=nonce)


def write_block_header(s, pver, bh: BlockHeader):
    write_element(s, "int32", bh.version)
    write_element(s, "chainhash.Hash", bh.prev_block)
    write_element(s, "chainhash.Hash", bh.merkle_root)
    write_element(s, "uint32Time", bh.timestamp)
    write_element(s, "uint32", bh.bits)
    write_element(s, "uint32", bh.nonce)
    return
