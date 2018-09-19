import unittest
from wire.msg_inv import *
from tests.utils import *


class TestInv(unittest.TestCase):
    def test_command(self):
        msg = MsgInv()
        self.assertEqual(str(msg.command()), "inv")

    def test_max_payload_length(self):
        msg = MsgInv()
        want_payload = 1800009
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_add_address(self):
        msg = MsgInv()
        hash = Hash()
        iv = InvVect(InvType.InvTypeBlock, hash)
        msg.add_inv_vect(iv)
        self.assertEqual(msg.inv_list[0], iv)

        try:
            for _ in range(MaxInvPerMsg):
                msg.add_inv_vect(iv)
        except Exception as e:
            self.assertEqual(type(e), MessageExceedMaxInvPerMsgErr)


class TestInvWire(unittest.TestCase):
    pass


class TestInvWireErrors(unittest.TestCase):
    pass
