import unittest
import io
from wire.msg_sendheaders import *


class TestMsgGetAddr(unittest.TestCase):
    def setUp(self):
        msgSendHeaders = MsgSendHeaders()
        msgSendHeadersEncoded = bytes([])

        self.tests = [
            # Latest protocol version.
            {
                "in": msgSendHeaders,
                "out": msgSendHeaders,
                "buf": msgSendHeadersEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version SendHeadersVersion + 1
            {
                "in": msgSendHeaders,
                "out": msgSendHeaders,
                "buf": msgSendHeadersEncoded,
                "pver": SendHeadersVersion + 1,
                "enc": BaseEncoding
            },

            # Protocol version SendHeadersVersion
            {
                "in": msgSendHeaders,
                "out": msgSendHeaders,
                "buf": msgSendHeadersEncoded,
                "pver": SendHeadersVersion + 1,
                "enc": BaseEncoding
            },
        ]

        self.err_tests = [
            # Protocol version SendHeadersVersion - 1
            {
                "in": msgSendHeaders,
                "out": msgSendHeaders,
                "buf": msgSendHeadersEncoded,
                "pver": SendHeadersVersion - 1,
                "enc": BaseEncoding,
                "read_err": BelowSendHeadersVersionMsgErr,
                "write_err": BelowSendHeadersVersionMsgErr
            },
        ]

    def test_command(self):
        msg = MsgSendHeaders()
        self.assertEqual(str(msg.command()), "sendheaders")

    def test_max_payload_length(self):
        msg = MsgSendHeaders()
        want_payload = 0
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

        # Err conditions
        for c in self.err_tests:
            s = io.BytesIO()
            try:
                c['in'].btc_encode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgSendHeaders()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])

        # Err conditions
        for c in self.err_tests:
            s = io.BytesIO(c['buf'])
            msg = MsgSendHeaders()
            try:
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
