from .common import *


class MsgSendHeaders(Message):
    def __init__(self):
        pass

    def __eq__(self, other):
        if type(other) is MsgSendHeaders:
            return True
        else:
            return False

    def btc_decode(self, s, pver, message_encoding):
        if pver < SendHeadersVersion:
            raise BelowSendHeadersVersionMsgErr

        return None

    def btc_encode(self, s, pver, message_encoding):
        if pver < SendHeadersVersion:
            raise BelowSendHeadersVersionMsgErr
        return None

    def command(self) -> str:
        return Commands.CmdSendHeaders

    def max_payload_length(self, pver: int) -> int:
        return 0
