from .common import *

# MaxFilterAddDataSize is the maximum byte size of a data
# element to add to the Bloom filter.  It is equal to the
# maximum element size of a script.
MaxFilterAddDataSize = 520


class MsgFilterAdd(Message):
    def __init__(self, data=None):
        self.data = data

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
        self.data = read_var_bytes(s, pver, MaxFilterAddDataSize, "filteradd data")
        return

    def btc_encode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr

        if len(self.data) > MaxFilterAddDataSize:
            raise MaxFilterAddDataSizeMsgErr

        write_var_bytes(s, pver, self.data)
        return

    def command(self) -> str:
        return Commands.CmdFilterAdd

    def max_payload_length(self, pver: int) -> int:
        return var_int_serialize_size(MaxFilterAddDataSize) + MaxFilterAddDataSize
