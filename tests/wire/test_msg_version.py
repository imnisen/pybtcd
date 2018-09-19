import unittest
from tests.utils import *
from wire.msg_version import *

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


def new_empty_msg_version():
    return MsgVersion(addr_you=None,
                      addr_me=None,
                      nonce=0,
                      last_block=0)


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
            msg_version = new_empty_msg_version()
            msg_version.btc_decode(s, c["pver"], c["enc"])
            self.assertEqual(msg_version, c['out'])


class TestVersionWireErrors(unittest.TestCase):
    def setUp(self):
        self.pver = 60002
        self.enc = BaseEncoding
        self.wire_err = MessageErr

        new_user_agent = "/" + "t" * (MaxUserAgentLen - 8 + 1) + ":0.0.1/"

        self.exceedUAVer = MsgVersion(addr_you=NetAddress(services=ServiceFlag.SFNodeNetwork,
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
                                      user_agent=new_user_agent,  # Change new user agent here
                                      last_block=234234  # 0x392fa
                                      )
        var_int_buf = io.BytesIO()
        write_var_int(var_int_buf, self.pver, len(new_user_agent.encode()))

        var_int_buf_value = var_int_buf.getvalue()
        newLen = len(baseVersionEncoded) - len(baseVersion.user_agent.encode()) + len(var_int_buf_value) - 1 + len(
            new_user_agent.encode())

        # BaseVersionEncoded everything before and include nonce
        # + user_agent'var_int + user_agent
        # + baseVersionEncoded's last block
        self.exceedUAVerEncoded = baseVersionEncoded[
                                  0:80] + var_int_buf_value + new_user_agent.encode() + baseVersionEncoded[97:101]

        assert newLen == len(self.exceedUAVerEncoded)

        self.tests = [
            # Force error in protocol version.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 0,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in services.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 4,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in timestamp.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 12,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in remote address.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 20,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in local address.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 47,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in nonce.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 73,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in user agent length.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 81,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in user agent.
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 82,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in last block..
            {
                "in": baseVersion,
                "buf": baseVersionEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": 92,
                "write_err": FixedBytesShortWriteErr,
                "read_err": FixedBytesUnexpectedEOFErr
            },

            # Force error in relay tx - no read error should happen since it's optional.
            {
                "in": baseVersionBIP0037,
                "buf": baseVersionBIP0037Encoded,
                "pver": BIP0037Version,
                "enc": BaseEncoding,
                "max": 101,
                "write_err": FixedBytesShortWriteErr,
                "read_err": None
            },

            # Force error due to user agent too big
            {
                "in": self.exceedUAVer,
                "buf": self.exceedUAVerEncoded,
                "pver": self.pver,
                "enc": BaseEncoding,
                "max": newLen,
                "write_err": MessageVersionLengthTooLong,
                "read_err": MessageVersionLengthTooLong
            },

        ]

    def test_btc_decode(self):

        # Test for fix buf
        fixed_reader = FixedBytesReader(0, bytes())
        msg_version = new_empty_msg_version()
        try:
            msg_version.btc_decode(fixed_reader, self.pver, self.enc)
        except Exception as e:
            self.assertEqual(type(e), FixedBytesUnexpectedEOFErr)

        for c in self.tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg_version = new_empty_msg_version()
                msg_version.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])

    def test_btc_encode(self):
        for c in self.tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].btc_encode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])


