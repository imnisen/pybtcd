import unittest
from wire.msg_block import *
from tests.utils import *

# blockOne is the first block in the mainnet block chain.
blockOne = MsgBlock(
    header=BlockHeader(
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
        timestamp=0x4966bc61,  # 2009-01-08 20:54:25 -0600 CST
        bits=0x1d00ffff,  # 486604799
        nonce=0x9962e301,  # 2573394689
    ),
    transactions=[
        MsgTx(
            version=1,
            tx_ins=[
                TxIn(
                    previous_out_point=OutPoint(
                        hash=Hash(),
                        index=0xffffffff
                    ),
                    signature_script=bytes([
                        0x04, 0xff, 0xff, 0x00, 0x1d, 0x01, 0x04,
                    ]),
                    sequence=0xffffffff

                ),
            ],
            tx_outs=[
                TxOut(
                    value=0x12a05f200,
                    pk_script=bytes([
                        0x41,  # OP_DATA_65
                        0x04, 0x96, 0xb5, 0x38, 0xe8, 0x53, 0x51, 0x9c,
                        0x72, 0x6a, 0x2c, 0x91, 0xe6, 0x1e, 0xc1, 0x16,
                        0x00, 0xae, 0x13, 0x90, 0x81, 0x3a, 0x62, 0x7c,
                        0x66, 0xfb, 0x8b, 0xe7, 0x94, 0x7b, 0xe6, 0x3c,
                        0x52, 0xda, 0x75, 0x89, 0x37, 0x95, 0x15, 0xd4,
                        0xe0, 0xa6, 0x04, 0xf8, 0x14, 0x17, 0x81, 0xe6,
                        0x22, 0x94, 0x72, 0x11, 0x66, 0xbf, 0x62, 0x1e,
                        0x73, 0xa8, 0x2c, 0xbf, 0x23, 0x42, 0xc8, 0x58,
                        0xee,  # 65-byte signature
                        0xac,  # OP_CHECKSIG
                    ])
                ),
            ],
            lock_time=0
        )
    ]
)

# Block one serialized bytes.
blockOneBytes = bytes([
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
    0x01,  # TxnCount
    0x01, 0x00, 0x00, 0x00,  # Version
    0x01,  # Varint for number of transaction inputs
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Previous output hash
    0xff, 0xff, 0xff, 0xff,  # Prevous output index
    0x07,  # Varint for length of signature script
    0x04, 0xff, 0xff, 0x00, 0x1d, 0x01, 0x04,  # Signature script (coinbase)
    0xff, 0xff, 0xff, 0xff,  # Sequence
    0x01,  # Varint for number of transaction outputs
    0x00, 0xf2, 0x05, 0x2a, 0x01, 0x00, 0x00, 0x00,  # Transaction amount
    0x43,  # Varint for length of pk script
    0x41,  # OP_DATA_65
    0x04, 0x96, 0xb5, 0x38, 0xe8, 0x53, 0x51, 0x9c,
    0x72, 0x6a, 0x2c, 0x91, 0xe6, 0x1e, 0xc1, 0x16,
    0x00, 0xae, 0x13, 0x90, 0x81, 0x3a, 0x62, 0x7c,
    0x66, 0xfb, 0x8b, 0xe7, 0x94, 0x7b, 0xe6, 0x3c,
    0x52, 0xda, 0x75, 0x89, 0x37, 0x95, 0x15, 0xd4,
    0xe0, 0xa6, 0x04, 0xf8, 0x14, 0x17, 0x81, 0xe6,
    0x22, 0x94, 0x72, 0x11, 0x66, 0xbf, 0x62, 0x1e,
    0x73, 0xa8, 0x2c, 0xbf, 0x23, 0x42, 0xc8, 0x58,
    0xee,  # 65-byte uncompressed public key
    0xac,  # OP_CHECKSIG
    0x00, 0x00, 0x00, 0x00,  # Lock time
])

blockOneTxLocs = [
    TxLoc(tx_start=81, tx_len=134),
]


