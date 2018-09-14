import unittest
import io
import ipaddress
from wire.netaddress import *
from tests.utils import *


class TestNetAddress(unittest.TestCase):
    def setUp(self):
        self.ip = ipaddress.ip_address("127.0.0.1")
        self.port = 8333

    def test_has_and_add_service(self):
        na = NetAddress(ServiceFlag.EMPTY, self.ip, self.port)

        self.assertFalse(na.has_service(ServiceFlag.SFNodeNetwork))

        na.add_service(ServiceFlag.SFNodeNetwork)

        self.assertEqual(na.services, ServiceFlag.SFNodeNetwork)

        self.assertTrue(na.has_service(ServiceFlag.SFNodeNetwork))

    def test_max_netaddress_payload(self):
        pver = ProtocolVersion
        want_payload = 30
        self.assertEqual(max_netaddress_payload(pver), want_payload)

        pver = NetAddressTimeVersion - 1
        want_payload = 26
        self.assertEqual(max_netaddress_payload(pver), want_payload)


class TestNetAddressWire(unittest.TestCase):
    def setUp(self):
        self.baseNetAddr = NetAddress(services=ServiceFlag.SFNodeNetwork,
                                      ip=ipaddress.ip_address("127.0.0.1"),
                                      port=8333,
                                      timestamp=0x495fab29)  # 2009-01-03 12:15:05 -0600 CST
        self.baseNetAddrNoTS = NetAddress(services=ServiceFlag.SFNodeNetwork,
                                          ip=ipaddress.ip_address("127.0.0.1"),
                                          port=8333,
                                          timestamp=0)
        self.baseNetAddrEncoded = bytes([
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
            0x20, 0x8d,  # Port 8333 in big-endian

        ])
        self.baseNetAddrNoTSEncoded = bytes([
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
            0x20, 0x8d,  # Port 8333 in big-endian

        ])
        self.tests = [

            # Latest protocol version without ts flag.
            {
                "in": self.baseNetAddr,
                "out": self.baseNetAddrNoTS,
                "ts": False,
                "buf": self.baseNetAddrNoTSEncoded,
                "pver": ProtocolVersion
            },

            # Latest protocol version with ts flag.
            {
                "in": self.baseNetAddr,
                "out": self.baseNetAddr,
                "ts": True,
                "buf": self.baseNetAddrEncoded,
                "pver": ProtocolVersion
            },

            # Protocol version NetAddressTimeVersion without ts flag.
            {
                "in": self.baseNetAddr,
                "out": self.baseNetAddrNoTS,
                "ts": False,
                "buf": self.baseNetAddrNoTSEncoded,
                "pver": NetAddressTimeVersion
            },

            # Protocol version NetAddressTimeVersion with ts flag.
            {
                "in": self.baseNetAddr,
                "out": self.baseNetAddr,
                "ts": True,
                "buf": self.baseNetAddrEncoded,
                "pver": NetAddressTimeVersion
            },

            # Protocol version NetAddressTimeVersion-1 without ts flag.
            {
                "in": self.baseNetAddr,
                "out": self.baseNetAddrNoTS,
                "ts": False,
                "buf": self.baseNetAddrNoTSEncoded,
                "pver": NetAddressTimeVersion - 1
            },

            # Protocol version NetAddressTimeVersion-1 with timestamp.
            # Even though the timestamp flag is set, this shouldn't have a
            # timestamp since it is a protocol version before it was
            # added.
            {
                "in": self.baseNetAddr,
                "out": self.baseNetAddrNoTS,
                "ts": False,
                "buf": self.baseNetAddrNoTSEncoded,
                "pver": NetAddressTimeVersion - 1
            },

        ]

    def test_write_netaddress(self):
        for c in self.tests:
            writer = io.BytesIO()
            write_netaddress(writer, c['pver'], c['in'], c['ts'])
            writer.seek(0)
            self.assertEqual(writer.read(), c['buf'])


    def test_read_netaddress(self):
        for c in self.tests:
            reader = io.BytesIO(c['buf'])
            na = read_netaddress(reader, c['pver'], c['ts'])
            self.assertEqual(na, c['out'])

class TestNetAddressWireErrors(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.pverNAT = NetAddressTimeVersion -1

        self.baseNetAddr = NetAddress(services=ServiceFlag.SFNodeNetwork,
                                      ip=ipaddress.ip_address("127.0.0.1"),
                                      port=8333,
                                      timestamp=0x495fab29)  # 2009-01-03 12:15:05 -0600 CST

        self.tests = [
            # Latest protocol version with timestamp and intentional
		    # read/write errors.
            # Force errors on timestamp.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on services.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 4,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on ip.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 12,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on port.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 28,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Latest protocol version with timestamp and intentional
            # read/write errors.
            # Force errors on services.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on ip.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 8,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on port.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pver,
                "ts": True,
                "max": 24,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Protocol version before NetAddressTimeVersion with timestamp
            # flag set (should not have timestamp due to old protocol
            # version) and  intentional read/write errors.
            # Force errors on services.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pverNAT,
                "ts": True,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on ip.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pverNAT,
                "ts": True,
                "max": 8,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force errors on port.
            {
                "in": self.baseNetAddr,
                "buf": bytes(),
                "pver": self.pverNAT,
                "ts": True,
                "max": 24,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

        ]


    def test_write_netaddress(self):
        for c in self.tests:
            writer = FixedBytesWriter(c['max'])
            try:
                write_netaddress(writer, c['pver'], c['in'], c['ts'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])




    def test_read_netaddress(self):
        for c in self.tests:
            reader = FixedBytesReader(c['max'], c['buf'])
            try:
                read_netaddress(reader, c['pver'], c['ts'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
