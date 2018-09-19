import unittest
from tests.utils import *
from wire.common import *

# mainNetGenesisHash is the hash of the first block in the block chain for the
# main network (genesis block).
mainNetGenesisHash = Hash(bytes([
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
]))


class TestElementWire(unittest.TestCase):
    def setUp(self):
        self.tests = [
            {
                "in": 1,
                "buf": bytes([0x01, 0x00, 0x00, 0x00]),
                "type": "int32"
            },
            {
                "in": 256,
                "buf": bytes([0x00, 0x01, 0x00, 0x00]),
                "type": "uint32"
            },
            {
                "in": 65536,
                "buf": bytes([0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "type": "int64"
            },
            {
                "in": 4294967296,
                "buf": bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00]),
                "type": "uint64"
            },
            {
                "in": True,
                "buf": bytes([0x01]),
                "type": "bool"
            },
            {
                "in": False,
                "buf": bytes([0x00]),
                "type": "bool"
            },
            {
                "in": bytes([0x01, 0x02, 0x03, 0x04]),
                "buf": bytes([0x01, 0x02, 0x03, 0x04]),
                "type": "[4]byte"
            },
            {
                "in": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, ]),
                "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, ]),
                "type": "[CommandSize]byte"

            },
            {
                "in": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                             0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, ]),
                "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                              0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, ]),
                "type": "[16]byte"

            },
            {
                "in": Hash(bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                                  0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
                                  0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                                  0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, ])),
                "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                              0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
                              0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                              0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, ]),
                "type": "chainhash.Hash"

            },
            {
                "in": ServiceFlag.SFNodeNetwork,
                "buf": bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "type": "ServiceFlag"
            },
            {
                "in": InvType.InvTypeTx,
                "buf": bytes([0x01, 0x00, 0x00, 0x00]),
                "type": "InvType"
            },
            {
                "in": BitcoinNet.MainNet,
                "buf": bytes([0xf9, 0xbe, 0xb4, 0xd9]),
                "type": "BitcoinNet"
            },
            #  TOADD Type not supported by the "fast" path and requires reflection.
            # {
            #     writeElementReflect(1),
            #     []byte{0x01, 0x00, 0x00, 0x00},
            # },

        ]

    # def test_write_element(self):
    #     for c in self.tests:
    #         s = io.BytesIO()
    #         write_element(s, c['type'], c['in'])
    #         self.assertEqual(s.getvalue(), c['buf'])
    #
    # def test_read_element(self):
    #     for c in self.tests:
    #         s = io.BytesIO(c['buf'])
    #         read_element(s, c['in'])
    #         self.assertEqual(s.getvalue(), c['buf'])


class TestElementWireErrors(unittest.TestCase):
    pass


class TestVarIntWire(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.tests = [
            # Single byte
            {
                "in": 0,
                "out": 0,
                "buf": bytes([0x00]),
                "pver": self.pver
            },

            # Max single byte
            {
                "in": 0xfc,
                "out": 0xfc,
                "buf": bytes([0xfc]),
                "pver": self.pver
            },

            # Min 2-byte
            {
                "in": 0xfd,
                "out": 0xfd,
                "buf": bytes([0xfd, 0x0fd, 0x00]),
                "pver": self.pver
            },

            # Max 2-byte
            {
                "in": 0xffff,
                "out": 0xffff,
                "buf": bytes([0xfd, 0xff, 0xff]),
                "pver": self.pver
            },

            # Min 4-byte
            {
                "in": 0x10000,
                "out": 0x10000,
                "buf": bytes([0xfe, 0x00, 0x00, 0x01, 0x00]),
                "pver": self.pver
            },

            # Max 4-byte
            {
                "in": 0xffffffff,
                "out": 0xffffffff,
                "buf": bytes([0xfe, 0xff, 0xff, 0xff, 0xff]),
                "pver": self.pver
            },

            # Min 8-byte
            {
                "in": 0x100000000,
                "out": 0x100000000,
                "buf": bytes([0xff, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00]),
                "pver": self.pver
            },

            # Max 8-byte
            {
                "in": 0xffffffffffffffff,
                "out": 0xffffffffffffffff,
                "buf": bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]),
                "pver": self.pver
            }
        ]

    def test_read_var_int(self):
        for c in self.tests:
            self.assertEqual(read_var_int(io.BytesIO(c['buf']), c['pver']), c['out'])

    def test_write_var_int(self):
        for c in self.tests:
            writer = io.BytesIO()
            write_var_int(writer, c['pver'], c['in'])
            writer.seek(0)
            self.assertEqual(writer.read(), c['buf'])


