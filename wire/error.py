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


class WitnessTxFlagByteMsgErr(MessageErr):
    pass


class MaxTxInPerMessageMsgErr(MessageErr):
    pass


class ReadScriptTooLongMsgErr(MessageErr):
    pass


class MaxTxOutPerMessageMsgErr(MessageErr):
    pass


class MaxWitnessItemsPerInputMsgErr(MessageErr):
    pass


class MaxTxPerBlockMsgErr(MessageErr):
    pass

class MaxBlockHeadersPerMsgMsgErr(MessageErr):
    pass

class BlockHeadersTxCountNotZeroMsgErr(MessageErr):
    pass