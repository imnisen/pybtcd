import unittest
import io
from wire.msg_getaddr import *


class TestMsgGetAddr(unittest.TestCase):
    def setUp(self):
        msgGetAddr = MsgGetAddr()
        msgGetAddrEncoded = bytes([])

        self.tests = [
            # Latest protocol version.
            {
                "in": msgGetAddr,
                "out": msgGetAddr,
                "buf": msgGetAddrEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0035Version.
            {
                "in": msgGetAddr,
                "out": msgGetAddr,
                "buf": msgGetAddrEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version.
            {
                "in": msgGetAddr,
                "out": msgGetAddr,
                "buf": msgGetAddrEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding
            },

            # Protocol version NetAddressTimeVersion.
            {
                "in": msgGetAddr,
                "out": msgGetAddr,
                "buf": msgGetAddrEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding
            },

            # Protocol version MultipleAddressVersion.
            {
                "in": msgGetAddr,
                "out": msgGetAddr,
                "buf": msgGetAddrEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding
            },

        ]

    def test_command(self):
        msg = MsgGetAddr()
        self.assertEqual(str(msg.command()), "getaddr")

    def test_max_payload_length(self):
        msg = MsgGetAddr()
        want_payload = 0
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgGetAddr()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])
