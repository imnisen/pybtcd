from .script import *
from .read_write_lock import RWLock


# TxSigHashes houses the partial set of sighashes introduced within BIP0143.
# This partial set of sighashes may be re-used within each input across a
# transaction when validating all inputs. As a result, validation complexity
# for SigHashAll can be reduced by a polynomial factor.
class TxSigHashes:
    def __init__(self, hash_prev_outs, hash_sequence, hash_outputs):
        """

        :param chainhash.Hash hash_prev_outs:
        :param chainhash.Hash hash_sequence:
        :param chainhash.Hash hash_outputs:
        """

        self.hash_prev_outs = hash_prev_outs
        self.hash_sequence = hash_sequence
        self.hash_outputs = hash_outputs

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
    def __init__(self, sig_hashes, lock=None):
        """

        :param dict{Hash->TxSigHashes} sig_hashes:
        :param RWLock lock:
        """
        self.sig_hashes = sig_hashes or {}
        self.lock = lock or RWLock()

    # AddSigHashes computes, then adds the partial sighashes for the passed
    # transaction.
    def add_sig_hashes(self, tx: MsgTx):
        self.lock.writer_acquire()
        self.sig_hashes[tx.tx_hash()] = TxSigHashes.from_msg_tx(tx)
        self.lock.writer_release()
        return

    # ContainsHashes returns true if the partial sighashes for the passed
    # transaction currently exist within the HashCache, and false otherwise.
    def contain_hashes(self, txid: Hash):
        self.lock.reader_acquire()
        found = txid in self.sig_hashes
        self.lock.reader_release()
        return found

    # GetSigHashes possibly returns the previously cached partial sighashes for
    # the passed transaction. This function also returns an additional boolean
    # value indicating if the sighashes for the passed transaction were found to
    # be present within the HashCache.
    def get_sig_hashes(self, txid: Hash):
        self.lock.reader_acquire()
        item = self.sig_hashes.get(txid, None)
        self.lock.reader_release()
        return item

    # PurgeSigHashes removes all partial sighashes from the HashCache belonging to
    # the passed transaction.
    def purge_sig_hashes(self, txid: Hash):
        self.lock.reader_acquire()
        self.sig_hashes.pop(txid, None)
        self.lock.reader_release()
        return
