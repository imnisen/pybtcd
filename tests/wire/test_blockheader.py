import unittest
from wire.blockheader import *
from tests.utils import *

# mainNetGenesisHash is the hash of the first block in the block chain for the
# main network (genesis block).
mainNetGenesisHash = Hash(bytes([
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
]))

# mainNetGenesisMerkleRoot is the hash of the first transaction in the genesis
# block for the main network.
mainNetGenesisMerkleRoot = Hash(bytes([
    0x3b, 0xa3, 0xed, 0xfd, 0x7a, 0x7b, 0x12, 0xb2,
    0x7a, 0xc7, 0x2c, 0x3e, 0x67, 0x76, 0x8f, 0x61,
    0x7f, 0xc8, 0x1b, 0xc3, 0x88, 0x8a, 0x51, 0x32,
    0x3a, 0x9f, 0xb8, 0xaa, 0x4b, 0x1e, 0x5e, 0x4a,
]))


class TestBlockHeader(unittest.TestCase):
    def setUp(self):
        nonce64 = random_uint64()
        self.nonce = nonce64
        self.hash = mainNetGenesisHash
        self.merkleHash = mainNetGenesisMerkleRoot
        self.bits = 0x1d00ffff

    def test_init(self):
        bh = BlockHeader(version=1, prev_block=self.hash, merkle_root=self.merkleHash,
                         bits=self.bits, nonce=self.nonce)

        self.assertEqual(bh.prev_block, self.hash)
        self.assertEqual(bh.merkle_root, self.merkleHash)
        self.assertEqual(bh.bits, self.bits)
        self.assertEqual(bh.nonce, self.nonce)


class TestBlockHeaderWire(unittest.TestCase):
    def setUp(self):
        nonce = 123123
        self.pver = 70001

        # baseBlockHdr is used in the various tests as a baseline BlockHeader.
        bits = 0x1d00ffff
        baseBlockHdr = BlockHeader(version=1, prev_block=mainNetGenesisHash,
                                   merkle_root=mainNetGenesisMerkleRoot, bits=bits,
                                   nonce=nonce,
                                   timestamp=0x495fab29)

        baseBlockHdrEncoded = bytes([
            0x01, 0x00, 0x00, 0x00,  # Version 1
            0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
            0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
            0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
            0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,  # PrevBlock
            0x3b, 0xa3, 0xed, 0xfd, 0x7a, 0x7b, 0x12, 0xb2,
            0x7a, 0xc7, 0x2c, 0x3e, 0x67, 0x76, 0x8f, 0x61,
            0x7f, 0xc8, 0x1b, 0xc3, 0x88, 0x8a, 0x51, 0x32,
            0x3a, 0x9f, 0xb8, 0xaa, 0x4b, 0x1e, 0x5e, 0x4a,  # MerkleRoot
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0xff, 0xff, 0x00, 0x1d,  # Bits
            0xf3, 0xe0, 0x01, 0x00,  # Nonce
        ])

        self.tests = [

            # Latest protocol version.
            {
                "in": baseBlockHdr,
                "out": baseBlockHdr,
                "buf": baseBlockHdrEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0035Version.
            {
                "in": baseBlockHdr,
                "out": baseBlockHdr,
                "buf": baseBlockHdrEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version.
            {
                "in": baseBlockHdr,
                "out": baseBlockHdr,
                "buf": baseBlockHdrEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding
            },

            # Protocol version NetAddressTimeVersion.
            {
                "in": baseBlockHdr,
                "out": baseBlockHdr,
                "buf": baseBlockHdrEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding
            },

            # Protocol version MultipleAddressVersion.
            {
                "in": baseBlockHdr,
                "out": baseBlockHdr,
                "buf": baseBlockHdrEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding
            },

        ]

    def test_write_block_header(self):
        for c in self.tests:
            s = io.BytesIO()
            write_block_header(s, c['pver'], c['in'])
            self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], enc=0)
            self.assertEqual(s.getvalue(), c['buf'])

    def test_read_block_header(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            bh = read_block_header(s, c['pver'])
            self.assertEqual(bh, c['out'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            bh = BlockHeader()
            bh.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(bh, c['out'])


class TestBlockHeaderSerialize(unittest.TestCase):
    def setUp(self):
        nonce = 123123
        bits = 0x1d00ffff
        baseBlockHdr = BlockHeader(version=1,
                                   prev_block=mainNetGenesisHash,
                                   merkle_root=mainNetGenesisMerkleRoot,
                                   timestamp=0x495fab29,
                                   bits=bits,
                                   nonce=nonce)
        baseBlockHdrEncoded = bytes([
            0x01, 0x00, 0x00, 0x00,  # Version 1
            0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
            0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
            0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
            0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,  # PrevBlock
            0x3b, 0xa3, 0xed, 0xfd, 0x7a, 0x7b, 0x12, 0xb2,
            0x7a, 0xc7, 0x2c, 0x3e, 0x67, 0x76, 0x8f, 0x61,
            0x7f, 0xc8, 0x1b, 0xc3, 0x88, 0x8a, 0x51, 0x32,
            0x3a, 0x9f, 0xb8, 0xaa, 0x4b, 0x1e, 0x5e, 0x4a,  # MerkleRoot
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0xff, 0xff, 0x00, 0x1d,  # Bits
            0xf3, 0xe0, 0x01, 0x00,  # Nonce
        ])

        self.tests = [
            {
                "in": baseBlockHdr,
                "out": baseBlockHdr,
                "buf": baseBlockHdrEncoded,
            }
        ]

    def test_serialize(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].serialize(s)
            self.assertEqual(s.getvalue(), c['buf'])

    def test_deserialize(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            bh = BlockHeader()
            bh.deserialize(s)
            self.assertEqual(bh, c['out'])
