import unittest
from wire.msg_filterload import *
from tests.utils import *


class TestMsgFilterLoad(unittest.TestCase):
    def setUp(self):
        self.wire_tests = [
            {
                "in": MsgFilterLoad(filter=bytes([0xff]) * 10,
                                    hash_funcs=50,
                                    tweak=0,
                                    flags=BloomUpdateType(0)),
                "out": MsgFilterLoad(filter=bytes([0xff]) * 10,
                                     hash_funcs=50,
                                     tweak=0,
                                     flags=BloomUpdateType(0)),
                "buf": bytes([
                    0x0a,  # filter size
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  # filter
                    0x32, 0x00, 0x00, 0x00,  # hash funcs
                    0x00, 0x00, 0x00, 0x00,  # tweak
                    0x00,  # update Type
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },

            {
                "in": MsgFilterLoad(filter=bytes([0x01, 0x02, 0x03, 0x04]),
                                    hash_funcs=10,
                                    tweak=0,
                                    flags=BloomUpdateType.BloomUpdateNone),
                "out": MsgFilterLoad(filter=bytes([0x01, 0x02, 0x03, 0x04]),
                                     hash_funcs=10,
                                     tweak=0,
                                     flags=BloomUpdateType.BloomUpdateNone),
                "buf": bytes([
                    0x04,  # count of filter bytes
                    0x01, 0x02, 0x03, 0x04,  # filter
                    0x0a, 0x00, 0x00, 0x00,  # hashfuns
                    0x00, 0x00, 0x00, 0x00,  # tweak
                    0x00  # flags
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
            },
        ]

        baseFilterLoad = bytes([0x01, 0x02, 0x03, 0x04])
        baseFilterLoad = MsgFilterLoad(filter=baseFilterLoad,
                                       hash_funcs=10,
                                       tweak=0,
                                       flags=BloomUpdateType.BloomUpdateNone)
        baseFilterLoadEncoded = bytes([
            0x04,  # count of filter bytes
            0x01, 0x02, 0x03, 0x04,  # filter
            0x00, 0x00, 0x00, 0x0a,  # hashfuns
            0x00, 0x00, 0x00, 0x00,  # tweak
            0x00  # flags
        ])

        self.wire_err_tests = [

            # MaxFilterSize
            {
                "in": MsgFilterLoad(filter=bytes([0xff]) * 36001,
                                    hash_funcs=10,
                                    tweak=0,
                                    flags=BloomUpdateType(0)),
                "buf": bytes([0xff]) * 36001,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 36001,
                "write_err": MaxFilterLoadFilterSizeMsgErr,
                "read_err": BytesTooLargeErr,
            },

            # MaxHashFuncsSize
            {
                "in": MsgFilterLoad(filter=bytes([0xff]) * 10,
                                    hash_funcs=61,
                                    tweak=0,
                                    flags=BloomUpdateType(0)),
                "buf": bytes([
                    0x0a,  # filter size
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  # filter
                    0x3d, 0x00, 0x00, 0x00,  # max hash funcs
                    0x00, 0x00, 0x00, 0x00,  # tweak
                    0x00,  # update Type
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": len([
                    0x0a,  # filter size
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  # filter
                    0x3d, 0x00, 0x00, 0x00,  # max hash funcs
                    0x00, 0x00, 0x00, 0x00,  # tweak
                    0x00,  # update Type
                ]),
                "write_err": MaxFilterLoadHashFuncsMsgErr,
                "read_err": MaxFilterLoadHashFuncsMsgErr,
            },

            # Force error in filter size.
            {
                "in": baseFilterLoad,
                "buf": baseFilterLoadEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in filter.
            {
                "in": baseFilterLoad,
                "buf": baseFilterLoadEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 1,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in hash funcs.
            {
                "in": baseFilterLoad,
                "buf": baseFilterLoadEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 5,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in tweak.
            {
                "in": baseFilterLoad,
                "buf": baseFilterLoadEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 9,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in flags.
            {
                "in": baseFilterLoad,
                "buf": baseFilterLoadEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "max": 13,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error due to unsupported protocol version.
            {
                "in": baseFilterLoad,
                "buf": baseFilterLoadEncoded,
                "pver": BIP0037Version - 1,
                "enc": BaseEncoding,
                "max": 10,
                "write_err": NotSupportBelowBIP37MsgErr,
                "read_err": NotSupportBelowBIP37MsgErr,
            },

        ]

    def test_command(self):
        msg = MsgFilterLoad()
        self.assertEqual(str(msg.command()), "filterload")

    def test_max_payload_length(self):
        msg = MsgFilterLoad()
        want_payload = 36012
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
            msg = MsgFilterLoad()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Error conditions
        for c in self.wire_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgFilterLoad()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