class TesMsgtBlock(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.header = BlockHeader(
            version=blockOne.header.version,
            prev_block=blockOne.header.prev_block.copy(),
            merkle_root=blockOne.header.merkle_root.copy(),
            bits=blockOne.header.bits,
            nonce=blockOne.header.nonce,
        )

        # For wire test
        self.wire_tests = [

            # Latest protocol version.
            {
                "in": blockOne,
                "out": blockOne,
                "buf": blockOneBytes,
                "txLocs": blockOneTxLocs,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0035Version.
            {
                "in": blockOne,
                "out": blockOne,
                "buf": blockOneBytes,
                "txLocs": blockOneTxLocs,
                "pver": BIP0035Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version.
            {
                "in": blockOne,
                "out": blockOne,
                "buf": blockOneBytes,
                "txLocs": blockOneTxLocs,
                "pver": BIP0031Version,
                "enc": BaseEncoding
            },

            # Protocol version NetAddressTimeVersion.
            {
                "in": blockOne,
                "out": blockOne,
                "buf": blockOneBytes,
                "txLocs": blockOneTxLocs,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding
            },

            # Protocol version MultipleAddressVersion.
            {
                "in": blockOne,
                "out": blockOne,
                "buf": blockOneBytes,
                "txLocs": blockOneTxLocs,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding
            },

            # TOADD Add case for witnessy block

        ]

        # For wire error test
        self.wire_err_tests = [

            # Force error in version.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in prev block hash.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 4,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in merkle root.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 36,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in timestamp.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 68,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in difficulty bits.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 72,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in header nonce.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 76,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction count.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 80,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transactions.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 81,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

        ]

        # for serialize and deserialize test
        self.serialize_tests = [
            {
                "in": blockOne,
                "out": blockOne,
                "buf": blockOneBytes,
                "txLocs": blockOneTxLocs,
            }
        ]

        # for serialize and deserialize error test
        self.serialize_err_tests = [
            # Force error in version.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in prev block hash.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 4,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in merkle root.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 36,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in timestamp.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 68,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in difficulty bits.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 72,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in header nonce.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 76,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction count.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 80,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transactions.
            {
                "in": blockOne,
                "buf": blockOneBytes,
                "max": 81,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },
        ]

        # for overflow test
        self.overflow_tests = [
            {
                "buf": bytes([
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
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                    0xff,  # TxnCount
                ]),
                "pver": self.pver,
                "enc": BaseEncoding,
                "err": MaxTxPerBlockMsgErr
            }
        ]

    def test_command(self):
        msg = MsgBlock(header=self.header)
        self.assertEqual(str(msg.command()), "block")

    def test_max_payload_length(self):
        msg = MsgBlock(header=self.header)
        want_payload = 4000000
        self.assertEqual(msg.max_payload_length(self.pver), want_payload)

    def test_add_transaction(self):
        msg = MsgBlock(header=self.header)
        tx = blockOne.transactions[0].copy()
        msg.add_transaction(tx)

        self.assertEqual(msg.transactions[0], blockOne.transactions[0])

    def test_clear_transactions(self):
        msg = MsgBlock(header=self.header)
        tx = blockOne.transactions[0].copy()
        msg.add_transaction(tx)
        self.assertEqual(msg.transactions[0], blockOne.transactions[0])

        msg.clear_transactions()
        self.assertEqual(len(msg.transactions), 0)

    def test_tx_hashes(self):
        # Block 1, transaction 1 hash.
        hashStr = "0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098"
        wantHash = Hash(hashStr)

        self.assertEqual(blockOne.tx_hashes()[0], wantHash)

    def test_block_hash(self):
        # Block 1 hash
        hashStr = "839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048"
        wantHash = Hash(hashStr)

        self.assertEqual(blockOne.block_hash(), wantHash)

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
            msg = MsgBlock()
            s = io.BytesIO(c['buf'])
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgBlock()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

        # Overflow conditons
        for c in self.overflow_tests:
            s = io.BytesIO(c['buf'])
            try:
                msg = MsgBlock()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['err'])

    def test_serialize(self):
        # Right conditions
        for c in self.serialize_tests:
            s = io.BytesIO()
            c['in'].serialize(s)
            self.assertEqual(s.getvalue(), c['buf'])

        # Error conditions
        for c in self.serialize_err_tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].serialize(s)
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_deserialize(self):
        # Right conditions
        for c in self.serialize_tests:
            msg = MsgBlock()
            s = io.BytesIO(c['buf'])
            msg.deserialize(s)
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.serialize_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgBlock()
                msg.deserialize(s)
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

        # Overflow conditons
        for c in self.overflow_tests:
            s = io.BytesIO(c['buf'])
            try:
                msg = MsgBlock()
                msg.deserialize(s)
            except Exception as e:
                self.assertEqual(type(e), c['err'])

    def test_deserialize_tx_loc(self):
        # Right conditions
        for c in self.serialize_tests:
            msg = MsgBlock()
            s = io.BytesIO(c['buf'])
            tx_loc_lst = msg.deserialize_tx_loc(s)

            self.assertEqual(msg, c['out'])
            self.assertEqual(tx_loc_lst[0], c['txLocs'][0])

        # Error conditions
        for c in self.serialize_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgBlock()
                msg.deserialize_tx_loc(s)
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

        # Overflow conditons
        for c in self.overflow_tests:
            s = io.BytesIO(c['buf'])
            try:
                msg = MsgBlock()
                msg.deserialize_tx_loc(s)
            except Exception as e:
                self.assertEqual(type(e), c['err'])

    def test_serialize_size(self):
        #  Block with no transactions.
        noTxBlock = MsgBlock(header=blockOne.header)

        tests = [
            {
                "in": noTxBlock,
                "size": 81
            },
            {
                "in": blockOne,
                "size": len(blockOneBytes)
            },
        ]

        for c in tests:
            self.assertEqual(c['in'].serialize_size(), c['size'])
