import unittest
from wire.msg_version import *
import io
from tests.utils import *

# baseVersion is used in the various tests as a baseline MsgVersion.
baseVersion = MsgVersion(addr_you=NetAddress(services=ServiceFlag.SFNodeNetwork,
                                             ip=ipaddress.ip_address("192.168.0.1"),
                                             port=8333,
                                             timestamp=0),  # Zero value -- no timestamp in version
                         addr_me=NetAddress(services=ServiceFlag.SFNodeNetwork,
                                            ip=ipaddress.ip_address("127.0.0.1"),
                                            port=8333,
                                            timestamp=0),  # Zero value -- no timestamp in version
                         protocol_version=60002,
                         services=ServiceFlag.SFNodeNetwork,
                         timestamp=0x495fab29,  # 2009-01-03 12:15:05 -0600 CST)
                         nonce=123123,  # 0x1e0f3
                         user_agent="/btcdtest:0.0.1/",  # "/btcdtest:0.0.1/",
                         last_block=234234  # 0x392fa
                         )

# baseVersionEncoded is the wire encoded bytes for baseVersion using protocol
# version 60002 and is used in the various tests.
baseVersionEncoded = bytes([
    0x62, 0xea, 0x00, 0x00,  # Protocol version 60002
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
    0x29, 0xab, 0x5f, 0x49, 0x00, 0x00, 0x00, 0x00,  # 64-bit Timestamp
    # AddrYou -- No timestamp for NetAddress in version message
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xff, 0xff, 0xc0, 0xa8, 0x00, 0x01,  # IP 192.168.0.1
    0x20, 0x8d,  # Port 8333 in big-endian
    # AddrMe -- No timestamp for NetAddress in version message
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
    0x20, 0x8d,  # Port 8333 in big-endian
    0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,  # Nonce
    0x10,  # Varint for user agent length
    0x2f, 0x62, 0x74, 0x63, 0x64, 0x74, 0x65, 0x73,
    0x74, 0x3a, 0x30, 0x2e, 0x30, 0x2e, 0x31, 0x2f,  # User agent
    0xfa, 0x92, 0x03, 0x00,  # Last block
])

# baseVersionBIP0037 is used in the various tests as a baseline MsgVersion for
# BIP0037.
baseVersionBIP0037 = MsgVersion(addr_you=NetAddress(services=ServiceFlag.SFNodeNetwork,
                                                    ip=ipaddress.ip_address("192.168.0.1"),
                                                    port=8333,
                                                    timestamp=0),  # Zero value -- no timestamp in version
                                addr_me=NetAddress(services=ServiceFlag.SFNodeNetwork,
                                                   ip=ipaddress.ip_address("127.0.0.1"),
                                                   port=8333,
                                                   timestamp=0),  # Zero value -- no timestamp in version
                                protocol_version=70001,
                                services=ServiceFlag.SFNodeNetwork,
                                timestamp=0x495fab29,  # 2009-01-03 12:15:05 -0600 CST)
                                nonce=123123,  # 0x1e0f3
                                user_agent="/btcdtest:0.0.1/",  # "/btcdtest:0.0.1/",
                                last_block=234234  # 0x392fa
                                )

# baseVersionBIP0037Encoded is the wire encoded bytes for baseVersionBIP0037
# using protocol version BIP0037Version and is used in the various tests.
baseVersionBIP0037Encoded = bytes([
    0x71, 0x11, 0x01, 0x00,  # Protocol version 70001
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
    0x29, 0xab, 0x5f, 0x49, 0x00, 0x00, 0x00, 0x00,  # 64-bit Timestamp
    # AddrYou -- No timestamp for NetAddress in version message
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xff, 0xff, 0xc0, 0xa8, 0x00, 0x01,  # IP 192.168.0.1
    0x20, 0x8d,  # Port 8333 in big-endian
    # AddrMe -- No timestamp for NetAddress in version message
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
    0x20, 0x8d,  # Port 8333 in big-endian
    0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,  # Nonce
    0x10,  # Varint for user agent length
    0x2f, 0x62, 0x74, 0x63, 0x64, 0x74, 0x65, 0x73,
    0x74, 0x3a, 0x30, 0x2e, 0x30, 0x2e, 0x31, 0x2f,  # User agent
    0xfa, 0x92, 0x03, 0x00,  # Last block
    0x01,  # Relay tx
])


class TestVersion(unittest.TestCase):
    def setUp(self):
        self.pver = ProtocolVersion
        self.last_block = 234234
        self.me = NetAddress(services=ServiceFlag.SFNodeNetwork,
                             ip=ipaddress.ip_address('127.0.0.1'),
                             port=8333)
        self.you = NetAddress(services=ServiceFlag.SFNodeNetwork,
                              ip=ipaddress.ip_address('192.168.0.1'),
                              port=8333)
        self.nonce = random_uint64()

    def test_init(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)
        self.assertEqual(msg.protocol_version, self.pver)
        self.assertEqual(msg.addr_me, self.me)
        self.assertEqual(msg.addr_you, self.you)
        self.assertEqual(msg.nonce, self.nonce)
        self.assertEqual(msg.user_agent, DefaultUserAgent)
        self.assertEqual(msg.last_block, self.last_block)
        self.assertFalse(msg.disable_relay_tx)

    def test_add_user_agent(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)

        msg.add_user_agent(name="myclient", version="1.2.3",
                           comments=["optional", "comments"])
        want_user_agent = DefaultUserAgent + "myclient:1.2.3(optional; comments)/"
        self.assertEqual(msg.user_agent, want_user_agent)

        msg.add_user_agent(name="mygui", version="3.4.5")

        want_user_agent += "mygui:3.4.5/"
        self.assertEqual(msg.user_agent, want_user_agent)
        try:
            msg.add_user_agent(name="t" * (MaxUserAgentLen - len(want_user_agent) - 2 + 1),
                               version="")
        except Exception as e:
            self.assertEqual(type(e), MessageVersionLengthTooLong)

    def test_has_service_add_service1(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)
        self.assertEqual(msg.services, 0)

        self.assertFalse(msg.has_service(ServiceFlag.SFNodeNetwork))

        msg.add_service(ServiceFlag.SFNodeNetwork)
        # self.assertEqual(msg.services.b, ServiceFlag.SFNodeNetwork.b)

        # self.assertTrue(msg.has_service(ServiceFlag.SFNodeNetwork))

    def test_command(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)

        self.assertEqual(str(msg.command()), "version")

    def test_max_payload_length(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)
        self.assertEqual(msg.max_payload_length(self.pver), 358)


