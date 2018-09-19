import unittest
from tests.utils import *
from wire.msg_addr import *

class TestAddr(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion

    def test_command(self):
        msg = MsgAddr()
        self.assertEqual(str(msg.command()), "addr")

    def test_max_payload_length(self):
        msg = MsgAddr()
        want_payload = 30009
        self.assertEqual(msg.max_payload_length(self.pver), want_payload)

        pver2 = NetAddressTimeVersion - 1
        want_payload2 = 26009
        self.assertEqual(msg.max_payload_length(pver2), want_payload2)

        pver3 = MultipleAddressVersion - 1
        want_payload3 = 35
        self.assertEqual(msg.max_payload_length(pver3), want_payload3)

    def test_add_address(self):
        msg = MsgAddr()
        na = NetAddress(services=ServiceFlag.SFNodeNetwork,
                        ip=ipaddress.ip_address("127.0.0.1"),
                        port=8333)
        msg.add_address(na)
        self.assertEqual(msg.addr_list[0], na)

        # test MaxAddrPerMsg
        msg2 = MsgAddr()
        na = NetAddress(services=ServiceFlag.SFNodeNetwork,
                        ip=ipaddress.ip_address("127.0.0.1"),
                        port=8333)
        try:
            for _ in range(MaxAddrPerMsg + 1):
                msg2.add_address(na)
        except Exception as e:
            self.assertEqual(type(e), MsgAddrTooManyErr)

        try:
            msg2.add_address(na)
        except Exception as e:
            self.assertEqual(type(e), MsgAddrTooManyErr)

    def test_add_addresses(self):
        msg = MsgAddr()
        na = NetAddress(services=ServiceFlag.SFNodeNetwork,
                        ip=ipaddress.ip_address("127.0.0.1"),
                        port=8333)
        na2 = NetAddress(timestamp=0x495fab29,
                         services=ServiceFlag.SFNodeNetwork,
                         ip=ipaddress.ip_address("192.168.0.1"),
                         port=8334)
        msg.add_addresses([na, na2])
        self.assertEqual(msg.addr_list[0], na)
        self.assertEqual(msg.addr_list[1], na2)
        self.assertEqual(len(msg.addr_list), 2)

    def test_clear_addresses(self):
        msg = MsgAddr()
        na = NetAddress(services=ServiceFlag.SFNodeNetwork,
                        ip=ipaddress.ip_address("127.0.0.1"),
                        port=8333)
        msg.add_address(na)
        self.assertEqual(msg.addr_list[0], na)

        msg.clear_addresses()

        self.assertEqual(len(msg.addr_list), 0)


class TestAddrWire(unittest.TestCase):
    def setUp(self):
        na = NetAddress(timestamp=0x495fab29,
                        services=ServiceFlag.SFNodeNetwork,
                        ip=ipaddress.ip_address("127.0.0.1"),
                        port=8333)
        na2 = NetAddress(timestamp=0x495fab29,
                         services=ServiceFlag.SFNodeNetwork,
                         ip=ipaddress.ip_address("192.168.0.1"),
                         port=8334)

        noAddr = MsgAddr()
        noAddrEncoded = bytes([0x00])

        multiAddr = MsgAddr()
        multiAddr.add_addresses([na, na2])
        multiAddrEncoded = bytes([
            0x02,  # Varint for number of addresses
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
            0x20, 0x8d,  # Port 8333 in big-endian
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0xc0, 0xa8, 0x00, 0x01,  # IP 192.168.0.1
            0x20, 0x8e,  # Port 8334 in big-endian
        ])

        self.tests = [
            # Latest protocol version with no addresses.
            {
                "in": noAddr,
                "out": noAddr,
                "buf": noAddrEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Latest protocol version with multiple addresses.
            {
                "in": multiAddr,
                "out": multiAddr,
                "buf": multiAddrEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version MultipleAddressVersion-1 with no addresses.
            {
                "in": noAddr,
                "out": noAddr,
                "buf": noAddrEncoded,
                "pver": MultipleAddressVersion - 1,
                "enc": BaseEncoding
            },
        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgAddr()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])


class TestAddrWireErrors(unittest.TestCase):
    def setUp(self):
        pver = ProtocolVersion
        pverMA = MultipleAddressVersion

        na = NetAddress(timestamp=0x495fab29,
                        services=ServiceFlag.SFNodeNetwork,
                        ip=ipaddress.ip_address("127.0.0.1"),
                        port=8333)

        na2 = NetAddress(timestamp=0x495fab29,
                         services=ServiceFlag.SFNodeNetwork,
                         ip=ipaddress.ip_address("192.168.0.1"),
                         port=8334)

        baseAddr = MsgAddr()
        baseAddr.add_addresses([na, na2])
        baseAddrEncoded = bytes([
            0x02,  # Varint for number of addresses
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
            0x20, 0x8d,  # Port 8333 in big-endian
            0x29, 0xab, 0x5f, 0x49,  # Timestamp
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0xc0, 0xa8, 0x00, 0x01,  # IP 192.168.0.1
            0x20, 0x8e,  # Port 8334 in big-endian
        ])

        maxAddr = MsgAddr()
        for _ in range(MaxAddrPerMsg):
            maxAddr.add_address(na)

        maxAddr.addr_list.append(na)
        maxAddrEncoded = bytes([
            0xfd, 0x03, 0xe9,  # Varint for number of addresses (1001)
        ])

        self.tests = [
            # Latest protocol version with intentional read/write errors.

            # Force error in addresses count
            {
                "in": baseAddr,
                "buf": baseAddrEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in address list.
            {
                "in": baseAddr,
                "buf": baseAddrEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 1,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error with greater than max inventory vectors.
            {
                "in": maxAddr,
                "buf": maxAddrEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 3,
                "write_err": MsgAddrTooManyErr,
                "read_err": MsgAddrTooManyErr,
            },

            # Force error with greater than max inventory vectors.
            {
                "in": maxAddr,
                "buf": maxAddrEncoded,
                "pver": pver,
                "enc": BaseEncoding,
                "max": 3,
                "write_err": MsgAddrTooManyErr,
                "read_err": MsgAddrTooManyErr,
            },

            # Force error with greater than max inventory vectors for
            # protocol versions before multiple addresses were allowed.
            {
                "in": maxAddr,
                "buf": maxAddrEncoded,
                "pver": pverMA - 1,
                "enc": BaseEncoding,
                "max": 3,
                "write_err": MsgAddrTooManyErr,
                "read_err": MsgAddrTooManyErr,
            }
        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].btc_encode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        for c in self.tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgAddr()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])
