import unittest
import wire
import chainhash
import btcutil
from blockchain.merkle import *
from tests.blockchain.common import *


class TestMerkle(unittest.TestCase):
    def test_build_merkle_tree_store(self):
        block = btcutil.Block(msg_block=Block100000)
        merkles = build_merkle_tree_store(block.get_transactions(), witness=False)
        calculated_merkle_root = merkles[-1]
        want_merkle = Block100000.header.merkle_root
        self.assertEqual(calculated_merkle_root, want_merkle)
