from .common import *


class MsgMemPool(Message):
    def __init__(self):
        pass

    def __eq__(self, other):
        if type(other) is MsgMemPool:
            return True
        else:
            return False

    def btc_decode(self, s, pver, message_encoding):
        if pver < BIP0035Version:
            raise MemPoolVerionBelowBIP35MsgErr
        return None

    def btc_encode(self, s, pver, message_encoding):
        if pver < BIP0035Version:
            raise MemPoolVerionBelowBIP35MsgErr
        return None

    def command(self) -> str:
        return Commands.CmdMemPool

    def max_payload_length(self, pver: int) -> int:
        return 0
