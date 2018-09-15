import unittest
from wire.msg_version import *


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

    def test_has_service(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)
        self.assertEqual(msg.services.b, 0)

        self.assertFalse(msg.has_service(ServiceFlag.SFNodeNetwork))

        # TODO
    def test_command(self):
        msg = MsgVersion(addr_me=self.me,
                         addr_you=self.you,
                         nonce=self.nonce,
                         last_block=self.last_block)

        self.assertEqual(str(msg.command()), "version")




