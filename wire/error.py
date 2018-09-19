class MessageErr(Exception):
    pass


class NonCanonicalVarIntErr(MessageErr):
    pass


class MessageLengthTooLongErr(MessageErr):
    pass


class BytesTooLargeErr(MessageErr):
    pass


class MessageExceedMaxInvPerMsgErr(MessageErr):
    pass


class MsgAddrTooManyErr(MessageErr):
    pass


class MaxBlockLocatorsPerMsgErr(MessageErr):
    pass


class MessageVersionLengthTooLong(MessageErr):
    pass
