import unittest
from wire.msg_alert import *
from tests.utils import *


class TestAlert(unittest.TestCase):
    def setUp(self):
        # For wire test
        baseAlert = Alert(version=1, relay_until=1337093712, expiration=1368628812,
                          id=1015, cancel=1013, set_cancel=[1014], min_ver=0, max_ver=40599,
                          set_sub_ver=["/Satoshi:0.7.2/"], priority=5000, comment="",
                          status_bar="URGENT: upgrade required, see http://bitcoin.org/dos for details")

        baseAlertEncoded = bytes([

            0x01, 0x00, 0x00, 0x00, 0x50,
            0x6e, 0xb2, 0x4f, 0x00, 0x00,
            0x00, 0x00, 0x4c, 0x9e, 0x93,
            0x51, 0x00, 0x00, 0x00, 0x00,
            0xf7, 0x03, 0x00, 0x00, 0xf5,
            0x03, 0x00, 0x00, 0x01, 0xf6,
            0x03, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x97, 0x9e, 0x00,
            0x00, 0x01, 0x0f, 0x2f, 0x53,
            0x61, 0x74, 0x6f, 0x73, 0x68,
            0x69, 0x3a, 0x30, 0x2e, 0x37,
            0x2e, 0x32, 0x2f, 0x88, 0x13,
            0x00, 0x00, 0x00, 0x40, 0x55,
            0x52, 0x47, 0x45, 0x4e, 0x54,
            0x3a, 0x20, 0x75, 0x70, 0x67,
            0x72, 0x61, 0x64, 0x65, 0x20,
            0x72, 0x65, 0x71, 0x75, 0x69,
            0x72, 0x65, 0x64, 0x2c, 0x20,
            0x73, 0x65, 0x65, 0x20, 0x68,
            0x74, 0x74, 0x70, 0x3a, 0x2f,
            0x2f, 0x62, 0x69, 0x74, 0x63,
            0x6f, 0x69, 0x6e, 0x2e, 0x6f,
            0x72, 0x67, 0x2f, 0x64, 0x6f,
            0x73, 0x20, 0x66, 0x6f, 0x72,
            0x20, 0x64, 0x65, 0x74, 0x61,
            0x69, 0x6c, 0x73, 0x00
        ])
        self.serialize_tests = [

            {
                "in": baseAlert,
                "out": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

        ]

        # For wire error test
        baseAlert = Alert(version=1, relay_until=1337093712, expiration=1368628812,
                          id=1015, cancel=1013, set_cancel=[1014], min_ver=0, max_ver=40599,
                          set_sub_ver=["/Satoshi:0.7.2/"], priority=5000, comment="",
                          status_bar="URGENT")
        baseAlertEncoded = bytes([
            # |....Pn.O....L..Q|
            0x01, 0x00, 0x00, 0x00, 0x50, 0x6e, 0xb2, 0x4f, 0x00, 0x00, 0x00, 0x00, 0x4c, 0x9e, 0x93, 0x51,
            # |................|
            0x00, 0x00, 0x00, 0x00, 0xf7, 0x03, 0x00, 0x00, 0xf5, 0x03, 0x00, 0x00, 0x01, 0xf6, 0x03, 0x00,
            # |.........../Sato|
            0x00, 0x00, 0x00, 0x00, 0x00, 0x97, 0x9e, 0x00, 0x00, 0x01, 0x0f, 0x2f, 0x53, 0x61, 0x74, 0x6f,
            # |shi:0.7.2/......|
            0x73, 0x68, 0x69, 0x3a, 0x30, 0x2e, 0x37, 0x2e, 0x32, 0x2f, 0x88, 0x13, 0x00, 0x00, 0x00, 0x06,
            # |URGENT.|
            0x55, 0x52, 0x47, 0x45, 0x4e, 0x54, 0x00,
        ])
        self.serialize_err_tests = [

            # Force error in version.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in SetCancel VarInt.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 28,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in SetCancel ints.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 29,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in MinVer
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 40,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in SetSubVer string VarInt.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 41,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in SetSubVer strings.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 48,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in Priority
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 60,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in Comment string.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 62,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in StatusBar string.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 64,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in Reserved string.
            {
                "in": baseAlert,
                "buf": baseAlertEncoded,
                "pver": ProtocolVersion,
                "max": 70,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

        ]


        self.overflow_tests = [
            # overflow the max number of elements in SetCancel
            # maxCountSetCancel + 1 == 8388575 == \xdf\xff\x7f\x00
            {
                "buf": bytes([
                    0x01, 0x00, 0x00, 0x00, 0x50, 0x6e, 0xb2, 0x4f, 0x00, 0x00, 0x00, 0x00, 0x4c, 0x9e, 0x93, 0x51, #|....Pn.O....L..Q|
		            0x00, 0x00, 0x00, 0x00, 0xf7, 0x03, 0x00, 0x00, 0xf5, 0x03, 0x00, 0x00, 0xfe, 0xdf, 0xff, 0x7f, #|................|
		            0x00, 0x00, 0x00, 0x00, 0x00, 0x97, 0x9e, 0x00, 0x00, 0x01, 0x0f, 0x2f, 0x53, 0x61, 0x74, 0x6f, #|.........../Sato|
		            0x73, 0x68, 0x69, 0x3a, 0x30, 0x2e, 0x37, 0x2e, 0x32, 0x2f, 0x88, 0x13, 0x00, 0x00, 0x00, 0x06, #|shi:0.7.2/......|
		            0x55, 0x52, 0x47, 0x45, 0x4e, 0x54, 0x00, #|URGENT.|
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "err": MaxCountSetCancelMsgErr
            },

            # overflow the max number of elements in SetSubVer
            # maxCountSetSubVer + 1 == 131071 + 1 == \x00\x00\x02\x00
            {
                "buf": bytes([
                    0x01, 0x00, 0x00, 0x00, 0x50, 0x6e, 0xb2, 0x4f, 0x00, 0x00, 0x00, 0x00, 0x4c, 0x9e, 0x93, 0x51, #|....Pn.O....L..Q|
		            0x00, 0x00, 0x00, 0x00, 0xf7, 0x03, 0x00, 0x00, 0xf5, 0x03, 0x00, 0x00, 0x01, 0xf6, 0x03, 0x00, #|................|
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x97, 0x9e, 0x00, 0x00, 0xfe, 0x00, 0x00, 0x02, 0x00, 0x74, 0x6f, #|.........../Sato|
                    0x73, 0x68, 0x69, 0x3a, 0x30, 0x2e, 0x37, 0x2e, 0x32, 0x2f, 0x88, 0x13, 0x00, 0x00, 0x00, 0x06, #|shi:0.7.2/......|
                    0x55, 0x52, 0x47, 0x45, 0x4e, 0x54, 0x00, #|URGENT.|
                ]),
                "pver": ProtocolVersion,
                "enc": BaseEncoding,
                "err": MaxCountSetSubVerlMsgErr
            },


        ]

    def test_serialize(self):
        # Right conditions
        for c in self.serialize_tests:
            s = io.BytesIO()
            c['in'].serialize(s, c['pver'])
            self.assertEqual(s.getvalue(), c['buf'])

        # Error conditions
        for c in self.serialize_err_tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].serialize(s, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_deserialize(self):
        # Right conditions
        for c in self.serialize_tests:
            alert = Alert()
            s = io.BytesIO(c['buf'])
            alert.deserialize(s, c['pver'])
            self.assertEqual(alert, c['out'])

        # Error conditions
        for c in self.serialize_err_tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                alert = Alert()
                alert.deserialize(s, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

        # Overflow conditons
        for c in self.overflow_tests:
            s = io.BytesIO(c['buf'])
            try:
                alert = Alert()
                alert.deserialize(s, c['pver'])
            except Exception as e:
                self.assertEqual(type(e), c['err'])
