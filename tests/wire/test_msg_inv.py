import unittest
import io
from wire.msg_inv import *
from tests.utils import *


class TestInv(unittest.TestCase):
    def test_command(self):
        msg = MsgInv()
        self.assertEqual(str(msg.command()), "inv")

    def test_max_payload_length(self):
        msg = MsgInv()
        want_payload = 1800009
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_add_address(self):
        msg = MsgInv()
        hash = Hash()
        iv = InvVect(InvType.InvTypeBlock, hash)
        msg.add_inv_vect(iv)
        self.assertEqual(msg.inv_list[0], iv)

        try:
            for _ in range(MaxInvPerMsg):
                msg.add_inv_vect(iv)
        except Exception as e:
            self.assertEqual(type(e), MessageExceedMaxInvPerMsgErr)


class TestInvWire(unittest.TestCase):
    def setUp(self):
        # Block 203707 hash.
        hashStr = "3264bc2ac36a60840790ba1d475d01367e7c723da941069e9dc"
        blockHash = Hash(hashStr)

        # Transaction 1 of Block 203707 hash.
        hashStr = "d28a3dc7392bf00a9855ee93dd9a81eff82a2c4fe57fbd42cfe71b487accfaf0"
        txkHash = Hash(hashStr)

        iv = InvVect(InvType.InvTypeBlock, blockHash)
        iv2 = InvVect(InvType.InvTypeTx, txkHash)

        # Empty inv message.
        NoInv = MsgInv()
        NoInvEncoded = bytes([
            0x00,  # Varint for number of inventory vectors
        ])

        # Inv message with multiple inventory vectors.
        MultiInv = MsgInv()
        MultiInv.add_inv_vect(iv)
        MultiInv.add_inv_vect(iv2)
        MultiInvEncoded = bytes([
            0x02,  # Varint for number of inv vectors
            0x02, 0x00, 0x00, 0x00,  # InvTypeBlock
            0xdc, 0xe9, 0x69, 0x10, 0x94, 0xda, 0x23, 0xc7,
            0xe7, 0x67, 0x13, 0xd0, 0x75, 0xd4, 0xa1, 0x0b,
            0x79, 0x40, 0x08, 0xa6, 0x36, 0xac, 0xc2, 0x4b,
            0x26, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 203707 hash
            0x01, 0x00, 0x00, 0x00,  # InvTypeTx
            0xf0, 0xfa, 0xcc, 0x7a, 0x48, 0x1b, 0xe7, 0xcf,
            0x42, 0xbd, 0x7f, 0xe5, 0x4f, 0x2c, 0x2a, 0xf8,
            0xef, 0x81, 0x9a, 0xdd, 0x93, 0xee, 0x55, 0x98,
            0x0a, 0xf0, 0x2b, 0x39, 0xc7, 0x3d, 0x8a, 0xd2,  # Tx 1 of block 203707 hash
        ])

        self.tests = [
            # Latest protocol version with no inv vectors.
            {
                "in": NoInv,
                "out": NoInv,
                "buf": NoInvEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },

            # Latest protocol version with multiple inv vectors.
            {
                "in": MultiInv,
                "out": MultiInv,
                "buf": MultiInvEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },

            # Protocol version BIP0035Version with no inv vectors.
            {
                "in": NoInv,
                "out": NoInv,
                "buf": NoInvEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding,
            },

            #  Protocol version BIP0035Version with multiple inv vectors.
            {
                "in": MultiInv,
                "out": MultiInv,
                "buf": MultiInvEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding,
            },

            # Protocol version BIP0031Version with no inv vectors.
            {
                "in": NoInv,
                "out": NoInv,
                "buf": NoInvEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding,
            },

            #  Protocol version BIP0031Version with multiple inv vectors.
            {
                "in": MultiInv,
                "out": MultiInv,
                "buf": MultiInvEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding,
            },

            # Protocol version NetAddressTimeVersion with no inv vectors.
            {
                "in": NoInv,
                "out": NoInv,
                "buf": NoInvEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding,
            },

            #  Protocol version NetAddressTimeVersion with multiple inv vectors.
            {
                "in": MultiInv,
                "out": MultiInv,
                "buf": MultiInvEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding,
            },

            # Protocol version MultipleAddressVersion with no inv vectors.
            {
                "in": NoInv,
                "out": NoInv,
                "buf": NoInvEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding,
            },

            #  Protocol version MultipleAddressVersion with multiple inv vectors.
            {
                "in": MultiInv,
                "out": MultiInv,
                "buf": MultiInvEncoded,
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
            msg = MsgInv()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])


class TestInvWireErrors(unittest.TestCase):
    def setUp(self):
        pver = ProtocolVersion

        # Block 203707 hash.
        hashStr = "3264bc2ac36a60840790ba1d475d01367e7c723da941069e9dc"
        blockHash = Hash(hashStr)

        iv = InvVect(InvType.InvTypeBlock, blockHash)

        # Base inv message used to induce errors.
        baseInv = MsgInv()
        baseInv.add_inv_vect(iv)
        baseInvEncoded = bytes([
            0x02,  # Varint for number of inv vectors
            0x02, 0x00, 0x00, 0x00,  # InvTypeBlock
            0xdc, 0xe9, 0x69, 0x10, 0x94, 0xda, 0x23, 0xc7,
            0xe7, 0x67, 0x13, 0xd0, 0x75, 0xd4, 0xa1, 0x0b,
            0x79, 0x40, 0x08, 0xa6, 0x36, 0xac, 0xc2, 0x4b,
            0x26, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Block 203707 hash
        ])

        # Inv message that forces an error by having more than the max allowed
        # inv vectors.
        maxInv = MsgInv()
        for _ in range(MaxInvPerMsg):
            maxInv.add_inv_vect(iv)

        maxInv.inv_list.append(iv)
        maxInvEncoded = bytes([
            0xfd, 0x51, 0xc3,  # Varint for number of inv vectors (50001)
        ])

        self.tests = [
            # Latest protocol version with intentional read/write errors.
            # Force error in inventory vector count
            {
                "in": baseInv,
                "buf": baseInvEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in inventory list.
            {
                "in": baseInv,
                "buf": baseInvEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 1,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error with greater than max inventory vectors.
            {
                "in": maxInv,
                "buf": maxInvEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 3,
                "write_err": MessageExceedMaxInvPerMsgErr,
                "read_err": MessageExceedMaxInvPerMsgErr,
            },
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
                c['in'].btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
