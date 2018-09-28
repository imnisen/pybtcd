import unittest
from wire.msg_reject import *
from tests.utils import *

mainNetGenesisHash = Hash(bytes([
    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,
]))


class TestRejectCode(unittest.TestCase):
    def test_str(self):
        tests = [
            {"in": RejectCode.RejectMalformed, "want": "REJECT_MALFORMED"},
            {"in": RejectCode.RejectInvalid, "want": "REJECT_INVALID"},
            {"in": RejectCode.RejectObsolete, "want": "REJECT_OBSOLETE"},
            {"in": RejectCode.RejectDuplicate, "want": "REJECT_DUPLICATE"},
            {"in": RejectCode.RejectNonstandard, "want": "REJECT_NONSTANDARD"},
            {"in": RejectCode.RejectDust, "want": "REJECT_DUST"},
            {"in": RejectCode.RejectInsufficientFee, "want": "REJECT_INSUFFICIENTFEE"},
            {"in": RejectCode.RejectCheckpoint, "want": "REJECT_CHECKPOINT"},
        ]

        for c in tests:
            self.assertEqual(str(c['in']), c['want'])


class TestMsgReject(unittest.TestCase):
    def setUp(self):
        self.length_tests = [
            {"pver": ProtocolVersion, "want_payload": MaxMessagePayload},
            {"pver": RejectVersion - 1, "want_payload": 0},
        ]

        self.wire_tests = [
            # Latest protocol version rejected command version (no hash).
            {
                "in": MsgReject(cmd=Commands.CmdVersion,
                                code=RejectCode.RejectDuplicate,
                                reason="duplicate version"),
                "out": MsgReject(cmd=Commands.CmdVersion,
                                 code=RejectCode.RejectDuplicate,
                                 reason="duplicate version"),
                "buf": bytes([
                    0x07, 0x76, 0x65, 0x72, 0x73, 0x69, 0x6f, 0x6e,  # "version"
                    0x12,  # RejectDuplicate
                    0x11, 0x64, 0x75, 0x70, 0x6c, 0x69, 0x63, 0x61,
                    0x74, 0x65, 0x20, 0x76, 0x65, 0x72, 0x73, 0x69,
                    0x6f, 0x6e,  # "duplicate version"
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Latest protocol version rejected command block (has hash).
            {
                "in": MsgReject(cmd=Commands.CmdBlock,
                                code=RejectCode.RejectDuplicate,
                                reason="duplicate block",
                                hash=mainNetGenesisHash),
                "out": MsgReject(cmd=Commands.CmdBlock,
                                 code=RejectCode.RejectDuplicate,
                                 reason="duplicate block",
                                 hash=mainNetGenesisHash),
                "buf": bytes([
                    0x05, 0x62, 0x6c, 0x6f, 0x63, 0x6b,  # "block"
                    0x12,  # RejectDuplicate
                    0x0f, 0x64, 0x75, 0x70, 0x6c, 0x69, 0x63, 0x61,
                    0x74, 0x65, 0x20, 0x62, 0x6c, 0x6f, 0x63, 0x6b,  # "duplicate block"
                    0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
                    0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
                    0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
                    0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,  # mainNetGenesisHash
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },
        ]

        pver = ProtocolVersion
        pverNoReject = RejectVersion - 1
        baseReject = MsgReject(cmd=Commands.CmdBlock,
                               code=RejectCode.RejectDuplicate,
                               reason="duplicate block",
                               hash=mainNetGenesisHash)
        baseRejectEncoded = bytes([
            0x05, 0x62, 0x6c, 0x6f, 0x63, 0x6b,  # "block"
            0x12,  # RejectDuplicate
            0x0f, 0x64, 0x75, 0x70, 0x6c, 0x69, 0x63, 0x61,
            0x74, 0x65, 0x20, 0x62, 0x6c, 0x6f, 0x63, 0x6b,  # "duplicate block"
            0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
            0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
            0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
            0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00,  # mainNetGenesisHash
        ])

        self.wire_err_tests = [
            # Force error in reject command.
            {
                "in": baseReject,
                "buf": baseRejectEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in reject code.
            {
                "in": baseReject,
                "buf": baseRejectEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 6,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in reject reason.
            {
                "in": baseReject,
                "buf": baseRejectEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 7,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in reject hash.
            {
                "in": baseReject,
                "buf": baseRejectEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 23,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error due to unsupported protocol version.
            {
                "in": baseReject,
                "buf": baseRejectEncoded,
                "pver": pverNoReject,
                "enc": BaseEncoding,
                "max": 6,
                "write_err": NotSupportBelowRejectVersionMsgErr,
                "read_err": NotSupportBelowRejectVersionMsgErr,
            },
        ]

    def test_command(self):
        msg = MsgReject()
        self.assertEqual(str(msg.command()), "reject")

    def test_max_payload_length(self):
        for c in self.length_tests:
            msg = MsgReject()
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
            msg = MsgReject()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgReject()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
