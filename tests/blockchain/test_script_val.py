import unittest
from blockchain.script_val import *
from tests.blockchain.common import *
import txscript


class TestScriptVal(unittest.TestCase):
    def test_check_block_scripts(self):
        test_block_num = 277647
        block_data_file = "%d.dat.bz2" % test_block_num
        blocks = load_blocks(block_data_file)

        self.assertTrue(len(blocks) == 1)

        store_data_file = "%d.utxostore.bz2" % test_block_num
        view = load_utxo_view(store_data_file)

        script_flags = txscript.ScriptFlags(txscript.ScriptFlag.ScriptBip16)
        check_block_scripts(blocks[0], view, script_flags, sig_cache=None, hash_cache=None)
