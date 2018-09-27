import unittest
from wire.msg_headers import *
from tests.utils import *

# blockOneHeader is the first block header in the mainnet block chain.
blockOneHeader = BlockHeader(
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
)

# mainNetGenesisHash is the hash of the first block in the block chain for the
# main network (genesis block).
mainNetGenesisHash = Hash(bytes([
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
]))


class TestMsgHeaders(unittest.TestCase):
    def setUp(self):
        self.pver = 60002
        bits = 0x1d00ffff
        nonce = 0x9962e301
        bh = BlockHeader(version=blockOneHeader.version, prev_block=mainNetGenesisHash,
                         merkle_root=blockOneHeader.merkle_root,
                         bits=bits, nonce=nonce, timestamp=blockOneHeader.timestamp)

        # Empty headers message.
        noHeaders = MsgHeaders()
        noHeadersEncoded = bytes([
            0x00,  # Varint for number of headers
        ])

        # Headers message with one header.
        oneHeader = MsgHeaders()
        oneHeader.add_block_header(bh)
        oneHeaderEncoded = bytes([
            0x01,  # VarInt for number of headers.
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
            0x00,  # TxnCount (0 for headers message)
        ])

        self.wire_tests = [
            # Latest protocol version with no headers.
            {"in": noHeaders, "out": noHeaders, "buf": noHeadersEncoded, "pver": ProtocolVersion, "enc": BaseEncoding},
            # Latest protocol version with one header.
            {"in": oneHeader, "out": oneHeader, "buf": oneHeaderEncoded, "pver": ProtocolVersion, "enc": BaseEncoding},

            # Protocol version BIP0035Version with no headers.
            {"in": noHeaders, "out": noHeaders, "buf": noHeadersEncoded, "pver": BIP0035Version, "enc": BaseEncoding},
            # Protocol version BIP0035Version with one header.
            {"in": oneHeader, "out": oneHeader, "buf": oneHeaderEncoded, "pver": BIP0035Version, "enc": BaseEncoding},

            # Protocol version BIP0031Version with no headers.
            {"in": noHeaders, "out": noHeaders, "buf": noHeadersEncoded, "pver": BIP0031Version, "enc": BaseEncoding},
            # Protocol version BIP0031Version with one header.
            {"in": oneHeader, "out": oneHeader, "buf": oneHeaderEncoded, "pver": BIP0031Version, "enc": BaseEncoding},

            # Protocol version NetAddressTimeVersion with no headers.
            {"in": noHeaders, "out": noHeaders, "buf": noHeadersEncoded, "pver": NetAddressTimeVersion,
             "enc": BaseEncoding},
            # Protocol version NetAddressTimeVersion with one header.
            {"in": oneHeader, "out": oneHeader, "buf": oneHeaderEncoded, "pver": NetAddressTimeVersion,
             "enc": BaseEncoding},

            # Protocol version MultipleAddressVersion with no headers.
            {"in": noHeaders, "out": noHeaders, "buf": noHeadersEncoded, "pver": MultipleAddressVersion,
             "enc": BaseEncoding},
            # Protocol version MultipleAddressVersion with one header.
            {"in": oneHeader, "out": oneHeader, "buf": oneHeaderEncoded, "pver": MultipleAddressVersion,
             "enc": BaseEncoding},

        ]

        # Message that forces an error by having more than the max allowed
        # headers.
        maxHeaders = MsgHeaders()
        for _ in range(MaxBlockHeadersPerMsg):
            maxHeaders.add_block_header(bh)
        maxHeaders.headers.append(bh)
        maxHeadersEncoded = bytes([
            0xfd, 0xd1, 0x07,  # Varint for number of addresses (2001)7D1
        ])

        # Intentionally invalid block header that has a transaction count used
        # to force errors.
        transHeader = MsgHeaders()
        transHeader.add_block_header(bh)  # TODO
        transHeaderEncoded = bytes([
            0x01,  # VarInt for number of headers.
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
            0x01,  # TxnCount (should be 0 for headers message, but 1 to force error)
        ])

        self.wire_err_tests = [
            # Latest protocol version with intentional read/write errors.
            # Force error in header count.
            {
                "in": oneHeader,
                "buf": oneHeaderEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },
            # Force error in block header.
            {
                "in": oneHeader,
                "buf": oneHeaderEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 5,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error with greater than max headers.
            {
                "in": maxHeaders,
                "buf": maxHeadersEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 3,
                "write_err": MaxBlockHeadersPerMsgMsgErr,
                "read_err": MaxBlockHeadersPerMsgMsgErr
            },

            # Force error with number of transactions.
            {
                "in": transHeader,
                "buf": transHeaderEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 81,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error with number of transactions.
            {
                "in": transHeader,
                "buf": transHeaderEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": len(transHeaderEncoded),
                "write_err": None,
                "read_err": BlockHeadersTxCountNotZeroMsgErr
            },

        ]

    def test_command(self):
        msg = MsgHeaders()
        self.assertEqual(str(msg.command()), "headers")

    def test_max_payload_length(self):
        msg = MsgHeaders()
        want_payload = 162009
        self.assertEqual(msg.max_payload_length(self.pver), want_payload)

    def test_add_block_header(self):
        msg = MsgHeaders()

        msg.add_block_header(blockOneHeader)

        self.assertEqual(msg.headers[0], blockOneHeader)

        # test MaxBlockHeadersPerMsg limit
        try:
            for _ in range(MaxBlockHeadersPerMsg):
                msg.add_block_header(blockOneHeader)
        except Exception as e:
            self.assertEqual(type(e), MaxBlockHeadersPerMsgMsgErr)

    def test_btc_encode(self):
        # Right condition
        for c in self.wire_tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

        # Wire error conditions
        for c in self.wire_err_tests:
            s = FixedBytesWriter(c['max'])

            if c['write_err']:
                try:
                    c['in'].btc_encode(s, c['pver'], c['enc'])
                except Exception as e:
                    self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        # Right condition
        for c in self.wire_tests:
            s = io.BytesIO(c['buf'])
            msg = MsgHeaders()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Wire error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgHeaders()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
