import unittest
from tests.utils import *
from wire.msg_verack import *

class TestVerAck(unittest.TestCase):
    def test_command(self):
        msg = MsgVerAck()
        self.assertEqual(str(msg.command()), "verack")

    def test_max_payload_length(self):
        msg = MsgVerAck()
        self.assertEqual(msg.max_payload_length(ProtocolVersion), 0)


class TestVerAckWire(unittest.TestCase):
    def setUp(self):
        msgVerAck = MsgVerAck()
        msgVerAckEncoded = bytes()
        self.tests = [

            # Latest protocol version.
            {
                "in": msgVerAck,
                "out": msgVerAck,
                "buf": msgVerAckEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0035Version.
            {
                "in": msgVerAck,
                "out": msgVerAck,
                "buf": msgVerAckEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version.
            {
                "in": msgVerAck,
                "out": msgVerAck,
                "buf": msgVerAckEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding
            },

            # Protocol version NetAddressTimeVersion.
            {
                "in": msgVerAck,
                "out": msgVerAck,
                "buf": msgVerAckEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding
            },

            # Protocol version MultipleAddressVersion.
            {
                "in": msgVerAck,
                "out": msgVerAck,
                "buf": msgVerAckEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding
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
            msg = MsgVerAck()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])
