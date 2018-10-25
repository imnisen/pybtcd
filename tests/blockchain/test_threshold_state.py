import unittest
from blockchain.threshold_state import *


class TestThresholdState(unittest.TestCase):
    def test_str(self):
        # TOADD parallel

        tests = [
            {"in": ThresholdState.ThresholdDefined, "want": "ThresholdDefined"},
            {"in": ThresholdState.ThresholdStarted, "want": "ThresholdStarted"},
            {"in": ThresholdState.ThresholdLockedIn, "want": "ThresholdLockedIn"},
            {"in": ThresholdState.ThresholdActive, "want": "ThresholdActive"},
            {"in": ThresholdState.ThresholdFailed, "want": "ThresholdFailed"},
        ]

        self.assertEqual(len(tests), ThresholdState.numThresholdsStates.value)

        for test in tests:
            self.assertEqual(str(test['in']), test['want'])

    def test_cache(self):
        # TOADD parallel
        tests = [
            {
                "name": "2 entries defined",
                "numEntries": 2,
                "state": ThresholdState.ThresholdDefined
            },

            {
                "name": "7 entries defined",
                "numEntries": 7,
                "state": ThresholdState.ThresholdStarted
            },

            {
                "name": "10 entries defined",
                "numEntries": 10,
                "state": ThresholdState.ThresholdActive
            },

            {
                "name": "5 entries defined",
                "numEntries": 5,
                "state": ThresholdState.ThresholdLockedIn
            },

            {
                "name": "3 entries defined",
                "numEntries": 3,
                "state": ThresholdState.ThresholdFailed
            },

        ]

        for test in tests:
            cache = new_threshold_caches(num_caches=1)[0]
            for i in range(test['numEntries']):
                hash = chainhash.Hash(bytes([i + 1]) + bytes([0]) * (chainhash.HashSize - 1))

                # Ensure the hash isn't available in the cache already.
                self.assertIsNone(cache.look_up(hash))

                # Ensure hash that was added to the cache reports it's
                # available and the state is the expected value.
                cache.update(hash, test['state'])
                self.assertEqual(cache.look_up(hash), test['state'])

                # Ensure adding an existing hash with the same state
                # doesn't break the existing entry.
                cache.update(hash, test['state'])
                self.assertEqual(cache.look_up(hash), test['state'])

                # Ensure adding an existing hash with a different state
                # updates the existing entry.
                newState = ThresholdState.ThresholdFailed
                if newState == test['state']:
                    newState = ThresholdState.ThresholdStarted

                cache.update(hash, newState)
                self.assertEqual(cache.look_up(hash), newState)
