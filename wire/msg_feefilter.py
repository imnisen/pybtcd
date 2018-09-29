from .common import *


class MsgFeeFilter(Message):
    def __init__(self, min_fee=None):
        self.min_fee = min_fee or 0

    def __eq__(self, other):
        return self.min_fee == other.min_fee

    def btc_decode(self, s, pver, message_encoding):
        if pver < FeeFilterVersion:
            raise BelowSendHeadersVersionMsgErr
        self.min_fee = read_element(s, "int64")
        return

    def btc_encode(self, s, pver, message_encoding):
        if pver < FeeFilterVersion:
            raise BelowSendHeadersVersionMsgErr
        write_element(s, "int64", self.min_fee)
        return

    def command(self) -> str:
        return Commands.CmdFeeFilter

    def max_payload_length(self, pver: int) -> int:
        return 8
