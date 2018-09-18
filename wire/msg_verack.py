from .message import *


class MsgVerAck(Message):
    def btc_decode(self, s, pver, message_encoding):
        return

    def btc_encode(self, s, pver, message_encoding):
        return

    def command(self) -> str:
        return Commands.CmdVerAck

    def max_payload_length(self, pver: int) -> int:
        return 0

    def __eq__(self, other):
        return type(other) is MsgVerAck
