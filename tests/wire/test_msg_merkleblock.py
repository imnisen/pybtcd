import unittest
from wire.msg_merkleblock import *
from tests.utils import *

# merkleBlockOne is the first block in the mainnet block chain.
merkleBlockOne = MsgMerkleBlock(
    header=BlockHeader(
        version=1,
        prev_block=Hash(bytes([
            0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
            0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
            0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
            0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00, ])
        ),
        merkle_root=Hash(bytes([
            0x98, 0x20, 0x51, 0xfd, 0x1e, 0x4b, 0xa7, 0x44,
            0xbb, 0xbe, 0x68, 0x0e, 0x1f, 0xee, 0x14, 0x67,
            0x7b, 0xa1, 0xa3, 0xc3, 0x54, 0x0b, 0xf7, 0xb1,
            0xcd, 0xb6, 0x06, 0xe8, 0x57, 0x23, 0x3e, 0x0e, ])
        ),
        timestamp=0x4966bc61,  # 2009-01-08 20:54:25 -0600 CST
        bits=0x1d00ffff,  # 486604799
        nonce=0x9962e301,  # 2573394689
    ),
    transactions=1,
    hashes=[
        Hash(bytes([
            0x98, 0x20, 0x51, 0xfd, 0x1e, 0x4b, 0xa7, 0x44,
            0xbb, 0xbe, 0x68, 0x0e, 0x1f, 0xee, 0x14, 0x67,
            0x7b, 0xa1, 0xa3, 0xc3, 0x54, 0x0b, 0xf7, 0xb1,
            0xcd, 0xb6, 0x06, 0xe8, 0x57, 0x23, 0x3e, 0x0e,
        ])),
    ],
    flags=bytes([0x80])
)

# merkleBlockOneBytes is the serialized bytes for a merkle block created from
# block one of the block chain where the first transaction matches.
merkleBlockOneBytes = bytes([
    0x01, 0x00, 0x00, 0x00,  # Version 1
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,  # PrevBlock
    0x98, 0x20, 0x51, 0xfd, 0x1e, 0x4b, 0xa7, 0x44,
    0xbb, 0xbe, 0x68, 0x0e, 0x1f, 0xee, 0x14, 0x67,
    0x7b, 0xa1, 0xa3, 0xc3, 0x54, 0x0b, 0xf7, 0xb1,
    0xcd, 0xb6, 0x06, 0xe8, 0x57, 0x23, 0x3e, 0x0e,  # MerkleRoot
    0x61, 0xbc, 0x66, 0x49,  # Timestamp
    0xff, 0xff, 0x00, 0x1d,  # Bits
    0x01, 0xe3, 0x62, 0x99,  # Nonce
    0x01, 0x00, 0x00, 0x00,  # TxnCount
    0x01,  # Num hashes
    0x98, 0x20, 0x51, 0xfd, 0x1e, 0x4b, 0xa7, 0x44,
    0xbb, 0xbe, 0x68, 0x0e, 0x1f, 0xee, 0x14, 0x67,
    0x7b, 0xa1, 0xa3, 0xc3, 0x54, 0x0b, 0xf7, 0xb1,
    0xcd, 0xb6, 0x06, 0xe8, 0x57, 0x23, 0x3e, 0x0e,  # Hash
    0x01,  # Num flag bytes
    0x80,  # Flags
])


class TesMsgtMerkleBlock(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.header = BlockHeader(
            version=1,
            prev_block=Hash(bytes([
                0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
                0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
                0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
                0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00])
            ),
            merkle_root=Hash(bytes([
                0x98, 0x20, 0x51, 0xfd, 0x1e, 0x4b, 0xa7, 0x44,
                0xbb, 0xbe, 0x68, 0x0e, 0x1f, 0xee, 0x14, 0x67,
                0x7b, 0xa1, 0xa3, 0xc3, 0x54, 0x0b, 0xf7, 0xb1,
                0xcd, 0xb6, 0x06, 0xe8, 0x57, 0x23, 0x3e, 0x0e])
            ),
            bits=0x1d00ffff,
            nonce=0x9962e301,
        )

        # For wire test
        self.wire_tests = [

            # Latest protocol version.
            {
                "in": merkleBlockOne,
                "out": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0037Version.
            {
                "in": merkleBlockOne,
                "out": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": BIP0037Version,
                "enc": BaseEncoding
            },

        ]

        # For wire error test
        pver = 70001
        pverNoMerkleBlock = BIP0037Version - 1
        self.wire_err_tests = [

            # Force error in version.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in prev block hash.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 4,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in merkle root.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 36,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in timestamp.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 68,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in difficulty bits.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 72,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in header nonce.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 76,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction count.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 80,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in num hashes.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 84,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in hashes.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 85,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in num flag bytes.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 117,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in flag bytes.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 118,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error due to unsupported protocol version.
            {
                "in": merkleBlockOne,
                "buf": merkleBlockOneBytes,
                "pver": pverNoMerkleBlock,
                "enc": BaseEncoding,
                "max": 119,
                "write_err": NotSupportBelowBIP37MsgErr,
                "read_err": NotSupportBelowBIP37MsgErr,
            },

        ]

        # for overflow test
        pver = 70001
        s = io.BytesIO()
        write_var_int(s, pver, maxTxPerBlock + 1)
        exceedMaxHashes = merkleBlockOneBytes[:84] + s.getvalue()

        s = io.BytesIO()
        write_var_int(s, pver, maxFlagsPerMerkleBlock + 1)
        exceedMaxFlagBytes = merkleBlockOneBytes[:117] + s.getvalue()

        self.overflow_tests = [
            {
                "buf": exceedMaxHashes,
                "pver": pver,
                "enc": BaseEncoding,
                "err": MaxTxPerBlockMsgErr
            },

            {
                "buf": exceedMaxFlagBytes,
                "pver": pver,
                "enc": BaseEncoding,
                "err": BytesTooLargeErr
            },
        ]

    def test_command(self):
        msg = MsgMerkleBlock(header=self.header)
        self.assertEqual(str(msg.command()), "merkleblock")

    def test_max_payload_length(self):
        msg = MsgMerkleBlock(header=self.header)
        want_payload = 4000000
        self.assertEqual(msg.max_payload_length(self.pver), want_payload)

    def test_add_tx_hash(self):
        msg = MsgMerkleBlock(header=self.header)

        hash = Hash("f051e59b5e2503ac626d03aaeac8ab7be2d72ba4b7e97119c5852d70d52dcb86")
        msg.add_tx_hash(hash.copy())
        self.assertEqual(msg.hashes[0], hash)

        try:
            for _ in range(maxTxPerBlock):
                msg.add_tx_hash(hash.copy())
        except Exception as e:
            self.assertEqual(type(e), MaxTxPerBlockMsgErr)

    def test_btc_encode(self):
        # Right conditions
        for c in self.wire_tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].btc_encode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        # Right conditions
        for c in self.wire_tests:
            msg = MsgMerkleBlock()
            s = io.BytesIO(c['buf'])
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgMerkleBlock()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

        # Overflow conditons
        for c in self.overflow_tests:
            s = io.BytesIO(c['buf'])
            try:
                msg = MsgMerkleBlock()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['err'])
