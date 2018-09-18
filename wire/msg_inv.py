from .message import *
from .invvect import *


class MsgInv(Message):
    def __init__(self, inv_list: list):
        self.inv_list = inv_list

    def btc_decode(self, s, pver, message_encoding):
        count = read_var_int(s, pver)
        if count > MaxInvPerMsg:
            raise MessageExceedMaxInvPerMsgErr
        for _ in range(count):
            iv = read_inv_vect(s, pver)
            self.add_inv_vect(iv)
        return

    def btc_encode(self, s, pver, message_encoding):
        count = len(self.inv_list)
        if count > MaxInvPerMsg:
            raise MessageExceedMaxInvPerMsgErr

        write_var_int(s, pver, count)

        for iv in self.inv_list:
            write_inv_vect(s, pver, iv)
        return

    def command(self) -> str:
        return Commands.CmdInv

    def max_payload_length(self, pver: int) -> int:
        return MaxVarIntPayload + (MaxInvPerMsg * maxInvVectPayload)

    def __eq__(self, other):
        if type(other) is MsgInv and \
                        len(self.inv_list) == len(other.inv_list):

            all_equal = True
            for i, m in enumerate(self.inv_list):
                if m != other.inv_list[i]:
                    all_equal = False
            return all_equal

        else:
            return False

    def add_inv_vect(self, iv):
        if len(self.inv_list) + 1 > MaxInvPerMsg:
            raise MessageExceedMaxInvPerMsgErr
        self.inv_list.append(iv)
        return
