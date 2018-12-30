import unittest
import btcutil
from blockchain.chain import *
from tests.blockchain.common import *


class TestChain(unittest.TestCase):

    # TestHaveBlock tests the HaveBlock API to ensure proper functionality.
    def test_have_block(self):
        # Load up blocks such that there is a side chain.
        # (genesis block) -> 1 -> 2 -> 3 -> 4
        #                          \-> 3a
        test_files = ["blk_0_to_4.dat.bz2", "blk_3A.dat.bz2"]

        blocks = []

        # Load init blocks from files
        for file in test_files:
            block_tmp = load_blocks(file)

            blocks.extend(block_tmp)

        # Create a new database and chain instance to run tests against.
        chain, teardown_func = chain_setup("haveblock", chaincfg.MainNetParams)

        try:
            # Since we're not dealing with the real block chain, set the coinbase
            # maturity to 1.
            chain.chain_params.coinbase_maturity = 1

            for block in blocks[1:]:
                _, is_orphan = chain.process_block_no_exception(block, BFNone)

                self.assertFalse(is_orphan)

            # Insert an orphan block.
            _, is_orphan = chain.process_block_no_exception(btcutil.Block(Block100000), BFNone)
            self.assertTrue(is_orphan)

            # Now we prepare the env
            tests = [
                # Genesis block should be present (in the main chain).
                {"hash": chaincfg.MainNetParams.genesis_hash.to_str(), "want": True},

                # Block 3a should be present (on a side chain).
                {"hash": "00000000474284d20067a4d33f6a02284e6ef70764a3a26d6a5b9df52ef663dd", "want": True},

                # Block 100000 should be present (as an orphan).
                {"hash": "000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506", "want": True},

                # Random hashes should not be available.
                {"hash": "123", "want": False},

            ]
            for test in tests:
                block_hash = chainhash.Hash(test['hash'])
                result = chain.have_block(block_hash)
                self.assertEqual(result, test['want'])
        finally:
            teardown_func()
