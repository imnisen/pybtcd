import unittest
import io
from wire.msg_mempool import *


class TestMsgMemPool(unittest.TestCase):
    def setUp(self):
        pver = ProtocolVersion
        oldPver = BIP0035Version - 1

        msgMemPool = MsgMemPool()
        msgMemPoolEncoded = bytes([])

        self.tests = [
            # Latest protocol version.
            {
                "in": msgMemPool,
                "out": msgMemPool,
                "buf": msgMemPoolEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "err": None
            },

            # Protocol version BIP0035Version -1 .
            {
                "in": msgMemPool,
                "out": msgMemPool,
                "buf": msgMemPoolEncoded,
                "pver": oldPver,
                "enc": BaseEncoding,
                "err": MemPoolVerionBelowBIP35MsgErr
            },
        ]

    def test_command(self):
        msg = MsgMemPool()
        self.assertEqual(str(msg.command()), "mempool")

    def test_max_payload_length(self):
        msg = MsgMemPool()
        want_payload = 0
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_btc_encode(self):
        for c in self.tests:
            if c["err"]:
                try:
                    s = io.BytesIO()
                    c['in'].btc_encode(s, c['pver'], c['enc'])
                except Exception as e:
                    self.assertEqual(type(e), c['err'])
            else:
                s = io.BytesIO()
                c['in'].btc_encode(s, c['pver'], c['enc'])
                self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_decode(self):
        for c in self.tests:
            if c['err']:
                try:
                    s = io.BytesIO(c['buf'])
                    msg = MsgMemPool()
                    msg.btc_decode(s, c['pver'], c['enc'])
                except Exception as e:
                    self.assertEqual(type(e), c['err'])
            else:
                s = io.BytesIO(c['buf'])
                msg = MsgMemPool()
                msg.btc_decode(s, c['pver'], c['enc'])
                self.assertEqual(msg, c['out'])
