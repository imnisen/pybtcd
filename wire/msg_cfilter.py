from .common import *


# FilterType is used to represent a filter type.
class FilterType(int):
    pass


# GCSFilterRegular is the regular filter type.
GCSFilterRegular = FilterType(0)

# MaxCFilterDataSize is the maximum byte size of a committed filter.
# The maximum size is currently defined as 256KiB.
MaxCFilterDataSize = 256 * 1024


# MsgCFilter implements the Message interface and represents a bitcoin cfilter
# message. It is used to deliver a committed filter in response to a
# getcfilters (MsgGetCFilters) message.
class MsgCFilter(Message):
    def __init__(self, filter_type, block_hash: Hash, data: bytes):
        self.filter_type = filter_type
        self.block_hash = block_hash
        self.data = data

    def __eq__(self, other):
        if not isinstance(other, MsgCFilter):
            return False
        return self.filter_type == other.filter_type and \
               self.block_hash == other.block_hash and \
               self.data == other.data

    def btc_decode(self, s, pver, message_encoding):
        self.filter_type = read_element(s, "FilterType")
        self.block_hash = read_element(s, "chainhash.Hash")
        self.data = read_var_bytes(s, pver, MaxCFilterDataSize, "cfilter data")
        return

    def btc_encode(self, s, pver, message_encoding):
        if len(self.data) > MaxCFilterDataSize:
            raise CFilterSizeTooLargeMsgErr

        write_element(s, "FilterType", self.filter_type)

        write_element(s, "chainhash.Hash", self.block_hash)

        write_var_bytes(s, pver, self.data)

        return

    # Deserialize decodes a filter from r into the receiver using a format that is
    # suitable for long-term storage such as a database. This function differs
    # from BtcDecode in that BtcDecode decodes from the bitcoin wire protocol as
    # it was sent across the network.  The wire encoding can technically differ
    # depending on the protocol version and doesn't even really need to match the
    # format of a stored filter at all. As of the time this comment was written,
    # the encoded filter is the same in both instances, but there is a distinct
    # difference and separating the two allows the API to be flexible enough to
    # deal with changes.
    def deserialize(self, s):
        # At the current time, there is no difference between the wire encoding
        # and the stable long-term storage format.  As a result, make use of
        # BtcDecode.
        self.btc_decode(s, pver=0, message_encoding=BaseEncoding)
        return

    def command(self) -> str:
        return Commands.CmdCFilter

    def max_payload_length(self, pver: int) -> int:
        return var_int_serialize_size(MaxCFilterDataSize) + MaxCFilterDataSize + HashSize + 1
