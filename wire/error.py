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


class MemPoolVerionBelowBIP35MsgErr(MessageErr):
    pass

class NotSupportBelowBIP35MsgErr(MessageErr):
    pass

class NotSupportBelowRejectVersionMsgErr(MessageErr):
    pass

class NotSupportBelowBIP37MsgErr(MessageErr):
    pass

class MaxFilterLoadHashFuncsMsgErr(MessageErr):
    pass

class MaxFilterLoadFilterSizeMsgErr(MessageErr):
    pass

class MaxFilterAddDataSizeMsgErr(MessageErr):
    pass

class MaxFlagsPerMerkleBlockMsgErr(MessageErr):
    pass