# TestVersionWire tests the MsgVersion wire encode and decode for various
# protocol versions.
class TestVersionWire(unittest.TestCase):
    def setUp(self):
        self.verRelayTxFalse = MsgVersion(addr_you=NetAddress(services=ServiceFlag.SFNodeNetwork,
                                                              ip=ipaddress.ip_address("192.168.0.1"),
                                                              port=8333,
                                                              timestamp=0),  # Zero value -- no timestamp in version
                                          addr_me=NetAddress(services=ServiceFlag.SFNodeNetwork,
                                                             ip=ipaddress.ip_address("127.0.0.1"),
                                                             port=8333,
                                                             timestamp=0),  # Zero value -- no timestamp in version
                                          protocol_version=70001,
                                          services=ServiceFlag.SFNodeNetwork,
                                          timestamp=0x495fab29,  # 2009-01-03 12:15:05 -0600 CST)
                                          nonce=123123,  # 0x1e0f3
                                          user_agent="/btcdtest:0.0.1/",  # "/btcdtest:0.0.1/",
                                          last_block=234234,  # 0x392fa
                                          disable_relay_tx=True
                                          )
        self.verRelayTxFalseEncoded = bytes([
            0x71, 0x11, 0x01, 0x00,  # Protocol version 70001
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x29, 0xab, 0x5f, 0x49, 0x00, 0x00, 0x00, 0x00,  # 64-bit Timestamp
            # AddrYou -- No timestamp for NetAddress in version message
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0xc0, 0xa8, 0x00, 0x01,  # IP 192.168.0.1
            0x20, 0x8d,  # Port 8333 in big-endian
            # AddrMe -- No timestamp for NetAddress in version message
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # SFNodeNetwork
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0x7f, 0x00, 0x00, 0x01,  # IP 127.0.0.1
            0x20, 0x8d,  # Port 8333 in big-endian
            0xf3, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,  # Nonce
            0x10,  # Varint for user agent length
            0x2f, 0x62, 0x74, 0x63, 0x64, 0x74, 0x65, 0x73,
            0x74, 0x3a, 0x30, 0x2e, 0x30, 0x2e, 0x31, 0x2f,  # User agent
            0xfa, 0x92, 0x03, 0x00,  # Last block
            0x00,  # Relay tx
        ])
        self.tests = [
            # Latest protocol version.
            {
                "in": baseVersionBIP0037,
                "out": baseVersionBIP0037,
                "buf": baseVersionBIP0037Encoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            # Protocol version BIP0037Version with relay transactions field
            # true.
            {
                "in": baseVersionBIP0037,
                "out": baseVersionBIP0037,
                "buf": baseVersionBIP0037Encoded,
                "pver": BIP0037Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0037Version with relay transactions field
            # false.
            {
                "in": self.verRelayTxFalse,
                "out": self.verRelayTxFalse,
                "buf": self.verRelayTxFalseEncoded,
                "pver": BIP0037Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0035Version.
            {
                "in": baseVersion,
                "out": baseVersion,
                "buf": baseVersionEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding
            },

            # Protocol version BIP0031Version.
            {
                "in": baseVersion,
                "out": baseVersion,
                "buf": baseVersionEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding
            },

            # Protocol version NetAddressTimeVersion.
            {
                "in": baseVersion,
                "out": baseVersion,
                "buf": baseVersionEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding
            },

            # Protocol version MultipleAddressVersion.
            {
                "in": baseVersion,
                "out": baseVersion,
                "buf": baseVersionEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding
            },

        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c["in"].btc_encode(s, c["pver"], c["enc"])
            self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c["buf"])
            msg_version = MsgVersion(addr_you=None,
                                     addr_me=None,
                                     nonce=None,
                                     last_block=None)
            msg_version.btc_decode(s, c["pver"], c["enc"])
            self.assertEqual(msg_version, c['out'])


# class TestVersionWireErrors(unittest.TestCase):
#     def setUp(self):
#         self.pver = 60002
#         self.enc = BaseEncoding
#         self.wire_err = MessageErr
#
#         newUAVer = "/" + "t" * (MaxUserAgentLen - 8 + 1) + ":0.0.1/"
#
#
#     def test_btc_encode(self):
#
#         # Test for fix buf
#         fixed_reader = FixedBytesReader(0, bytes())
#         msg_version = MsgVersion(addr_you=None,
#                                  addr_me=None,
#                                  nonce=None,
#                                  last_block=None)
#         try:
#             msg_version.btc_decode(fixed_reader, self.pver, self.enc)
#         except Exception as e:
#             self.assertEqual(type(e), FixedBytesUnexpectedEOFErr)
