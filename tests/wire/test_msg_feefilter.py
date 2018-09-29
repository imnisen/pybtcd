import unittest
from wire.msg_feefilter import *
from tests.utils import *


class TestMsgGetAddr(unittest.TestCase):
    def setUp(self):
        self.wire_tests = [
            # Latest protocol version.
            {
                "in": MsgFeeFilter(123123),
                "out": MsgFeeFilter(123123),
                "buf": bytes([0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version FeeFilterVersion
            {
                "in": MsgFeeFilter(456456),
                "out": MsgFeeFilter(456456),
                "buf": bytes([0x08, 0xf7, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": FeeFilterVersion,
                "enc": BaseEncoding
            },

        ]

        self.wire_err_tests = [
            # Force error in minfee.
            {
                "in": MsgFeeFilter(123123),
                "buf": bytes([0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": ProtocolVersion,
                "max": 0,
                "enc": BaseEncoding,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in minfee.
            {
                "in": MsgFeeFilter(123123),
                "buf": bytes([0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]),
                "pver": FeeFilterVersion - 1,
                "max": 4,
                "enc": BaseEncoding,
                "read_err": BelowSendHeadersVersionMsgErr,
                "write_err": BelowSendHeadersVersionMsgErr
            },

        ]

    def test_command(self):
        msg = MsgFeeFilter()
        self.assertEqual(str(msg.command()), "feefilter")

    def test_max_payload_length(self):
        msg = MsgFeeFilter()
        want_payload = 8
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_btc_encode(self):
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
        for c in self.wire_tests:
            s = io.BytesIO(c['buf'])
            msg = MsgFeeFilter()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgFeeFilter()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
