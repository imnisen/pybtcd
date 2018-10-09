import unittest
import random
import os
from wire.msg_tx import OutPoint, TxIn, TxOut
from txscript.hash_cache import *
from txscript.constant import *


def get_random_tx():
    tx = MsgTx()

    # make num_tx_ins tx_ins
    num_tx_ins = random.randrange(0, 11)
    for _ in range(num_tx_ins):
        tx_in = TxIn(
            previous_out_point=OutPoint(
                hash=Hash(data=os.urandom(HashSize)),
                index=random.randrange(0, MaxInt32)
            ),
            sequence=random.randrange(0, MaxInt32)
        )
        tx.add_tx_in(tx_in)

    # make num_yx_outs tx_outs
    num_tx_outs = random.randrange(0, 11)
    for _ in range(num_tx_outs):
        tx_out = TxOut(
            value=random.randrange(0, MaxInt32),
            pk_script=os.urandom(30)
        )
        tx.add_tx_out(tx_out)

    return tx


class TestHashCache(unittest.TestCase):
    def test_add_contains(self):
        # TOADD TODO make the test run parallel?

        hash_cache = HashCache()

        # Add random tx to hash_cache
        random_txs = []
        for _ in range(10):
            random_tx = get_random_tx()
            random_txs.append(random_tx)
            hash_cache.add_sig_hashes(random_tx)

        # check contains
        for tx in random_txs:
            self.assertTrue(hash_cache.contain_hashes(tx.tx_hash()))

    def test_add_get(self):
        # TOADD TODO make the test run parallel?

        hash_cache = HashCache()

        # Add tx to hash_cache
        # random_txs = []
        # for _ in range(10):
        random_tx = get_random_tx()
        # random_txs.append(random_tx)
        hash_cache.add_sig_hashes(random_tx)

        # check get
        cache_tx = hash_cache.get_sig_hashes(random_tx.tx_hash())

        sign_hashes = TxSigHashes.from_msg_tx(random_tx)

        self.assertEqual(cache_tx, sign_hashes)

    def test_purge_contains(self):
        # TOADD TODO make the test run parallel?

        hash_cache = HashCache()

        # Add random tx to hash_cache
        random_txs = []
        for _ in range(10):
            random_tx = get_random_tx()
            random_txs.append(random_tx)
            hash_cache.add_sig_hashes(random_tx)

        # check contains
        for tx in random_txs:
            self.assertTrue(hash_cache.contain_hashes(tx.tx_hash()))

        # purge txs
        for tx in random_txs:
            hash_cache.purge_sig_hashes(tx.tx_hash())

        # check not cotaions
        for tx in random_txs:
            self.assertFalse(hash_cache.contain_hashes(tx.tx_hash()))
