from .blockheader import *
from .msg_tx import *
from .msg_block import maxTxPerBlock
from .utils import *

# maxFlagsPerMerkleBlock is the maximum number of flag bytes that could
# possibly fit into a merkle block.  Since each transaction is represented by
# a single bit, this is the max number of transactions per block divided by
# 8 bits per byte.  Then an extra one to cover partials.
maxFlagsPerMerkleBlock = int(maxTxPerBlock / 8)


class MsgMerkleBlock(Message):
    def __init__(self, header=None, transactions=None, hashes=None, flags=None):
        """

        :param BlockHeader header:
        :param int transactions:
        :param []Hash hashes:
        :param []byte flags:
        """
        self.header = header or BlockHeader()
        self.transactions = transactions or []
        self.hashes = hashes or []
        self.flags = flags or []

    def __eq__(self, other):
        return self.header == other.header and \
               self.transactions == other.transactions and \
               list_equal(self.hashes, other.hashes) and \
               self.flags == other.flags

    def add_tx_hash(self, hash):
        if len(self.hashes) + 1 > maxTxPerBlock:
            raise MaxTxPerBlockMsgErr
        self.hashes.append(hash)
        return

    def btc_decode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr

        self.header = read_block_header(s, pver)
        self.transactions = read_element(s, "uint32")

        count = read_var_int(s, pver)
        if count > maxTxPerBlock:
            raise MaxTxPerBlockMsgErr

        for _ in range(count):
            self.add_tx_hash(read_element(s, "chainhash.Hash"))

        self.flags = read_var_bytes(s, pver, maxFlagsPerMerkleBlock, "merkle block flags size")
        return

    def btc_encode(self, s, pver, message_encoding):
        if pver < BIP0037Version:
            raise NotSupportBelowBIP37MsgErr

        if len(self.hashes) > maxTxPerBlock:
            raise MaxTxPerBlockMsgErr

        if len(self.flags) > maxFlagsPerMerkleBlock:
            raise MaxFlagsPerMerkleBlockMsgErr

        # write header
        write_block_header(s, pver, self.header)

        # write transcations(a uint32 type)
        write_element(s, "uint32", self.transactions)

        # write tx count
        write_var_int(s, pver, len(self.hashes))

        # write every tx
        for hash in self.hashes:
            write_element(s, "chainhash.Hash", hash)

        # write flags
        write_var_bytes(s, pver, self.flags)
        return

    def command(self) -> str:
        return Commands.CmdMerkleBlock

    def max_payload_length(self, pver: int) -> int:
        return MaxBlockPayload