class TestVersionOptionalFields(unittest.TestCase):
    def setUp(self):
        # onlyRequiredVersion is a version message that only contains the
        # required versions and all other values set to their default values.
        onlyRequiredVersion = MsgVersion(protocol_version=60002,
                                         services=ServiceFlag.SFNodeNetwork,
                                         timestamp=0x495fab29,
                                         addr_you=NetAddress(timestamp=0,
                                                             services=ServiceFlag.SFNodeNetwork,
                                                             ip=ipaddress.ip_address("192.168.0.1"),
                                                             port=8333))
        onlyRequiredVersionEncoded = baseVersionEncoded[:-55]

        # addrMeVersion is a version message that contains all fields through
        # the AddrMe field.
        addrMeVersion = MsgVersion(protocol_version=60002,
                                   services=ServiceFlag.SFNodeNetwork,
                                   timestamp=0x495fab29,
                                   addr_you=NetAddress(timestamp=0,
                                                       services=ServiceFlag.SFNodeNetwork,
                                                       ip=ipaddress.ip_address("192.168.0.1"),
                                                       port=8333),
                                   addr_me=NetAddress(
                                       timestamp=0,
                                       services=ServiceFlag.SFNodeNetwork,
                                       ip=ipaddress.ip_address("127.0.0.1"),
                                       port=8333))
        addrMeVersionEncoded = baseVersionEncoded[:-29]

        # onceVersion is a version message that contains all fields through
        # the Nonce field.
        nonceVersion = MsgVersion(protocol_version=60002,
                                  services=ServiceFlag.SFNodeNetwork,
                                  timestamp=0x495fab29,
                                  addr_you=NetAddress(timestamp=0,
                                                      services=ServiceFlag.SFNodeNetwork,
                                                      ip=ipaddress.ip_address("192.168.0.1"),
                                                      port=8333),
                                  addr_me=NetAddress(
                                      timestamp=0,
                                      services=ServiceFlag.SFNodeNetwork,
                                      ip=ipaddress.ip_address("127.0.0.1"),
                                      port=8333),
                                  nonce=123123)

        nonceVersionEncoded = baseVersionEncoded[:-21]

        # uaVersion is a version message that contains all fields through
        # the UserAgent field.
        uaVersion = MsgVersion(protocol_version=60002,
                               services=ServiceFlag.SFNodeNetwork,
                               timestamp=0x495fab29,
                               addr_you=NetAddress(timestamp=0,
                                                   services=ServiceFlag.SFNodeNetwork,
                                                   ip=ipaddress.ip_address("192.168.0.1"),
                                                   port=8333),
                               addr_me=NetAddress(
                                   timestamp=0,
                                   services=ServiceFlag.SFNodeNetwork,
                                   ip=ipaddress.ip_address("127.0.0.1"),
                                   port=8333),
                               nonce=123123,
                               user_agent="/btcdtest:0.0.1/")

        uaVersionEncoded = baseVersionEncoded[:-4]

        # lastBlockVersion is a version message that contains all fields
        # through the LastBlock field.
        lastBlockVersion = MsgVersion(protocol_version=60002,
                                      services=ServiceFlag.SFNodeNetwork,
                                      timestamp=0x495fab29,
                                      addr_you=NetAddress(timestamp=0,
                                                          services=ServiceFlag.SFNodeNetwork,
                                                          ip=ipaddress.ip_address("192.168.0.1"),
                                                          port=8333),
                                      addr_me=NetAddress(
                                          timestamp=0,
                                          services=ServiceFlag.SFNodeNetwork,
                                          ip=ipaddress.ip_address("127.0.0.1"),
                                          port=8333),
                                      nonce=123123,
                                      user_agent="/btcdtest:0.0.1/",
                                      last_block=234234)

        lastBlockVersionEncoded = baseVersionEncoded[:]

        self.tests = [
            {
                "msg": onlyRequiredVersion,
                "buf": onlyRequiredVersionEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            {
                "msg": addrMeVersion,
                "buf": addrMeVersionEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            {
                "msg": nonceVersion,
                "buf": nonceVersionEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            {
                "msg": uaVersion,
                "buf": uaVersionEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },

            {
                "msg": lastBlockVersion,
                "buf": lastBlockVersionEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding
            },
        ]

    def test_btc_decode(self):
        for c in self.tests:
            msg_version = new_empty_msg_version()
            s = io.BytesIO(c['buf'])
            msg_version.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg_version, c['msg'])
