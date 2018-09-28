from .common import *

# MaxFilterLoadHashFuncs is the maximum number of hash functions to
# load into the Bloom filter.
MaxFilterLoadHashFuncs = 50

# MaxFilterLoadFilterSize is the maximum size in bytes a filter may be.
MaxFilterLoadFilterSize = 36000


class MsgFilterLoad(Message):
    def __init__(self, filter=None, hash_funcs=None, tweak=None, flags=None):
        """

        :param uint8_t[] filter:
        :param uint32_t hash_funcs:
        :param uint32_t tweak:
        :param uint8_t/BloomUpdateType flags:
        """
        self.filter = filter or bytes()
        self.hash_funcs = hash_funcs or 0
        self.tweak = tweak or 0
        self.flags = flags or BloomUpdateType.BloomUpdateNone

    def __eq__(self, other):
        return self.filter == other.filter and \
               self.hash_funcs == other.hash_funcs and \
               self.tweak == other.tweak and \
               self.flags == other.flags

    def btc_decode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr

        self.filter = read_var_bytes(s, pver, MaxFilterLoadFilterSize, "filterload filter size")
        self.hash_funcs = read_element(s, "uint32")

        self.tweak = read_element(s, "uint32")
        self.flags = read_element(s, "BloomUpdateType")

        if self.hash_funcs > MaxFilterLoadHashFuncs:
            raise MaxFilterLoadHashFuncsMsgErr

        return

    def btc_encode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr
        if len(self.filter) > MaxFilterLoadFilterSize:
            raise MaxFilterLoadFilterSizeMsgErr

        if self.hash_funcs > MaxFilterLoadHashFuncs:
            raise MaxFilterLoadHashFuncsMsgErr

        write_var_bytes(s, pver, self.filter)
        write_element(s, "uint32", self.hash_funcs)
        write_element(s, "uint32", self.tweak)
        write_element(s, "BloomUpdateType", self.flags)

        return

    def command(self) -> str:
        return Commands.CmdFilterLoad

    def max_payload_length(self, pver: int) -> int:

        # TOCHECK in doc, there is no var int size of filter, stange!
        # Num filter bytes (varInt) + filter + 4 bytes hash funcs +
        # 4 bytes tweak + 1 byte flags.
        return var_int_serialize_size(MaxFilterLoadFilterSize) + MaxFilterLoadFilterSize + 9
