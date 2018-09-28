from .common import *


class MsgFilterClear(Message):
    def __init__(self, data=None):
        self.data = data or []

    def __eq__(self, other):
        if len(self.data) == len(other.data):
            for i in range(len(self.data)):
                if self.data[i] != other.data[i]:
                    return False
            return True
        else:
            return False

    def btc_decode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr
        return

    def btc_encode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr
        return

    def command(self) -> str:
        return Commands.CmdFilterClear

    def max_payload_length(self, pver: int) -> int:
        return 0
