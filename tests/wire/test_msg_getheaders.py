import unittest
from tests.utils import *
from wire.msg_getheaders import *

# mainNetGenesisHash is the hash of the first block in the block chain for the
# main network (genesis block).
mainNetGenesisHash = Hash(bytes([
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
]))


class TestGetHeaders(unittest.TestCase):
    def test_command(self):
        msg = MsgGetHeaders()
        self.assertEqual(str(msg.command()), "getheaders")

    def test_max_payload_length(self):
        msg = MsgGetHeaders()
        want_payload = 16045
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_block_locator_hash(self):
        # Block 99500 hash.
        hashStr = "000000000002e7ad7b9eef9479e4aabc65cb831269cc20d2632c13684406dee0"
        locatorHash = Hash(hashStr)

        # Block 100000 hash.
        hashStr = "3ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"
        hashStop = Hash(hashStr)

        msg = MsgGetHeaders(hash_stop=hashStop)

        msg.add_block_locator_hash(locatorHash)
        self.assertEqual(msg.block_locator_hashes[0], locatorHash)

        try:
            for _ in range(MaxBlockLocatorsPerMsg):
                msg.add_block_locator_hash(locatorHash)
        except Exception as e:
            self.assertEqual(type(e), MaxBlockLocatorsPerMsgErr)


class TestGetHeadersWire(unittest.TestCase):
    def setUp(self):
        # Set protocol inside getheaders message.
        pver = 60002

        # Block 99499 hash.
        hashStr = "2710f40c87ec93d010a6fd95f42c59a2cbacc60b18cf6b7957535"
        hashLocator = Hash(hashStr)

        # Block 99500 hash.
        hashStr = "2e7ad7b9eef9479e4aabc65cb831269cc20d2632c13684406dee0"
        hashLocator2 = Hash(hashStr)

        # Block 100000 hash.
        hashStr = "3ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"
        hashStop = Hash(hashStr)

        noLocators = MsgGetHeaders(hash_stop=Hash(), protocol_version=pver)
        noLocatorsEncoded = bytes([
            0x62, 0xea, 0x00, 0x00,  # Protocol version 60002
            0x00,  # Varint for number of block locator hashes
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Hash stop
        ])

        # MsgGetHeaders message with multiple block locators and a stop hash.
        multiLocators = MsgGetHeaders(hash_stop=hashStop, protocol_version=pver)
        multiLocators.add_block_locator_hash(hashLocator2)
        multiLocators.add_block_locator_hash(hashLocator)
        multiLocatorsEncoded = bytes([
            0x62, 0xea, 0x00, 0x00,  # Protocol version 60002
            0x02,  # Varint for number of block locator hashes
            0xe0, 0xde, 0x06, 0x44, 0x68, 0x13, 0x2c, 0x63,
            0xd2, 0x20, 0xcc, 0x69, 0x12, 0x83, 0xcb, 0x65,
            0xbc, 0xaa, 0xe4, 0x79, 0x94, 0xef, 0x9e, 0x7b,
            0xad, 0xe7, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 99500 hash
            0x35, 0x75, 0x95, 0xb7, 0xf6, 0x8c, 0xb1, 0x60,
            0xcc, 0xba, 0x2c, 0x9a, 0xc5, 0x42, 0x5f, 0xd9,
            0x6f, 0x0a, 0x01, 0x3d, 0xc9, 0x7e, 0xc8, 0x40,
            0x0f, 0x71, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 99499 hash
            0x06, 0xe5, 0x33, 0xfd, 0x1a, 0xda, 0x86, 0x39,
            0x1f, 0x3f, 0x6c, 0x34, 0x32, 0x04, 0xb0, 0xd2,
            0x78, 0xd4, 0xaa, 0xec, 0x1c, 0x0b, 0x20, 0xaa,
            0x27, 0xba, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00,  # Hash stop

        ])

        self.tests = [
            # Latest protocol version with no block locators.
            {
                "in": noLocators,
                "out": noLocators,
                "buf": noLocatorsEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },

            # Latest protocol version with multiple block locators.
            {
                "in": multiLocators,
                "out": multiLocators,
                "buf": multiLocatorsEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },

            # Protocol version BIP0035Version with no block locators.
            {
                "in": noLocators,
                "out": noLocators,
                "buf": noLocatorsEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding,
            },

            #  Protocol version BIP0035Version with multiple block locators.
            {
                "in": multiLocators,
                "out": multiLocators,
                "buf": multiLocatorsEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding,
            },

            # Protocol version BIP0031Version with no block locators.
            {
                "in": noLocators,
                "out": noLocators,
                "buf": noLocatorsEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding,
            },

            #  Protocol version BIP0031Version with multiple block locators.
            {
                "in": multiLocators,
                "out": multiLocators,
                "buf": multiLocatorsEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding,
            },

            # Protocol version NetAddressTimeVersion with no block locators.
            {
                "in": noLocators,
                "out": noLocators,
                "buf": noLocatorsEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding,
            },

            #  Protocol version NetAddressTimeVersion with multiple block locators.
            {
                "in": multiLocators,
                "out": multiLocators,
                "buf": multiLocatorsEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding,
            },

            # Protocol version MultipleAddressVersion with no block locators.
            {
                "in": noLocators,
                "out": noLocators,
                "buf": noLocatorsEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding,
            },

            #  Protocol version MultipleAddressVersion with multiple block locators.
            {
                "in": multiLocators,
                "out": multiLocators,
                "buf": multiLocatorsEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding,
            },

        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgGetHeaders()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])


