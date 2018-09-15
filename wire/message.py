from .protocol import BitcoinNet
from enum import Enum

# CommandSize is the fixed size of all commands in the common bitcoin message
# header.  Shorter commands must be zero padded.
CommandSize = 12


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
