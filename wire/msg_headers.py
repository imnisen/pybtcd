from .blockheader import *
from .msg_tx import *

# MaxBlockHeadersPerMsg is the maximum number of block headers that can be in
# a single bitcoin headers message.
MaxBlockHeadersPerMsg = 2000


class MsgHeaders(Message):
    def __init__(self, headers=None):
        self.headers = headers or []

    def __eq__(self, other):
        if len(self.headers) == len(other.headers):
            for i in range(len(self.headers)):
                if self.headers[i] != other.headers[i]:
                    return False
            return True
        else:
            return False

    # TOCHECK
    # what does protocol[https://en.bitcoin.it/wiki/Protocol_documentation#headers] mean by:
    # Note that the block headers in this packet include a transaction count (a var_int, so there can be more than 81 bytes per header) as opposed to the block headers that are hashed by miners.
    def btc_decode(self, s, pver, message_encoding):
        count = read_var_int(s, pver)

        if count > MaxBlockHeadersPerMsg:
            raise MaxBlockHeadersPerMsgMsgErr

        for _ in range(count):
            bh = read_block_header(s, pver)

            # read always 0 txn_count in blockheader, but not include in our BlockHeader class
            tx_count = read_var_int(s, pver)
            if tx_count > 0:
                raise BlockHeadersTxCountNotZeroMsgErr

            self.add_block_header(bh)

        return

    def btc_encode(self, s, pver, message_encoding):
        count = len(self.headers)
        if count > MaxBlockHeadersPerMsg:
            raise MaxBlockHeadersPerMsgMsgErr

        # write count
        write_var_int(s, pver, count)

        # write headers
        for bh in self.headers:
            write_block_header(s, pver, bh)

            # The wire protocol encoding always includes a 0 for the number
            # of transactions on header messages.  This is really just an
            # artifact of the way the original implementation serializes
            # block headers, but it is required.
            write_var_int(s, pver, 0)

        return

    def command(self) -> str:
        return Commands.CmdHeaders

    def max_payload_length(self, pver: int) -> int:
        # Num headers (varInt) + max allowed headers (header length + 1 byte
        # for the number of transactions which is always 0).
        return MaxVarIntPayload + MaxBlockHeadersPerMsg * (MaxBlockHeaderPayload + 1)

    def add_block_header(self, bh):
        self.headers.append(bh)
        return
