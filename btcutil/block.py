import io
import chainhash
import wire


class Block:
    def __init__(self, msg_block, serialized_block, serialized_block_no_witness,
                 block_hash, block_height, transactions, txns_generated):
        """

        :param *wire.MsgBlock msg_block: Underlying MsgBlock
        :param []byte serialized_block: Serialized bytes for the block
        :param []byte serialized_block_no_witness: Serialized bytes for block w/o witness data
        :param *chainhash.Hash block_hash: Cached block hash
        :param int32 block_height: Height in the main block chain
        :param []*Tx transactions: Transactions
        :param bool txns_generated: ALL wrapped transactions generated
        """
        self.msg_block = msg_block
        self.serialized_block = serialized_block
        self.serialized_block_no_witness = serialized_block_no_witness
        self.block_hash = block_hash
        self.block_height = block_height
        self.transactions = transactions
        self.txns_generated = txns_generated

    # MsgBlock returns the underlying wire.MsgBlock for the Block.
    def msg_block(self):
        return self.msg_block

    # Bytes returns the serialized bytes for the Block.  This is equivalent to
    # calling Serialize on the underlying wire.MsgBlock, however it caches the
    # result so subsequent calls are more efficient.
    def bytes(self):
        # Return the cached serialized bytes if it has already been generated.
        if len(self.serialized_block):
            return self.serialized_block

        # Serialize the MsgBlock.
        w = io.BytesIO()
        self.msg_block.serilize(w)
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
        self.msg_block.serilize_no_witness(w)
        serialized_block_no_witness = w.getvalue()

        # Cache the serialized bytes and return them.
        self.serialized_block_no_witness = serialized_block_no_witness

        return serialized_block_no_witness

    # Hash returns the block identifier hash for the Block.  This is equivalent to
    # calling BlockHash on the underlying wire.MsgBlock, however it caches the
    # result so subsequent calls are more efficient.
    def hash(self):
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
    def tx(self, tx_num:int):
        pass
