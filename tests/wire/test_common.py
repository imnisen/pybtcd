import unittest
from wire.common import *
from chainhash import *
from wire.protocol import *


class TestElementWire(unittest.TestCase):
    def setUp(self):
        self.tests = [
            {
                "in": 1,
                "buf": bytes([0x01, 0x00, 0x00, 0x00])
            },
            {
                "in": 256,
                "buf": bytes([0x00, 0x01, 0x00, 0x00])
            },
            {
                "in": 65536,
                "buf": bytes([0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
            },
            {
                "in": 4294967296,
                "buf": bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00])
            },
            {
                "in": True,
                "buf": bytes([0x01])
            },
            {
                "in": False,
                "buf": bytes([0x00])
            },
            {
                "in": bytes([0x01, 0x02, 0x03, 0x04]),
                "buf": bytes([0x01, 0x02, 0x03, 0x04])
            },
            {
                "in": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, ]),
                "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, ])
            },
            {
                "in": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                             0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, ]),
                "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                              0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, ])
            },
            {
                "in": Hash(bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                                  0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
                                  0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                                  0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, ])),
                "buf": bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                              0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
                              0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                              0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, ])
            },
            {
                "in": ServiceFlag.SFNodeNetwork,
                "buf": bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            },
            # TOADD about InvType test
            # {
            #     InvType(InvTypeTx),
            #     []byte{0x01, 0x00, 0x00, 0x00},
            # },
            {
                "in": BitcoinNet.MainNet,
                "buf": bytes([0xf9, 0xbe, 0xb4, 0xd9]),
            },
            #  TOADD Type not supported by the "fast" path and requires reflection.
            # {
            #     writeElementReflect(1),
            #     []byte{0x01, 0x00, 0x00, 0x00},
            # },

        ]

    def test_write_element(self):
        for c in self.tests:
            pass
            # write_element(c['in'])
            # self.assertEqual()


class TestElementWireErrors(unittest.TestCase):
    pass


class TestVarIntWire(unittest.TestCase):
    pass


class TestVarIntWireErrors(unittest.TestCase):
    pass


class TestVarIntNonCanonicat(unittest.TestCase):
    pass


class TestVarIntSerializeSize(unittest.TestCase):
    pass


class TestVarStringWire(unittest.TestCase):
    pass


class TestVarStringWireErrors(unittest.TestCase):
    pass


class TestVarStringOverflowErrors(unittest.TestCase):
    pass


class TestVarBytesWire(unittest.TestCase):
    pass


class TestVarBytesWireErrors(unittest.TestCase):
    pass


class TestVarBytesOverflowErrors(unittest.TestCase):
    pass


class TestRandomUint64(unittest.TestCase):
    pass


class TestRandomUint64Errors(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
