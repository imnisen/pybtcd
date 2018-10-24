import unittest
from blockchain.median_time import *
import blockchain.median_time


class TestMedianTime(unittest.TestCase):
    def test_median_time(self):
        tests = [
            # # Not enough samples must result in an offset of 0.
            # {"in": [1], "wantOffset": 0, "useDupID": False},
            # {"in": [1, 2], "wantOffset": 0, "useDupID": False},
            # {"in": [1, 2, 3], "wantOffset": 0, "useDupID": False},
            # {"in": [1, 2, 3, 4], "wantOffset": 0, "useDupID": False},
            #
            # # Various number of entries.  The expected offset is only
            # # updated on odd number of elements.
            # {"in": [-13, 57, -4, -23, -12], "wantOffset": -12, "useDupID": False},
            # {"in": [55, -13, 61, -52, 39, 55], "wantOffset": 39, "useDupID": False},
            # {"in": [-62, -58, -30, -62, 51, -30, 15], "wantOffset": -30, "useDupID": False},
            # {"in": [29, -47, 39, 54, 42, 41, 8, -33], "wantOffset": 39, "useDupID": False},
            # {"in": [37, 54, 9, -21, -56, -36, 5, -11, -39], "wantOffset": -11, "useDupID": False},
            # {"in": [57, -28, 25, -39, 9, 63, -16, 19, -60, 25], "wantOffset": 9, "useDupID": False},
            # {"in": [-5, -4, -3, -2, -1], "wantOffset": -3, "useDupID": True}, # TODO
            #
            # # # The offset stops being updated once the max number of entries
            # # # has been reached.  This is actually a bug from Bitcoin Core,
            # # # but since the time is ultimately used as a part of the
            # # # consensus rules, it must be mirrored.
            # # {"in": [-67, 67, -50, 24, 63, 17, 58, -14, 5, -32, -52], "wantOffset": 17, "useDupID": False},
            # # {"in": [-67, 67, -50, 24, 63, 17, 58, -14, 5, -32, -52, 45], "wantOffset": 17, "useDupID": False},
            # # {"in": [-67, 67, -50, 24, 63, 17, 58, -14, 5, -32, -52, 45, 4], "wantOffset": 17, "useDupID": False},

        ]

        # Modify the max number of allowed median time entries for these tests.
        blockchain.median_time.maxMedianTimeEntries = 10
        for test in tests:
            filter = MedianTime()
            for j, offset in enumerate(test['in']):
                source_id = str(j)
                now = int(time.time())
                tOffset = now + offset
                filter.add_time_sample(source_id, tOffset)

                if test['useDupID']:
                    tOffset -= offset
                    filter.add_time_sample(source_id, tOffset)

            # Since it is possible that the time.Now call in AddTimeSample
            # and the time.Now calls here in the tests will be off by one
            # second, allow a fudge factor to compensate.
            gotOffset = filter.offset()
            wantOffset = test['wantOffset']
            wantOffset2 = test['wantOffset'] - 1
            self.assertIn(gotOffset, (wantOffset, wantOffset2))

            adjustedTime = filter.adjusted_time()
            now = int(time.time())
            wantTime = now + filter.offset()
            wantTime2 = now + filter.offset() - 1
            self.assertIn(adjustedTime, (wantTime, wantTime2))

        # Reset the modify of constant
        blockchain.median_time.maxMedianTimeEntries = 200