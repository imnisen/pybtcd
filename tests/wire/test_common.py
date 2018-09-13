import unittest
from wire.common import *
from chainhash import *
from wire.protocol import *
import io


# class TestElementWire(unittest.TestCase):
#     def setUp(self):
#         self.tests = [
#             {
#                 "in": 1,
#                 "buf": bytes([0x01, 0x00, 0x00, 0x00])
#             },
#             {
#                 "in": 256,
#                 "buf": bytes([0x00, 0x01, 0x00, 0x00])
#             },
#             {
#                 "in": 65536,
#                 "buf": bytes([0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
#             },
#             {
#                 "in": 4294967296,
#                 "buf": bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00])
#             },
#             {
#                 "in": True,
#                 "buf": bytes([0x01])
#             },
#             {
#                 "in": False,
#                 "buf": bytes([0x00])
#             },
#             {
#                 "in": bytes([0x01, 0x02, 0x03, 0x04]),
#                 "buf": bytes([0x01, 0x02, 0x03, 0x04])
#             },
#             {
#                 "in": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, ]),
#                 "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, ])
#             },
#             {
#                 "in": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
#                              0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, ]),
#                 "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
#                               0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, ])
#             },
#             {
#                 "in": Hash(bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
#                                   0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
#                                   0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
#                                   0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, ])),
#                 "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
#                               0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
#                               0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
#                               0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, ])
#             },
#             {
#                 "in": ServiceFlag.SFNodeNetwork,
#                 "buf": bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
#             },
#             # TOADD about InvType test
#             # {
#             #     InvType(InvTypeTx),
#             #     []byte{0x01, 0x00, 0x00, 0x00},
#             # },
#             {
#                 "in": BitcoinNet.MainNet,
#                 "buf": bytes([0xf9, 0xbe, 0xb4, 0xd9]),
#             },
#             #  TOADD Type not supported by the "fast" path and requires reflection.
#             # {
#             #     writeElementReflect(1),
#             #     []byte{0x01, 0x00, 0x00, 0x00},
#             # },
#
#         ]
#
#     def test_write_element(self):
#         for c in self.tests:
#             pass
#             # write_element(c['in'])
#             # self.assertEqual()
#
#
# class TestElementWireErrors(unittest.TestCase):
#     pass
#

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


# For TestVarIntWireErrors test, same as golang newFixedWriter, newFixedReader
class FixedBytesErr(Exception):
    pass


class FixedBytesInitErr(FixedBytesErr):
    pass


class FixedBytesUnexpectedEOFErr(FixedBytesErr):
    pass


class FixedBytesShortWriteErr(FixedBytesErr):
    pass


class FixedBytesReader():
    def __init__(self, max, buf):
        if max < 0:
            raise FixedBytesInitErr

        self.max = max
        self._data = io.BytesIO(buf)

    def read(self, size: int) -> bytes:
        # Limit the case, maybe we can let size<=0, and decide what to do
        if size <= 0:
            raise FixedBytesErr('size must greater than 0')

        result = bytearray()
        while True:
            if size == 0:
                break

            if self.max == 0:
                raise FixedBytesUnexpectedEOFErr

            result += self._data.read(1)
            self.max -= 1
            size -= 1

        return bytes(result)


class FixedBytesWriter():
    def __init__(self, max):
        if max < 0:
            raise FixedBytesInitErr
        self.max = max
        self._data = io.BytesIO()

    def write(self, val: bytes):

        val_len = len(val)
        i = 0
        while True:
            if i > val_len - 1:
                break
            if self.max == 0:
                raise FixedBytesShortWriteErr

            self._data.write(val[i].to_bytes(1, byteorder="little"))
            i += 1
            self.max -= 1
        return


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
