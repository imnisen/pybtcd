import chainhash
import wire
import io
from .read_write_lock import RWLock

# calcHashPrevOuts calculates a single hash of all the previous outputs
# (txid:index) referenced within the passed transaction. This calculated hash
# can be re-used when validating all inputs spending segwit outputs, with a
# signature hash type of SigHashAll. This allows validation to re-use previous
# hashing computation, reducing the complexity of validating SigHashAll inputs
# from  O(N^2) to O(N).
def calc_hash_prevouts(tx: wire.MsgTx):
    """

    :param wire.MsgTx tx:
    :return:
    """
    buffer = io.BytesIO()
    for tx_in in tx.tx_ins:
        # First write out the 32-byte transaction ID one of whose
        # outputs are being referenced by this input.
        buffer.write(tx_in.previous_out_point.hash.to_bytes())

        # Next, we'll encode the index of the referenced output as a
        # little endian integer.
        buffer.write(tx_in.previous_out_point.index.to_bytes(4, byteorder="little"))

    return chainhash.double_hash_h(buffer.getvalue())


# calcHashSequence computes an aggregated hash of each of the sequence numbers
# within the inputs of the passed transaction. This single hash can be re-used
# when validating all inputs spending segwit outputs, which include signatures
# using the SigHashAll sighash type. This allows validation to re-use previous
# hashing computation, reducing the complexity of validating SigHashAll inputs
# from O(N^2) to O(N).
def calc_hash_sequence(tx: wire.MsgTx):
    """

    :param wire.MsgTx tx:
    :return:
    """
    buffer = io.BytesIO()
    for tx_in in tx.tx_ins:
        buffer.write(tx_in.sequence.to_bytes(4, byteorder="little"))

    return chainhash.double_hash_h(buffer.getvalue())


# calcHashOutputs computes a hash digest of all outputs created by the
# transaction encoded using the wire format. This single hash can be re-used
# when validating all inputs spending witness programs, which include
# signatures using the SigHashAll sighash type. This allows computation to be
# cached, reducing the total hashing complexity from O(N^2) to O(N).
def calc_hash_outputs(tx: wire.MsgTx):
    """

    :param wire.MsgTx tx:
    :return:
    """
    buffer = io.BytesIO()
    for tx_out in tx.tx_outs:
        wire.write_tx_out(buffer, 0, 0, tx_out)

    return chainhash.double_hash_h(buffer.getvalue())


# TxSigHashes houses the partial set of sighashes introduced within BIP0143.
# This partial set of sighashes may be re-used within each input across a
# transaction when validating all inputs. As a result, validation complexity
# for SigHashAll can be reduced by a polynomial factor.
class TxSigHashes:
    def __init__(self, hash_prev_outs=None, hash_sequence=None, hash_outputs=None):
        """

        :param chainhash.Hash hash_prev_outs:
        :param chainhash.Hash hash_sequence:
        :param chainhash.Hash hash_outputs:
        """

        self.hash_prev_outs = hash_prev_outs or chainhash.Hash()
        self.hash_sequence = hash_sequence or chainhash.Hash()
        self.hash_outputs = hash_outputs or chainhash.Hash()

    def __eq__(self, other):
        return self.hash_prev_outs == other.hash_prev_outs and \
               self.hash_sequence == other.hash_sequence and \
               self.hash_outputs == other.hash_outputs

    @classmethod
    def from_msg_tx(cls, tx):
        return cls(hash_prev_outs=calc_hash_prevouts(tx),
                   hash_sequence=calc_hash_sequence(tx),
                   hash_outputs=calc_hash_outputs(tx))


# HashCache houses a set of partial sighashes keyed by txid. The set of partial
# sighashes are those introduced within BIP0143 by the new more efficient
# sighash digest calculation algorithm. Using this threadsafe shared cache,
# multiple goroutines can safely re-use the pre-computed partial sighashes
# speeding up validation time amongst all inputs found within a block.
class HashCache:
    def __init__(self, sig_hashes=None, lock=None):
        """

        :param dict{Hash->TxSigHashes} sig_hashes:
        :param RWLock lock:
        """
        self.sig_hashes = sig_hashes or {}
        self.lock = lock or RWLock()

    # AddSigHashes computes, then adds the partial sighashes for the passed
    # transaction.
    def add_sig_hashes(self, tx: wire.MsgTx):
        self.lock.writer_acquire()
        self.sig_hashes[tx.tx_hash()] = TxSigHashes.from_msg_tx(tx)
        self.lock.writer_release()
        return

    # ContainsHashes returns true if the partial sighashes for the passed
    # transaction currently exist within the HashCache, and false otherwise.
    def contain_hashes(self, txid: chainhash.Hash):
        self.lock.reader_acquire()
        found = txid in self.sig_hashes
        self.lock.reader_release()
        return found

    # GetSigHashes possibly returns the previously cached partial sighashes for
    # the passed transaction. This function also returns an additional boolean
    # value indicating if the sighashes for the passed transaction were found to
    # be present within the HashCache.
    def get_sig_hashes(self, txid: chainhash.Hash):
        self.lock.reader_acquire()
        item = self.sig_hashes.get(txid, None)
        self.lock.reader_release()
        return item

    # PurgeSigHashes removes all partial sighashes from the HashCache belonging to
    # the passed transaction.
    def purge_sig_hashes(self, txid: chainhash.Hash):
        self.lock.reader_acquire()
        self.sig_hashes.pop(txid, None)
        self.lock.reader_release()
        return
