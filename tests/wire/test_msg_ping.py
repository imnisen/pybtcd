import unittest
from wire.msg_ping import *
from tests.utils import *


class TestMsgPing(unittest.TestCase):
    def setUp(self):
        self.length_tests = [
            {"pver": ProtocolVersion, "want_payload": 8},
            {"pver": BIP0031Version, "want_payload": 0},
        ]

        self.wire_tests = [
            # Latest protocol version.
            {
                "in": MsgPing(123123),
                "out": MsgPing(123123),
                "buf": bytes([0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version+1
            {
                "in": MsgPing(456456),
                "out": MsgPing(456456),
                "buf": bytes([0x08, 0xf7, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": BIP0031Version + 1,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version
            {
                "in": MsgPing(789789),
                "out": MsgPing(0),
                "buf": bytes([]),
                "pver": BIP0031Version,
                "enc": BaseEncoding
            },
        ]

        self.wire_err_tests = [
            {
                "in": MsgPing(123123),
                "buf": bytes([0xf3, 0xe0, 0x01, 0x00]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 2,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            }
        ]

    def test_command(self):
        msg = MsgPing()
        self.assertEqual(str(msg.command()), "ping")

    def test_max_payload_length(self):
        for c in self.length_tests:
            msg = MsgPing()
            want_payload = c['want_payload']
            self.assertEqual(msg.max_payload_length(c['pver']), want_payload)

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
            s = io.BytesIO(c['buf'])
            msg = MsgPing()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgPing()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
