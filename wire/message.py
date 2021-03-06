from .protocol import *

# CommandSize is the fixed size of all commands in the common bitcoin message
# header.  Shorter commands must be zero padded.
CommandSize = 12

# BaseEncoding encodes all messages in the default format specified
# for the Bitcoin wire protocol.
BaseEncoding = 1 << 0

# WitnessEncoding encodes all messages other than transaction messages
# using the default Bitcoin wire protocol specification. For transaction
# messages, the new encoding format detailed in BIP0144 will be used.
WitnessEncoding = 1 << 1

# MaxMessagePayload is the maximum bytes a message can be regardless of other
# individual limits imposed by messages themselves.
MaxMessagePayload = (1024 * 1024 * 32)  # 32MB


class Commands(Enum):
    EMPTY = ""
    CmdVersion = "version"
    CmdVerAck = "verack"
    CmdGetAddr = "getaddr"
    CmdAddr = "addr"
    CmdGetBlocks = "getblocks"
    CmdInv = "inv"
    CmdGetData = "getdata"
    CmdNotFound = "notfound"
    CmdBlock = "block"
    CmdTx = "tx"
    CmdGetHeaders = "getheaders"
    CmdHeaders = "headers"
    CmdPing = "ping"
    CmdPong = "pong"
    CmdAlert = "alert"
    CmdMemPool = "mempool"
    CmdFilterAdd = "filteradd"
    CmdFilterClear = "filterclear"
    CmdFilterLoad = "filterload"
    CmdMerkleBlock = "merkleblock"
    CmdReject = "reject"
    CmdSendHeaders = "sendheaders"
    CmdFeeFilter = "feefilter"
    CmdGetCFilters = "getcfilters"
    CmdGetCFHeaders = "getcfheaders"
    CmdGetCFCheckpt = "getcfcheckpt"
    CmdCFilter = "cfilter"
    CmdCFHeaders = "cfheaders"
    CmdCFCheckpt = "cfcheckpt"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, s):
        for c in cls:
            if c.value == s:
                return c
        raise ValueError(cls.__name__ + ' has no value matching "' + s + '"')


# Message is an interface that describes a bitcoin message.  A type that
# implements Message has complete control over the representation of its data
# and may therefore contain additional or fewer fields than those which
# are used directly in the protocol encoded message.
class Message:
    def btc_decode(self, s, pver, message_encoding):
        raise NotImplementedError

    def btc_encode(self, s, pver, message_encoding):
        raise NotImplementedError

    def command(self) -> str:
        raise NotImplementedError

    def max_payload_length(self, pver: int) -> int:
        raise NotImplementedError

        # def __init__(self, command: str) -> 'Message':
        #     # TODADD dispatch
        #     pass


class MessageHeader:
    def __init__(self, magic: BitcoinNet, command: str, length: int, checksum: bytes):
        self.magic = magic
        self.command = command
        self.length = length
        self.checksum = checksum


class RejectCode(Enum):
    EMPTY = (0x00, "")
    RejectMalformed = (0x01, "REJECT_MALFORMED")
    RejectInvalid = (0x10, "REJECT_INVALID")
    RejectObsolete = (0x11, "REJECT_OBSOLETE")
    RejectDuplicate = (0x12, "REJECT_DUPLICATE")
    RejectNonstandard = (0x40, "REJECT_NONSTANDARD")
    RejectDust = (0x41, "REJECT_DUST")
    RejectInsufficientFee = (0x42, "REJECT_INSUFFICIENTFEE")
    RejectCheckpoint = (0x43, "REJECT_CHECKPOINT")

    def __str__(self):
        return self.value[1]

    @classmethod
    def from_string(cls, s):
        for bitcoin_net in cls:
            if bitcoin_net.value[1] == s:
                return bitcoin_net
        raise ValueError(cls.__name__ + ' has no value matching "' + s + '"')

    @classmethod
    def from_int(cls, i):
        for flagService in cls:
            if flagService.value[0] == i:
                return flagService
        raise ValueError(cls.__name__ + ' has no value matching "' + str(i) + '"')


class BloomUpdateType(Enum):
    # BloomUpdateNone indicates the filter is not adjusted when a match is
    # found.
    BloomUpdateNone = 0

    # BloomUpdateAll indicates if the filter matches any data element in a
    # public key script, the outpoint is serialized and inserted into the
    # filter.
    BloomUpdateAll = 1

    # BloomUpdateP2PubkeyOnly indicates if the filter matches a data
    # element in a public key script and the script is of the standard
    # pay-to-pubkey or multisig, the outpoint is serialized and inserted
    # into the filter.
    BloomUpdateP2PubkeyOnly = 2
