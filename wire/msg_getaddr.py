from .common import *


class MsgGetAddr(Message):
    def __init__(self):
        pass

    def __eq__(self, other):
        if type(other) is MsgGetAddr:
            return True
        else:
            return False

    def btc_decode(self, s, pver, message_encoding):
        return None

    def btc_encode(self, s, pver, message_encoding):
        return None

    def command(self) -> str:
        return Commands.CmdGetAddr

    def max_payload_length(self, pver: int) -> int:
        return 0
