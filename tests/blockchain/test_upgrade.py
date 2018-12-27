import unittest
from blockchain.upgrade import *
from tests.utils import hex_to_bytes


def check_entries_equal(entries1: dict, entries2: dict) -> bool:
    # Make sure length is same
    if len(entries1) != len(entries2):
        return False

    # Make sure keys are same
    if set(entries1) != set(entries2):
        return False

    # Make sure values are same of same key
    for key in entries1.keys():
        if entries1[key] != entries2[key]:
            return False

    return True


class TestUpgrade(unittest.TestCase):
    def test_deserialize_utxo_entry_v0(self):
        tests = [
            # From tx in main blockchain:
            # 0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098
            {
                "name": "Only output 0, coinbase",
                "entries": {
                    0: UtxoEntry(
                        amount=5000000000,
                        pk_script=hex_to_bytes(
                            "410496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52da7589379515d4e0a604f8141781e62294721166bf621e73a82cbf2342c858eeac"),
                        block_height=1,
                        packed_flags=tfCoinBase
                    )
                },
                "serialized": hex_to_bytes("010103320496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52")
            },

            # From tx in main blockchain:
            # 8131ffb0a2c945ecaf9b9063e59558784f9c3a74741ce6ae2a18d0571dac15bb
            {
                "name": "Only output 1, not coinbase",
                "entries": {
                    1: UtxoEntry(
                        amount=1000000,
                        pk_script=hex_to_bytes(
                            "76a914ee8bd501094a7d5ca318da2506de35e1cb025ddc88ac"),
                        block_height=100001,
                        packed_flags=TxoFlags(0)
                    )
                },
                "serialized": hex_to_bytes("01858c21040700ee8bd501094a7d5ca318da2506de35e1cb025ddc")
            },

            # Adapted from tx in main blockchain:
            # df3f3f442d9699857f7f49de4ff0b5d0f3448bec31cdc7b5bf6d25f2abd637d5
            {
                "name": "outputs 0 and 2 not coinbase",
                "entries": {
                    0: UtxoEntry(
                        amount=20000000,
                        pk_script=hex_to_bytes(
                            "76a914e2ccd6ec7c6e2e581349c77e067385fa8236bf8a88ac"),
                        block_height=113931,
                        packed_flags=TxoFlags(0)
                    ),

                    2: UtxoEntry(
                        amount=15000000,
                        pk_script=hex_to_bytes(
                            "76a914b8025be1b3efc63b0ad48e7f9f10e87544528d5888ac"),
                        block_height=113931,
                        packed_flags=TxoFlags(0)
                    ),

                },
                "serialized": hex_to_bytes(
                    "0185f90b0a011200e2ccd6ec7c6e2e581349c77e067385fa8236bf8a800900b8025be1b3efc63b0ad48e7f9f10e87544528d58")
            },

            # Adapted from tx in main blockchain:
            # 1b02d1c8cfef60a189017b9a420c682cf4a0028175f2f563209e4ff61c8c3620
            {
                "name": "Only output 22, not coinbase",
                "entries": {
                    22: UtxoEntry(
                        amount=366875659,
                        pk_script=hex_to_bytes(
                            "a9141dd46a006572d820e448e12d2bbb38640bc718e687"),
                        block_height=338156,
                        packed_flags=TxoFlags(0)
                    ),

                },
                "serialized": hex_to_bytes(
                    "0193d06c100000108ba5b9e763011dd46a006572d820e448e12d2bbb38640bc718e6")
            },

        ]
        for test in tests:
            # Deserialize to map of utxos keyed by the output index.
            entries = deserialize_utxo_entry_v0(test['serialized'])

            # Ensure the deserialized entry has the same properties as the
            # ones in the test entry.
            self.assertTrue(check_entries_equal(entries, test['entries']))
