import io
import time
from chainhash.hashfuncs import *
from .common import *

# MaxBlockHeaderPayload is the maximum number of bytes a block header can be.
# Version 4 bytes + Timestamp 4 bytes + Bits 4 bytes + Nonce 4 bytes +
# PrevBlock and MerkleRoot hashes.
MaxBlockHeaderPayload = 16 + (HashSize * 2)


# BlockHeader defines information about a block and is used in the bitcoin
# block (MsgBlock) and headers (MsgHeaders) messages.
class BlockHeader:
    def __init__(self, version=None, prev_block=None, merkle_root=None, timestamp=None, bits=None, nonce=None):
        """

        :param int32 version:
        :param chainhash.Hash prev_block:
        :param chainhash.Hash merkle_root:
        :param uint32 timestamp:
        :param uint32 bits:
        :param uint32 nonce:
        """

        self.version = version or 0
        self.prev_block = prev_block or Hash()
        self.merkle_root = merkle_root or Hash()
        self.timestamp = timestamp or int(time.time())
        self.bits = bits or 0
        self.nonce = nonce or 0

    def __eq__(self, other):
        return self.version == other.version and \
               self.prev_block == other.prev_block and \
               self.merkle_root == other.merkle_root and \
               self.timestamp == other.timestamp and \
               self.bits == other.bits and \
               self.nonce == other.nonce

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
        self.version = read_element(s, "int32")
        self.prev_block = read_element(s, "chainhash.Hash")
        self.merkle_root = read_element(s, "chainhash.Hash")
        self.timestamp = read_element(s, "uint32Time")
        self.bits = read_element(s, "uint32")
        self.nonce = read_element(s, "uint32")
        return

    def serialize(self, s):
        write_block_header(s, 0, self)
        return

    def deserialize(self, s):
        self.version = read_element(s, "int32")
        self.prev_block = read_element(s, "chainhash.Hash")
        self.merkle_root = read_element(s, "chainhash.Hash")
        self.timestamp = read_element(s, "uint32Time")
        self.bits = read_element(s, "uint32")
        self.nonce = read_element(s, "uint32")
        return


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
