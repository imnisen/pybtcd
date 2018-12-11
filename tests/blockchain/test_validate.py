import unittest
import chaincfg
import chainhash
import pyutil
from blockchain.validate import *
from tests.blockchain.common import *


class TestValidate(unittest.TestCase):
    # TestSequenceLocksActive tests the SequenceLockActive function to ensure it
    # works as expected in all possible combinations/scenarios.
    def test_sequence_lock_active(self):
        tests = [
            # Block based sequence lock with equal block height.
            {"seq_lock": SequenceLock(block_height=100, seconds=-1), "block_height": 1001, "mtp": 9, "want": True},

            # Time based sequence lock with mtp past the absolute time.
            {"seq_lock": SequenceLock(block_height=-1, seconds=30), "block_height": 2, "mtp": 31, "want": True},

            # Block based sequence lock with current height below seq lock block height.
            {"seq_lock": SequenceLock(block_height=1000, seconds=-1), "block_height": 90, "mtp": 9, "want": False},

            # Time based sequence lock with current time before lock time.
            {"seq_lock": SequenceLock(block_height=-1, seconds=30), "block_height": 2, "mtp": 29, "want": False},

            # Block based sequence lock at the same height, so shouldn't yet be active.
            {"seq_lock": SequenceLock(block_height=1000, seconds=-1), "block_height": 1000, "mtp": 9, "want": False},

            #  Time based sequence lock with current time equal to lock time, so shouldn't yet be active.
            {"seq_lock": SequenceLock(block_height=-1, seconds=30), "block_height": 2, "mtp": 30, "want": False},

        ]

        for test in tests:
            got = sequence_lock_active(test['seq_lock'], test['block_height'], test['mtp'])
            self.assertEqual(got, test['want'])

    #
    # TOADD test_check_connect_block_template
    #

    # TestCheckBlockSanity tests the CheckBlockSanity function to ensure it works
    # as expected.
    def test_check_block_sanity(self):
        pow_limit = chaincfg.MainNetParams.pow_limit
        block = btcutil.Block(msg_block=Block100000)
        time_source = MedianTime()
        check_block_sanity(block, pow_limit, time_source)

        # Ensure a block that has a timestamp with a precision higher than one
        # second fails.
        timestamp = block.get_msg_block().header.timestamp
        block.get_msg_block().header.timestamp = timestamp + 1
        with self.assertRaises(RuleError):
            check_block_sanity(block, pow_limit, time_source)

    # TestCheckSerializedHeight tests the checkSerializedHeight function with
    # various serialized heights and also does negative tests to ensure errors
    # and handled properly.
    def test_check_serialized_height(self):
        # Create an empty coinbase template to be used in the tests below.
        coinbase_outpoint = wire.OutPoint(chainhash.Hash(), pyutil.MaxUint32)
        coinbase_tx = wire.MsgTx(version=1)
        coinbase_tx.add_tx_in(wire.TxIn(previous_out_point=coinbase_outpoint))

        # Expected rule errors
        missing_height_error = RuleError(ErrorCode.ErrMissingCoinbaseHeight)
        bad_height_error = RuleError(ErrorCode.ErrBadCoinbaseHeight)

        tests = [
            # No serialized height length.
            {"sig_script": bytes(), "want_height": 0, "err": missing_height_error},

            # Serialized height length with no height bytes.
            {"sig_script": bytes([0x02]), "want_height": 0, "err": missing_height_error},

            # Serialized height length with too few height bytes.
            {"sig_script": bytes([0x02, 0x4a]), "want_height": 0, "err": missing_height_error},

            # Serialized height that needs 2 bytes to encode.
            {"sig_script": bytes([0x02, 0x4a, 0x52]), "want_height": 21066, "err": None},

            # Serialized height that needs 2 bytes to encode, but backwards endianness.
            {"sig_script": bytes([0x02, 0x4a, 0x52]), "want_height": 19026, "err": bad_height_error},

            # Serialized height that needs 3 bytes to encode.
            {"sig_script": bytes([0x03, 0x40, 0x0d, 0x03]), "want_height": 200000, "err": None},

            # Serialized height that needs 3 bytes to encode, but backwards endianness.
            {"sig_script": bytes([0x03, 0x40, 0x0d, 0x03]), "want_height": 1074594560, "err": bad_height_error},

        ]

        for test in tests:
            msg_tx = coinbase_tx.copy()
            msg_tx.tx_ins[0].signature_script = test['sig_script']
            tx = btcutil.Tx(msg_tx)

            if test['err']:
                with self.assertRaises(RuleError) as cm:
                    check_serialized_height(tx, test['want_height'])
                self.assertEqual(cm.exception.c, test['err'].c)

            else:
                check_serialized_height(tx, test['want_height'])
