from .blockheader import *
from .msg_tx import *

# defaultTransactionAlloc is the default size used for the backing array
# for transactions.  The transaction array will dynamically grow as needed, but
# this figure is intended to provide enough space for the number of
# transactions in the vast majority of blocks without needing to grow the
# backing array multiple times.
defaultTransactionAlloc = 2048  # Not used

# MaxBlockPayload is the maximum bytes a block message can be in bytes.
# After Segregated Witness, the max block payload has been raised to 4MB.
MaxBlockPayload = 4000000

# maxTxPerBlock is the maximum number of transactions that could
# possibly fit into a block.
maxTxPerBlock = int((MaxBlockPayload / minTxPayload) + 1)

# MaxBlockPayload is the maximum bytes a block message can be in bytes.
# After Segregated Witness, the max block payload has been raised to 4MB.
MaxBlockPayload = 4000000


# TxLoc holds locator data for the offset and length of where a transaction is
# located within a MsgBlock data buffer.
class TxLoc:
    def __init__(self, tx_start, tx_len):
        self.tx_start = tx_start
        self.tx_len = tx_len

    def __eq__(self, other):
        return self.tx_start == other.tx_start and self.tx_len == other.tx_len


class MsgBlock(Message):
    def __init__(self, header=None, transactions=None):
        """

        :param BlockHeader header:
        :param [] transactions:
        """
        self.header = header or BlockHeader()
        self.transactions = transactions or []

    def __eq__(self, other):
        if self.header == other.header and len(self.transactions) == len(other.transactions):
            for i in range(len(self.transactions)):
                if self.transactions[i] != other.transactions[i]:
                    return False
            return True
        else:
            return False

    def btc_decode(self, s, pver, message_encoding):
        self.header = read_block_header(s, pver)

        tx_count = read_var_int(s, pver)
        if tx_count > maxTxPerBlock:
            raise MaxTxPerBlockMsgErr

        for _ in range(tx_count):
            msg_tx = MsgTx()
            msg_tx.btc_decode(s, pver, message_encoding)
            self.add_transaction(msg_tx)
        return

    def deserialize(self, s):
        self.btc_decode(s, pver=0, message_encoding=WitnessEncoding)
        return

    def deserialize_no_witness(self, s):
        self.btc_decode(s, pver=0, message_encoding=BaseEncoding)
        return

    def deserialize_tx_loc(self, s):
        # At the current time, there is no difference between the wire encoding
        # at protocol version 0 and the stable long-term storage format.  As
        # a result, make use of existing wire protocol functions.
        self.header = read_block_header(s, pver=0)

        tx_count = read_var_int(s, pver=0)
        if tx_count > maxTxPerBlock:
            raise MaxTxPerBlockMsgErr

        tx_loc_lst = []
        for _ in range(tx_count):
            tx_start = s.tell()

            msg_tx = MsgTx()
            msg_tx.deserialize(s)
            self.add_transaction(msg_tx)

            tx_len = s.tell() - tx_start

            tx_loc_lst.append(TxLoc(tx_start=tx_start, tx_len=tx_len))
        return tx_loc_lst

    def btc_encode(self, s, pver, message_encoding):
        # write header
        write_block_header(s, pver, self.header)

        # write tx count
        write_var_int(s, pver, len(self.transactions))

        # write every tx
        for tx in self.transactions:
            tx.btc_encode(s, pver, message_encoding)
        return

    def serialize(self, s):

        # At the current time, there is no difference between the wire encoding
        # at protocol version 0 and the stable long-term storage format.  As
        # a result, make use of BtcEncode.
        #
        # Passing WitnessEncoding as the encoding type here indicates that
        # each of the transactions should be serialized using the witness
        # serialization structure defined in BIP0141.
        self.btc_encode(s, pver=0, message_encoding=WitnessEncoding)
        return

    def serialize_no_witness(self, s):
        self.btc_encode(s, pver=0, message_encoding=BaseEncoding)
        return

    # SerializeSize returns the number of bytes it would take to serialize the
    # block, factoring in any witness data within transaction.
    def serialize_size(self):
        # Block header bytes + Serialized varint size for the number of
        # transactions.
        n = blockHeaderLen + var_int_serialize_size(len(self.transactions))

        for tx in self.transactions:
            n += tx.serialize_size()
        return n

    def serialize_size_stripped(self):
        # Block header bytes + Serialized varint size for the number of
        # transactions.
        n = blockHeaderLen + var_int_serialize_size(len(self.transactions))

        for tx in self.transactions:
            n += tx.serialize_size_stripped()
        return n

    # BlockHash computes the block identifier hash for this block.
    def block_hash(self) -> Hash():
        return self.header.block_hash()

    def tx_hashes(self):

        return [tx.tx_hash() for tx in self.transactions]

    def command(self) -> str:
        return Commands.CmdBlock

    def max_payload_length(self, pver: int) -> int:
        # Block header at 80 bytes + transaction count + max transactions
        # which can vary up to the MaxBlockPayload (including the block header
        # and transaction count).
        return MaxBlockPayload

    def add_transaction(self, tx):
        self.transactions.append(tx)
        return

    def clear_transactions(self):
        self.transactions = []
        return
