import io
import chainhash
import wire
from .error import *
from .tx import *

# BlockHeightUnknown is the value returned for a block height that is unknown.
# This is typically because the block has not been inserted into the main chain
# yet.
BlockHeightUnknown = -1

class Block:
    def __init__(self, msg_block, serialized_block=None, serialized_block_no_witness=None,
                 block_hash=None, block_height=None, transactions=None, txns_generated=None):
        """

        :param wire.MsgBlock msg_block: Underlying MsgBlock
        :param []byte serialized_block: Serialized bytes for the block
        :param []byte serialized_block_no_witness: Serialized bytes for block w/o witness data
        :param chainhash.Hash or None block_hash: Cached block hash
        :param int32 block_height: Height in the main block chain
        :param []*Tx transactions: Transactions
        :param bool txns_generated: ALL wrapped transactions generated
        """
        self.msg_block = msg_block
        self.serialized_block = serialized_block or bytes()
        self.serialized_block_no_witness = serialized_block_no_witness or bytes()
        self.block_hash = block_hash or None
        self.block_height = block_height or BlockHeightUnknown
        self.transactions = transactions or []
        self.txns_generated = txns_generated or False

    @classmethod
    def from_reader(cls, r):
        msg_block = wire.MsgBlock()
        msg_block.deserialize(r)
        return cls(msg_block=msg_block, block_height=BlockHeightUnknown)

    @classmethod
    def from_bytes(cls, serialized_block: bytes):
        r = io.BytesIO(serialized_block)
        return cls.from_reader(r)

    @classmethod
    def from_block_and_bytes(cls, msg_block, serialized_block):
        return cls(msg_block=msg_block, serialized_block=serialized_block, block_height=BlockHeightUnknown)


    # TODO same name as filed, fix latter
    # MsgBlock returns the underlying wire.MsgBlock for the Block.
    def get_msg_block(self):
        return self.msg_block

    # Bytes returns the serialized bytes for the Block.  This is equivalent to
    # calling Serialize on the underlying wire.MsgBlock, however it caches the
    # result so subsequent calls are more efficient.
    def bytes(self) -> bytes:
        # Return the cached serialized bytes if it has already been generated.
        if len(self.serialized_block):
            return self.serialized_block

        # Serialize the MsgBlock.
        w = io.BytesIO()
        self.msg_block.serialize(w)
        serialized_block = w.getvalue()

        # Cache the serialized bytes and return them.
        self.serialized_block = serialized_block

        return serialized_block

    # BytesNoWitness returns the serialized bytes for the block with transactions
    # encoded without any witness data.
    def bytes_no_witness(self):
        # Return the cached serialized bytes if it has already been generated.
        if len(self.serialized_block_no_witness):
            return self.serialized_block_no_witness

        # Serialize the MsgBlock.
        w = io.BytesIO()
        self.msg_block.serialize_no_witness(w)
        serialized_block_no_witness = w.getvalue()

        # Cache the serialized bytes and return them.
        self.serialized_block_no_witness = serialized_block_no_witness

        return serialized_block_no_witness

    # Hash returns the block identifier hash for the Block.  This is equivalent to
    # calling BlockHash on the underlying wire.MsgBlock, however it caches the
    # result so subsequent calls are more efficient.
    def hash(self) -> chainhash.Hash:
        if self.block_hash:
            return self.block_hash

        hash = self.msg_block.block_hash()
        self.block_hash = hash
        return hash

    # Tx returns a wrapped transaction (btcutil.Tx) for the transaction at the
    # specified index in the Block.  The supplied index is 0 based.  That is to
    # say, the first transaction in the block is txNum 0.  This is nearly
    # equivalent to accessing the raw transaction (wire.MsgTx) from the
    # underlying wire.MsgBlock, however the wrapped transaction has some helpful
    # properties such as caching the hash so subsequent calls are more efficient.
    def tx(self, tx_idx: int):
        num_tx = len(self.msg_block.transactions)

        if tx_idx < 0 or tx_idx > num_tx - 1:
            msg = "transaction index %d is out of range - max %d" % (tx_idx, num_tx - 1)
            raise OutOfRangeError(msg)

        if len(self.transactions) == 0:
            self.transactions = [None] * num_tx

        if self.transactions[tx_idx]:
            return self.transactions[tx_idx]

        new_tx = Tx(self.msg_block.transactions[tx_idx])
        new_tx.set_index(tx_idx)
        self.transactions[tx_idx] = new_tx
        return new_tx

    # Transactions returns a slice of wrapped transactions (btcutil.Tx) for all
    # transactions in the Block.  This is nearly equivalent to accessing the raw
    # transactions (wire.MsgTx) in the underlying wire.MsgBlock, however it
    # instead provides easy access to wrapped versions (btcutil.Tx) of them.
    def get_transactions(self):
        # Return transactions if they have ALL already been generated.  This
        # flag is necessary because the wrapped transactions are lazily
        # generated in a sparse fashion.
        if self.txns_generated:
            return self.transactions

        if len(self.transactions) == 0:
            self.transactions = [None] * len(self.msg_block.transactions)

        for i, tx in enumerate(self.transactions):
            if not tx:
                new_tx = Tx(self.msg_block.transactions[i])
                new_tx.set_index(i)
                self.transactions[i] = new_tx

        self.txns_generated = True
        return self.transactions

    # TxHash returns the hash for the requested transaction number in the Block.
    # The supplied index is 0 based.  That is to say, the first transaction in the
    # block is txNum 0.  This is equivalent to calling TxHash on the underlying
    # wire.MsgTx, however it caches the result so subsequent calls are more
    # efficient.
    def tx_hash(self, tx_idx):
        # Attempt to get a wrapped transaction for the specified index.  It
        # will be created lazily if needed or simply return the cached version
        # if it has already been generated.
        tx = self.tx(tx_idx)

        # Defer to the wrapped transaction which will return the cached hash if
        # it has already been generated.
        return tx.hash()

    # TxLoc returns the offsets and lengths of each transaction in a raw block.
    # It is used to allow fast indexing into transactions within the raw byte
    # stream.
    def tx_loc(self):
        raw_msg = self.bytes()
        rbuf = io.BytesIO(raw_msg)

        mblock = wire.MsgBlock()
        tx_locs = mblock.deserialize_tx_loc(rbuf)
        return tx_locs

    def height(self):
        return self.block_height

    def set_height(self, height:int):
        self.block_height = height