class TestVarIntWireErrors(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.tests = [
            # Force errors on discriminant.
            {
                "in": 0,
                "buf": bytes([0x00]),
                "pver": self.pver,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force errors on 2-byte read/write.
            {
                "in": 0xfd,
                "buf": bytes([0xfd]),
                "pver": self.pver,
                "max": 2,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force errors on 4-byte read/write.
            {
                "in": 0x10000,
                "buf": bytes([0xfe]),
                "pver": self.pver,
                "max": 2,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force errors on 8-byte read/write.
            {
                "in": 0x100000000,
                "buf": bytes([0xff]),
                "pver": self.pver,
                "max": 2,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

        ]

    def test_read_var_int(self):
        for c in self.tests:
            reader = FixedBytesReader(c["max"], c["buf"])
            try:
                read_var_int(reader, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

    def test_write_var_int(self):
        for c in self.tests:
            writer = FixedBytesWriter(c["max"])
            try:
                write_var_int(writer, c['pver'], c["in"])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])


class TestVarIntNonCanonicat(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.tests = [
            {
                "name": "0 encoded with 3 bytes",
                "in": bytes([0xfd, 0x00, 0x00]),
                "pver": self.pver,
            },

            {
                "name": "max single-byte value encoded with 3 bytes",
                "in": bytes([0xfd, 0xfc, 0x00]),
                "pver": self.pver,
            },

            {
                "name": "0 encoded with 5 bytes",
                "in": bytes([0xfe, 0x00, 0x00, 0x00, 0x00]),
                "pver": self.pver,
            },

            {
                "name": "max three-byte value encoded with 5 bytes",
                "in": bytes([0xfe, 0xff, 0xff, 0x00, 0x00]),
                "pver": self.pver,
            },

            {
                "name": "0 encoded with 9 bytes",
                "in": bytes([0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": self.pver,
            },

            {
                "name": "max five-byte value encoded with 9 bytes",
                "in": bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00]),
                "pver": self.pver,
            },
        ]

    def test_read_var_int(self):
        for c in self.tests:
            reader = io.BytesIO(c['in'])
            try:
                read_var_int(reader, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), NonCanonicalVarIntErr)


class TestVarIntSerializeSize(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.tests = [
            # Single byte
            {
                "val": 0,
                "size": 1
            },

            # Max single byte
            {
                "val": 0xfc,
                "size": 1
            },

            # Min 2-byte
            {
                "val": 0xfd,
                "size": 3
            },

            # Max 2-byte
            {
                "val": 0xffff,
                "size": 3
            },

            # Min 4-byte
            {
                "val": 0x10000,
                "size": 5
            },

            # Max 4-byte
            {
                "val": 0xffffffff,
                "size": 5
            },

            # Min 8-byte
            {
                "val": 0x100000000,
                "size": 9
            },

            # Max 8-byte
            {
                "val": 0xffffffffffffffff,
                "size": 9
            },

        ]

    def test_var_int_serialize_size(self):
        for c in self.tests:
            self.assertEqual(var_int_serialize_size(c['val']), c['size'])


class TestVarStringWire(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.str256 = "test" * 64
        self.tests = [

            # Empty string
            {
                "in": "",
                "out": "",
                "buf": bytes([0x00]),
                "pver": self.pver
            },

            # Single byte varint + string
            {
                "in": "Test",
                "out": "Test",
                "buf": bytes([0x04]) + bytes("Test".encode()),
                "pver": self.pver
            },

            # 2-byte varint + string
            {
                "in": self.str256,
                "out": self.str256,
                "buf": bytes([0xfd, 0x00, 0x01]) + bytes(self.str256.encode()),
                "pver": self.pver
            },
        ]

    def test_read_var_string(self):
        for c in self.tests:
            self.assertEqual(read_var_string(io.BytesIO(c['buf']), c['pver']), c['out'])

    def test_write_var_string(self):
        for c in self.tests:
            writer = io.BytesIO()
            write_var_string(writer, c['pver'], c['in'])
            writer.seek(0)
            self.assertEqual(writer.read(), c['buf'])


class TestVarStringWireErrors(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.str256 = "test" * 64
        self.tests = [
            # Force errors on empty string.
            {
                "in": "",
                "buf": bytes([0x00]),
                "pver": self.pver,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error on single byte varint + string.
            {
                "in": "Test",
                "buf": bytes([0x04]),
                "pver": self.pver,
                "max": 2,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on 2-byte varint + string.
            {
                "in": self.str256,
                "buf": bytes([0xfd]),
                "pver": self.pver,
                "max": 2,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },
        ]

    def test_read_var_string(self):
        for c in self.tests:
            reader = FixedBytesReader(c["max"], c["buf"])
            try:
                read_var_string(reader, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

    def test_write_var_string(self):
        for c in self.tests:
            writer = FixedBytesWriter(c["max"])
            try:
                write_var_string(writer, c['pver'], c["in"])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])


class TestVarStringOverflowErrors(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.tests = [
            {
                "buf": bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]),
                "pver": self.pver,
                "err": MessageLengthTooLongErr
            },
            {
                "buf": bytes([0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]),
                "pver": self.pver,
                "err": MessageLengthTooLongErr
            }
        ]

    def test_read_var_string(self):
        for c in self.tests:
            reader = io.BytesIO(c["buf"])
            try:
                read_var_string(reader, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), c['err'])


class TestVarBytesWire(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.bytes256 = bytes([0x01]) * 256
        self.tests = [
            {
                "in": bytes([]),
                "buf": bytes([0x00]),
                "pver": self.pver,
            },
            {
                "in": bytes([0x01]),
                "buf": bytes([0x01, 0x01]),
                "pver": self.pver,
            },
            {
                "in": self.bytes256,
                "buf": bytes([0xfd, 0x00, 0x01]) + self.bytes256,
                "pver": self.pver,
            },
        ]

    def test_read_var_bytes(self):
        for c in self.tests:
            reader = io.BytesIO(c['buf'])
            self.assertEqual(read_var_bytes(reader, c['pver'], MaxMessagePayload, "test payload"),
                             c['in'])

    def test_write_var_bytes(self):
        for c in self.tests:
            writer = io.BytesIO()
            write_var_bytes(writer, c['pver'], c['in'])
            writer.seek(0)
            self.assertEqual(writer.read(), c['buf'])


class TestVarBytesWireErrors(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.bytes256 = bytes([0x01]) * 256
        self.tests = [

            # Force errors on empty byte array.
            {
                "in": bytes([]),
                "buf": bytes([0x00]),
                "pver": self.pver,
                "max": 0,
                "read_err": FixedBytesUnexpectedEOFErr,
                "write_err": FixedBytesShortWriteErr,
            },

            # Force error on single byte varint + byte array.
            {
                "in": bytes([0x01, 0x02, 0x03]),
                "buf": bytes([0x04]),
                "pver": self.pver,
                "max": 2,
                "read_err": FixedBytesUnexpectedEOFErr,
                "write_err": FixedBytesShortWriteErr,
            },

            # Force errors on 2-byte varint + byte array.
            {
                "in": self.bytes256,
                "buf": bytes([0xfd]),
                "pver": self.pver,
                "max": 2,
                "read_err": FixedBytesUnexpectedEOFErr,
                "write_err": FixedBytesShortWriteErr,
            },
        ]

    def test_read_var_bytes(self):
        for c in self.tests:
            reader = FixedBytesReader(c['max'], c["buf"])
            try:
                read_var_bytes(reader, c['pver'], MaxMessagePayload, "test payload")
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

    def test_write_var_bytes(self):
        for c in self.tests:
            writer = FixedBytesWriter(c["max"])
            try:
                write_var_bytes(writer, c['pver'], c['in'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])


class TestVarBytesOverflowErrors(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.bytes256 = bytes([0x01]) * 256
        self.tests = [
            {
                "buf": bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]),
                "pver": self.pver,
                "err": BytesTooLargeErr,
            },

            {
                "buf": bytes([0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]),
                "pver": self.pver,
                "err": BytesTooLargeErr,
            },
        ]

    def test_read_var_bytes(self):
        for c in self.tests:
            reader = io.BytesIO(c["buf"])
            try:
                read_var_bytes(reader, c['pver'], MaxMessagePayload, "test payload")
            except Exception as e:
                self.assertEqual(type(e), c['err'])


class TestRandomUint64(unittest.TestCase):
    def setUp(self):
        self.tries = 1 << 8
        self.watermark = 1 << 56
        self.maxHits = 5
        self.badRNG = "The random number generator on this system is clearly " + \
                      "terrible since we got {} values less than %d in {} runs " + \
                      "when only {} was expected"

    def test_random_uint64(self):
        num_hits = 0
        for i in range(self.tries):
            nonce = random_uint64()
            if nonce < self.watermark:
                num_hits += 1
            if num_hits > self.maxHits:
                s = self.badRNG.format(num_hits, self.watermark, self.tries, self.maxHits)
                raise Exception('Random Uint64 iteration {} failed - {} {}'.format(i, s, num_hits))


if __name__ == '__main__':
    unittest.main()
