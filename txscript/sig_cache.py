import secrets
from .read_write_lock import RWLock


# sigCacheEntry represents an entry in the SigCache. Entries within the
# SigCache are keyed according to the sigHash of the signature. In the
# scenario of a cache-hit (according to the sigHash), an additional comparison
# of the signature, and public key will be executed in order to ensure a complete
# match. In the occasion that two sigHashes collide, the newer sigHash will
# simply overwrite the existing entry.
class SigCacheEntry:
    def __init__(self, sig, pub_key):
        """

        :param Sig sig:
        :param PublicKey pub_key:
        """

        self.sig = sig
        self.pub_key = pub_key


# SigCache implements an ECDSA signature verification cache with a randomized
# entry eviction policy. Only valid signatures will be added to the cache. The
# benefits of SigCache are two fold. Firstly, usage of SigCache mitigates a DoS
# attack wherein an attack causes a victim's client to hang due to worst-case
# behavior triggered while processing attacker crafted invalid transactions. A
# detailed description of the mitigated DoS attack can be found here:
# https://bitslog.wordpress.com/2013/01/23/fixed-bitcoin-vulnerability-explanation-why-the-signature-cache-is-a-dos-protection/.
# Secondly, usage of the SigCache introduces a signature verification
# optimization which speeds up the validation of transactions within a block,
# if they've already been seen and verified within the mempool.
class SigCache:
    def __init__(self, valid_sigs=None, max_entries=None, lock=None):
        """

        :param dict{Hash->SigCacheEntry} valid_sigs:
        :param uint max_entries:
        :param RWLock lock:
        """
        self.valid_sigs = valid_sigs or {}
        self.max_entries = max_entries or 0
        self.lock = lock or RWLock()

    # Exists returns true if an existing entry of 'sig' over 'sigHash' for public
    # key 'pubKey' is found within the SigCache. Otherwise, false is returned.
    #
    # NOTE: This function is safe for concurrent access. Readers won't be blocked
    # unless there exists a writer, adding an entry to the SigCache.
    def exists(self, sig_hash, sig, pub_key):
        """

        :param sig_hash:
        :param sig:
        :param pub_key:
        :return:
        """
        self.lock.reader_acquire()
        entry = self.valid_sigs.get(sig_hash)
        self.lock.reader_release()
        if entry:
            return entry.pub_key == pub_key and entry.sig == sig
        else:
            return False

    # Add adds an entry for a signature over 'sigHash' under public key 'pubKey'
    # to the signature cache. In the event that the SigCache is 'full', an
    # existing entry is randomly chosen to be evicted in order to make space for
    # the new entry.
    #
    # NOTE: This function is safe for concurrent access. Writers will block
    # simultaneous readers until function execution has concluded.
    def add(self, sig_hash, sig, pub_key):
        self.lock.writer_acquire()

        if self.max_entries <= 0:
            self.lock.writer_release()
            return

        if len(self.valid_sigs) + 1 > self.max_entries:
            # Below is from origin
            # Remove a random entry from the map. Relying on the random
            # starting point of Go's map iteration. It's worth noting that
            # the random iteration starting point is not 100% guaranteed
            # by the spec, however most Go compilers support it.
            # Ultimately, the iteration order isn't important here because
            # in order to manipulate which items are evicted, an adversary
            # would need to be able to execute preimage attacks on the
            # hashing function in order to start eviction at a specific
            # entry.
            # But here we use random
            self.valid_sigs.pop(secrets.choice(list(self.valid_sigs.keys())))

        self.valid_sigs[sig_hash] = SigCacheEntry(sig=sig, pub_key=pub_key)

        self.lock.writer_release()
        return
