import chainhash
import wire
import io
import pyutil

# TxIndexUnknown is the value returned for a transaction index that is unknown.
# This is typically because the transaction has not been inserted into a block
# yet.
TxIndexUnknown = -1


# Tx defines a bitcoin transaction that provides easier and more efficient
# manipulation of raw transactions.  It also memoizes the hash for the
# transaction on its first access so subsequent accesses don't have to repeat
# the relatively expensive hashing operations.
class Tx:
    def __init__(self, msg_tx, tx_hash=None, tx_hash_witness=None,
                 tx_has_witness=None, tx_index=None):
        """

        :param wire.MsgTx msg_tx: Underlying MsgTx
        :param chainhash.Hash tx_hash: Cached transaction hash
        :param chainhash.Hash tx_hash_witness: Cached transaction witness hash
        :param bool tx_has_witness: If the transaction has witness data
        :param int tx_index: Position within a block or TxIndexUnknown
        """
        self.msg_tx = msg_tx
        self.tx_hash = tx_hash or None
        self.tx_hash_witness = tx_hash_witness or None
        self.tx_has_witness = tx_has_witness or None
        self.tx_index = tx_index or TxIndexUnknown

    @classmethod
    def from_reader(cls, r):
        msg_tx = wire.MsgTx()
        msg_tx.deserialize(r)
        return cls(msg_tx=msg_tx, tx_index=TxIndexUnknown)

    @classmethod
    def from_bytes(cls, serialized_tx: bytes):
        r = io.BytesIO(serialized_tx)
        return cls.from_reader(r)

    # MsgTx returns the underlying wire.MsgTx for the transaction.
    def get_msg_tx(self):
        return self.msg_tx

    # Hash returns the hash of the transaction.  This is equivalent to
    # calling TxHash on the underlying wire.MsgTx, however it caches the
    # result so subsequent calls are more efficient.
    def hash(self):
        if self.tx_hash is not None:
            return self.tx_hash

        hash = self.msg_tx.tx_hash()
        self.tx_hash = hash
        return hash

    # WitnessHash returns the witness hash (wtxid) of the transaction.  This is
    # equivalent to calling WitnessHash on the underlying wire.MsgTx, however it
    # caches the result so subsequent calls are more efficient.
    def witness_hash(self):
        if self.tx_hash_witness is not None:
            return self.tx_hash_witness

        hash = self.msg_tx.witness_hash()
        self.tx_hash_witness = hash
        return hash

    # HasWitness returns false if none of the inputs within the transaction
    # contain witness data, true false otherwise. This equivalent to calling
    # HasWitness on the underlying wire.MsgTx, however it caches the result so
    # subsequent calls are more efficient.
    def has_witness(self):
        if self.tx_has_witness is not None:
            return self.tx_has_witness

        has_witness = self.msg_tx.has_witness()
        self.tx_has_witness = has_witness
        return has_witness

    # Index returns the saved index of the transaction within a block.  This value
    # will be TxIndexUnknown if it hasn't already explicitly been set.
    def index(self):
        return self.tx_index

    def set_index(self, index: int):
        self.tx_index = index


    # IsCoinBase determines whether or not a transaction is a coinbase.  A coinbase
    # is a special transaction created by miners that has no inputs.  This is
    # represented in the block chain by a transaction with a single input that has
    # a previous output transaction index set to the maximum value along with a
    # zero hash.
    #
    # This function only differs from IsCoinBaseTx in that it works with a higher
    # level util transaction as opposed to a raw wire transaction.
    def is_coin_base(self):

        msg_tx = self.get_msg_tx()

        # A coin base must only have one transaction input.
        if len(msg_tx.tx_ins) != 1:
            return False

            # The previous output of a coin base must have a max value index and
        # a zero hash.
        prev_out = msg_tx.tx_ins[0].previous_out_point
        if prev_out.index != pyutil.MaxUint32 or prev_out.hash != chainhash.Hash():
            return False

        return True

