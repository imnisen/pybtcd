from .common import *


# MsgPing implements the Message interface and represents a bitcoin ping
# message.
#
# For versions BIP0031Version and earlier, it is used primarily to confirm
# that a connection is still valid.  A transmission error is typically
# interpreted as a closed connection and that the peer should be removed.
# For versions AFTER BIP0031Version it contains an identifier which can be
# returned in the pong message to determine network timing.
#
# The payload for this message just consists of a nonce used for identifying
# it later.
class MsgPing(Message):
    def __init__(self, nonce=None):
        self.nonce = nonce or 0

    def __eq__(self, other):
        return self.nonce == other.nonce

    def btc_decode(self, s, pver, message_encoding):
        # There was no nonce for BIP0031Version and earlier.
        # NOTE: > is not a mistake here.  The BIP0031 was defined as AFTER
        # the version unlike most others.
        if pver > BIP0031Version:
            self.nonce = read_element(s, "uint64")
        return

    def btc_encode(self, s, pver, message_encoding):
        # There was no nonce for BIP0031Version and earlier.
        # NOTE: > is not a mistake here.  The BIP0031 was defined as AFTER
        # the version unlike most others.
        if pver > BIP0031Version:
            write_element(s, "uint64", self.nonce)
        return

    def command(self) -> str:
        return Commands.CmdPing

    def max_payload_length(self, pver: int) -> int:
        if pver > BIP0031Version:
            return 8
        return 0
