from .message import *


class MsgInv(Message):
    def __init__(self, inv_list:list):
        self.inv_list = inv_list

    def btc_decode(self, s, pver, message_encoding):
        pass

    def btc_encode(self, s, pver, message_encoding):
        pass

    def command(self) -> str:
        return Commands.CmdInv

    def max_payload_length(self, pver: int) -> int:
        pass

    def __eq__(self, other):
        pass
