from .protocol import BitcoinNet
from enum import Enum

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


class Commands(Enum):
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