class TestGetHeadersWireErrors(unittest.TestCase):
    def setUp(self):
        # Set protocol inside getheaders message.
        pver = 60002

        # Block 99499 hash.
        hashStr = "2710f40c87ec93d010a6fd95f42c59a2cbacc60b18cf6b7957535"
        hashLocator = Hash(hashStr)

        # Block 99500 hash.
        hashStr = "2e7ad7b9eef9479e4aabc65cb831269cc20d2632c13684406dee0"
        hashLocator2 = Hash(hashStr)

        # Block 100000 hash.
        hashStr = "3ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"
        hashStop = Hash(hashStr)

        # MsgGetHeaders message with multiple block locators and a stop hash.
        baseGetHeaders = MsgGetHeaders(hash_stop=hashStop, protocol_version=pver)
        baseGetHeaders.add_block_locator_hash(hashLocator2)
        baseGetHeaders.add_block_locator_hash(hashLocator)
        baseGetHeadersEncoded = bytes([
            0x62, 0xea, 0x00, 0x00,  # Protocol version 60002
            0x02,  # Varint for number of block locator hashes
            0xe0, 0xde, 0x06, 0x44, 0x68, 0x13, 0x2c, 0x63,
            0xd2, 0x20, 0xcc, 0x69, 0x12, 0x83, 0xcb, 0x65,
            0xbc, 0xaa, 0xe4, 0x79, 0x94, 0xef, 0x9e, 0x7b,
            0xad, 0xe7, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 99500 hash
            0x35, 0x75, 0x95, 0xb7, 0xf6, 0x8c, 0xb1, 0x60,
            0xcc, 0xba, 0x2c, 0x9a, 0xc5, 0x42, 0x5f, 0xd9,
            0x6f, 0x0a, 0x01, 0x3d, 0xc9, 0x7e, 0xc8, 0x40,
            0x0f, 0x71, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 99499 hash
            0x06, 0xe5, 0x33, 0xfd, 0x1a, 0xda, 0x86, 0x39,
            0x1f, 0x3f, 0x6c, 0x34, 0x32, 0x04, 0xb0, 0xd2,
            0x78, 0xd4, 0xaa, 0xec, 0x1c, 0x0b, 0x20, 0xaa,
            0x27, 0xba, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00,  # Hash stop
        ])

        maxGetHeaders = MsgGetHeaders(hash_stop=hashStop)
        for _ in range(MaxBlockLocatorsPerMsg):
            maxGetHeaders.add_block_locator_hash(mainNetGenesisHash)

        maxGetHeaders.block_locator_hashes.append(mainNetGenesisHash)

        maxGetHeadersEncoded = bytes([
            0x62, 0xea, 0x00, 0x00,  # Protocol version 60002
            0xfd, 0xf5, 0x01,  # Varint for number of block loc hashes (501)
        ])

        self.tests = [
            # Force error in protocol version.
            {
                "in": baseGetHeaders,
                "buf": baseGetHeadersEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in block locator hash count.
            {
                "in": baseGetHeaders,
                "buf": baseGetHeadersEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 4,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in block locator hashes.
            {
                "in": baseGetHeaders,
                "buf": baseGetHeadersEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 5,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            #  Force error in stop hash.
            {
                "in": baseGetHeaders,
                "buf": baseGetHeadersEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 69,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error with greater than max block locator hashes.
            {
                "in": maxGetHeaders,
                "buf": maxGetHeadersEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 7,
                "write_err": MaxBlockLocatorsPerMsgErr,
                "read_err": MaxBlockLocatorsPerMsgErr,
            }
        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].btc_encode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        for c in self.tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgGetHeaders()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
