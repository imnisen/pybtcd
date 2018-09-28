import unittest
from wire.msg_filterclear import *
from tests.utils import *


class TestMsgFilterClear(unittest.TestCase):
    def setUp(self):
        msgFilterClear = MsgFilterClear()
        msgFilterClearEncoded = bytes([])
        self.wire_tests = [
            {
                "in": msgFilterClear,
                "out": msgFilterClear,
                "buf": msgFilterClearEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },

            {
                "in": msgFilterClear,
                "out": msgFilterClear,
                "buf": msgFilterClearEncoded,
                "pver": BIP0037Version + 1,
                "enc": BaseEncoding,
            },

            {
                "in": msgFilterClear,
                "out": msgFilterClear,
                "buf": msgFilterClearEncoded,
                "pver": BIP0037Version,
                "enc": BaseEncoding,
            },
        ]

        self.wire_err_tests = [
            # Force error due to unsupported protocol version.
            {
                "in": msgFilterClear,
                "buf": msgFilterClearEncoded,
                "pver": BIP0037Version - 1,
                "enc": BaseEncoding,
                "max": 4,
                "write_err": NotSupportBelowBIP37MsgErr,
                "read_err": NotSupportBelowBIP37MsgErr,
            },
        ]

    def test_command(self):
        msg = MsgFilterClear()
        self.assertEqual(str(msg.command()), "filterclear")

    def test_max_payload_length(self):
        msg = MsgFilterClear()
        want_payload = 0
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

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
            msg = MsgFilterClear()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgFilterClear()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
