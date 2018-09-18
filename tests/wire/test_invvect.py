import unittest
import io
from wire.invvect import *


class TestInvTypeStringer(unittest.TestCase):
    def test_string(self):
        tests = [
            {"in": InvType.InvTypeError, "want": "ERROR"},
            {"in": InvType.InvTypeTx, "want": "MSG_TX"},
            {"in": InvType.InvTypeBlock, "want": "MSG_BLOCK"},
        ]
        for c in tests:
            self.assertEqual(str(c['in']), c['want'])


class TestInvVect(unittest.TestCase):
    def test_init(self):
        inv_type = InvType.InvTypeBlock
        hash = Hash()
        iv = InvVect(inv_type=inv_type, hash=hash)
        self.assertEqual(iv.inv_type, inv_type)
        self.assertEqual(iv.hash, hash)


class TestInvVectWire(unittest.TestCase):
    def setUp(self):
        # Block 203707 hash.
        hashStr = "3264bc2ac36a60840790ba1d475d01367e7c723da941069e9dc"
        baseHash = Hash(hashStr)

        # errInvVect is an inventory vector with an error.
        errInvVect = InvVect(inv_type=InvType.InvTypeError, hash=Hash())
        errInvVectEncoded = bytes([
            0x00, 0x00, 0x00, 0x00,  # InvTypeError
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # No hash
        ])

        # txInvVect is an inventory vector representing a transaction.
        txInvVect = InvVect(inv_type=InvType.InvTypeTx, hash=baseHash)
        txInvVectEncoded = bytes([
            0x01, 0x00, 0x00, 0x00,  # InvTypeTx
            0xdc, 0xe9, 0x69, 0x10, 0x94, 0xda, 0x23, 0xc7,
            0xe7, 0x67, 0x13, 0xd0, 0x75, 0xd4, 0xa1, 0x0b,
            0x79, 0x40, 0x08, 0xa6, 0x36, 0xac, 0xc2, 0x4b,
            0x26, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 203707 hash
        ])

        # blockInvVect is an inventory vector representing a block.
        blockInvVect = InvVect(inv_type=InvType.InvTypeBlock, hash=baseHash)
        blockInvVectEncoded = bytes([
            0x02, 0x00, 0x00, 0x00,  # InvTypeBlock
            0xdc, 0xe9, 0x69, 0x10, 0x94, 0xda, 0x23, 0xc7,
            0xe7, 0x67, 0x13, 0xd0, 0x75, 0xd4, 0xa1, 0x0b,
            0x79, 0x40, 0x08, 0xa6, 0x36, 0xac, 0xc2, 0x4b,
            0x26, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 203707 hash
        ])

        self.tests = [
            # Latest protocol version error inventory vector.
            {
                "in": errInvVect,
                "out": errInvVect,
                "buf": errInvVectEncoded,
                "pver": ProtocolVersion
            },

            # Latest protocol version tx inventory vector.
            {
                "in": txInvVect,
                "out": txInvVect,
                "buf": txInvVectEncoded,
                "pver": ProtocolVersion
            },

            # Latest protocol version block inventory vector.
            {
                "in": blockInvVect,
                "out": blockInvVect,
                "buf": blockInvVectEncoded,
                "pver": ProtocolVersion
            },

            # Protocol version BIP0035Version error inventory vector.
            {
                "in": errInvVect,
                "out": errInvVect,
                "buf": errInvVectEncoded,
                "pver": BIP0035Version
            },

            # Protocol version BIP0035Version tx inventory vector.
            {
                "in": txInvVect,
                "out": txInvVect,
                "buf": txInvVectEncoded,
                "pver": BIP0035Version
            },

            # Protocol version BIP0035Version block inventory vector.
            {
                "in": blockInvVect,
                "out": blockInvVect,
                "buf": blockInvVectEncoded,
                "pver": BIP0035Version
            },

            # Protocol version BIP0031Version error inventory vector.
            {
                "in": errInvVect,
                "out": errInvVect,
                "buf": errInvVectEncoded,
                "pver": BIP0031Version
            },

            # Protocol version BIP0031Version tx inventory vector.
            {
                "in": txInvVect,
                "out": txInvVect,
                "buf": txInvVectEncoded,
                "pver": BIP0031Version
            },

            # Protocol version BIP0031Version block inventory vector.
            {
                "in": blockInvVect,
                "out": blockInvVect,
                "buf": blockInvVectEncoded,
                "pver": BIP0031Version
            },

            # Protocol version NetAddressTimeVersion error inventory vector.
            {
                "in": errInvVect,
                "out": errInvVect,
                "buf": errInvVectEncoded,
                "pver": NetAddressTimeVersion
            },

            # Protocol version NetAddressTimeVersion tx inventory vector.
            {
                "in": txInvVect,
                "out": txInvVect,
                "buf": txInvVectEncoded,
                "pver": NetAddressTimeVersion
            },

            # Protocol version NetAddressTimeVersion block inventory vector.
            {
                "in": blockInvVect,
                "out": blockInvVect,
                "buf": blockInvVectEncoded,
                "pver": NetAddressTimeVersion
            },

            # Protocol version NetAddressTimeVersion error inventory vector.
            {
                "in": errInvVect,
                "out": errInvVect,
                "buf": errInvVectEncoded,
                "pver": NetAddressTimeVersion
            },

            # Protocol version MultipleAddressVersion tx inventory vector.
            {
                "in": txInvVect,
                "out": txInvVect,
                "buf": txInvVectEncoded,
                "pver": MultipleAddressVersion
            },

            # Protocol version MultipleAddressVersion block inventory vector.
            {
                "in": blockInvVect,
                "out": blockInvVect,
                "buf": blockInvVectEncoded,
                "pver": MultipleAddressVersion
            },
        ]

    def test_read_inv_vect(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            self.assertEqual(read_inv_vect(s, c['pver']), c['out'])

    def test_write_inv_vect(self):
        for c in self.tests:
            s = io.BytesIO()
            write_inv_vect(s, c['pver'], c['in'])
            self.assertEqual(s.getvalue(), c['buf'])
