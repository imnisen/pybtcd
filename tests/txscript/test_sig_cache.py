import unittest
import hashlib
import copy
import chainhash
from txscript.sig_cache import *
import btcec


def gen_random_sig():
    msg_hash = chainhash.Hash(secrets.token_bytes(chainhash.HashSize))
    private_key = btcec.SigningKey.generate(curve=btcec.SECP256k1)

    sig = private_key.sign(data=msg_hash.to_bytes(), hashfunc=hashlib.sha256)  # TODO need hashfunc ?

    pub_key = private_key.get_verifying_key()

    return msg_hash, sig, pub_key


def copy_signature(sig):
    return copy.deepcopy(sig)


def copy_private_key():
    pass


def copy_public_key(key):
    key_string = key.to_string()
    return btcec.PublicKey.from_string(key_string, curve=btcec.SECP256k1)  # TODO need hashfunc ?


# def gen_random_sig2():
#     msg_hash = secrets.token_bytes(32)
#     private_key = SigningKey.generate(curve=SECP256k1)
#
#     sig = private_key.sign(data=msg_hash, hashfunc=hashlib.sha256)  # TODO need hashfunc ?
#
#     pub_key = private_key.get_verifying_key()
#
#     return msg_hash, sig, pub_key

class TestSigCache(unittest.TestCase):
    def test_add_exists(self):
        sig_cache = SigCache(max_entries=200)
        msg1, sig1, key1 = gen_random_sig()
        sig_cache.add(msg1, sig1, key1)
        sig1_copy = copy_signature(sig1)
        key1_copy = copy_public_key(key1)

        self.assertTrue(sig_cache.exists(msg1, sig1_copy, key1_copy))

    def test_add_exists_max_entries(self):
        sig_cache_size = 5
        sig_cache = SigCache(max_entries=sig_cache_size)

        for _ in range(sig_cache_size):
            msg1, sig1, key1 = gen_random_sig()
            sig_cache.add(msg1, sig1, key1)
            sig1_copy = copy_signature(sig1)
            key1_copy = copy_public_key(key1)

            self.assertTrue(sig_cache.exists(msg1, sig1_copy, key1_copy))

        self.assertEqual(len(sig_cache.valid_sigs), sig_cache_size)

        msg2, sig2, key2 = gen_random_sig()
        sig_cache.add(msg2, sig2, key2)

        self.assertEqual(len(sig_cache.valid_sigs), sig_cache_size)

        sig2_copy = copy_signature(sig2)
        key2_copy = copy_public_key(key2)

        self.assertTrue(sig_cache.exists(msg2, sig2_copy, key2_copy))

    def test_add_exists_zero_entries(self):
        sig_cache = SigCache(max_entries=0)
        msg1, sig1, key1 = gen_random_sig()
        sig_cache.add(msg1, sig1, key1)

        sig1_copy = copy_signature(sig1)
        key1_copy = copy_public_key(key1)

        self.assertFalse(sig_cache.exists(msg1, sig1_copy, key1_copy))
