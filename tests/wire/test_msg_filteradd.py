import unittest
from wire.msg_filteradd import *
from tests.utils import *


class TestMsgFilterAdd(unittest.TestCase):
    def setUp(self):
        self.wire_tests = [
            {
                "in": MsgFilterAdd(data=bytes([0x01, 0x02])),
                "out": MsgFilterAdd(data=bytes([0x01, 0x02])),
                "buf": bytes([
                    0x02,
                    0x01, 0x02
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },
        ]

        self.wire_err_tests = [
            # Protocol version below BIP0037
            {
                "in": MsgFilterAdd(data=bytes([0x01, 0x02])),
                "buf": bytes([
                    0x02,
                    0x01, 0x02
                ]),
                "pver": BIP0031Version,
                "enc": BaseEncoding,
                "max": 3,
                "write_err": NotSupportBelowBIP37MsgErr,
                "read_err": NotSupportBelowBIP37MsgErr,
            },

            # Beyond MaxFilterAddDataSize
            {
                "in": MsgFilterAdd(data=bytes([0xff]) * 521),
                "buf": bytes([0xff]) * 521,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 521,
                "write_err": MaxFilterAddDataSizeMsgErr,
                "read_err": BytesTooLargeErr,
            }

        ]

        baseData = bytes([0x01, 0x02, 0x03, 0x04])
        baseFilterAdd = MsgFilterAdd(data=baseData)
        baseFilterAddEncoded = bytes([
            0x04,
            0x01, 0x02, 0x03, 0x04
        ])
        self.wire_err_tests.extend([

            # Force error in data size.
            {
                "in": baseFilterAdd,
                "buf": baseFilterAddEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in data .
            {
                "in": baseFilterAdd,
                "buf": baseFilterAddEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 1,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error due to unsupported protocol version
            {
                "in": baseFilterAdd,
                "buf": baseFilterAddEncoded,
                "pver": BIP0037Version - 1,
                "enc": BaseEncoding,
                "max": 5,
                "write_err": NotSupportBelowBIP37MsgErr,
                "read_err": NotSupportBelowBIP37MsgErr,
            },
        ])

    def test_command(self):
        msg = MsgFilterAdd()
        self.assertEqual(str(msg.command()), "filteradd")

    def test_max_payload_length(self):
        msg = MsgFilterAdd()
        want_payload = 523
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
            msg = MsgFilterAdd()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgFilterAdd()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
