import unittest
from database.treap.treapiter import *
from database.treap.mutable import *
from database.treap.immutable import *


def uint32_to_bytes(i):
    return i.to_bytes(4, "big")


def bytes_to_uint32(b):
    return int.from_bytes(b, "big")


class TestIterator(unittest.TestCase):
    def test_mutable_iterator(self):
        # TOADD parallel

        tests = [

            # No range limits.  Values are the set (0, 1, 2, ..., 49).
            # Seek existing value.
            {
                "numKeys": 50,
                "step": 1,
                "startKey": None,
                "limitKey": None,
                "expectedFirst": uint32_to_bytes(0),
                "expectedLast": uint32_to_bytes(49),
                "seekKey": uint32_to_bytes(12),
                "expectedSeek": uint32_to_bytes(12),
            },

            # Limited to range [24, end].  Values are the set
            # (0, 2, 4, ..., 48).  Seek value that doesn't exist and is
            # greater than largest existing key.
            {
                "numKeys": 50,
                "step": 2,
                "startKey": uint32_to_bytes(24),
                "limitKey": None,
                "expectedFirst": uint32_to_bytes(24),
                "expectedLast": uint32_to_bytes(48),
                "seekKey": uint32_to_bytes(49),
                "expectedSeek": None,
            },

            # Limited to range [start, 25).  Values are the set
            # (0, 3, 6, ..., 48).  Seek value that doesn't exist but is
            # before an existing value within the range.
            {
                "numKeys": 50,
                "step": 3,
                "startKey": None,
                "limitKey": uint32_to_bytes(25),
                "expectedFirst": uint32_to_bytes(0),
                "expectedLast": uint32_to_bytes(24),
                "seekKey": uint32_to_bytes(17),
                "expectedSeek": uint32_to_bytes(18),
            },

            # Limited to range [10, 21).  Values are the set
            # (0, 4, ..., 48).  Seek value that exists, but is before the
            # minimum allowed range.
            {
                "numKeys": 50,
                "step": 4,
                "startKey": uint32_to_bytes(10),
                "limitKey": uint32_to_bytes(21),
                "expectedFirst": uint32_to_bytes(12),
                "expectedLast": uint32_to_bytes(20),
                "seekKey": uint32_to_bytes(4),
                "expectedSeek": None,
            },

            # Limited by prefix {0,0,0}, range [{0,0,0}, {0,0,1}).
            # Since it's a bytewise compare,  {0,0,0,...} < {0,0,1}.
            # Seek existing value within the allowed range.
            {
                "numKeys": 300,
                "step": 1,
                "startKey": bytes([0x00, 0x00, 0x00]),
                "limitKey": bytes([0x00, 0x00, 0x01]),
                "expectedFirst": uint32_to_bytes(0),
                "expectedLast": uint32_to_bytes(255),
                "seekKey": uint32_to_bytes(100),
                "expectedSeek": uint32_to_bytes(100),
            },

        ]

        for test in tests:
            testTreap = Mutable()

            # Insert a bunch of keys.
            for i in range(0, test['numKeys'], test['step']):
                key = uint32_to_bytes(i)
                testTreap.put(key, key)

            # Create new iterator limited by the test params.
            iter = testTreap.iterator(test['startKey'], test['limitKey'])

            # Ensure the first item is accurate.
            has_first = iter.first()
            if test['expectedFirst']:
                self.assertTrue(has_first)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedFirst'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedFirst'])

            # Ensure the iterator gives the expected items in order.
            curNum = bytes_to_uint32(test['expectedFirst'])
            while iter.next():
                curNum += test['step']

                # Ensure key is as expected.
                gotKey = iter.key()
                expectedKey = uint32_to_bytes(curNum)
                self.assertEqual(gotKey, expectedKey)

                gotVal = iter.value()
                self.assertEqual(gotVal, expectedKey)

            # Ensure iterator is exhausted.
            self.assertFalse(iter.valid())

            # Ensure the last item is accurate.
            hasLast = iter.last()
            if test['expectedLast']:
                self.assertTrue(hasLast)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedLast'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedLast'])

            # Ensure the iterator gives the expected items in reverse
            # order.
            curNum = bytes_to_uint32(test['expectedLast'])
            while iter.prev():
                curNum -= test['step']

                # Ensure key is as expected.
                gotKey = iter.key()
                expectedKey = uint32_to_bytes(curNum)
                self.assertEqual(gotKey, expectedKey)

                gotVal = iter.value()
                self.assertEqual(gotVal, expectedKey)

            # Ensure iterator is exhausted.
            self.assertFalse(iter.valid())

            # Seek to the provided key.
            seekValid = iter.seek(test['seekKey'])
            if test['expectedSeek']:
                self.assertTrue(seekValid)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedSeek'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedSeek'])

            # Recreate the iterator and ensure calling Next on it before it
            # has been positioned gives the first element.
            iter = testTreap.iterator(test['startKey'], test['limitKey'])
            hasNext = iter.next()
            if test['expectedFirst']:
                self.assertTrue(hasNext)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedFirst'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedFirst'])

            # Recreate the iterator and ensure calling Prev on it before it
            # has been positioned gives the last element.
            iter = testTreap.iterator(test['startKey'], test['limitKey'])
            hasPrev = iter.prev()
            if test['expectedLast']:
                self.assertTrue(hasPrev)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedLast'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedLast'])

    def test_mutable_empty_iterator(self):
        # TOADD parallel

        testTreap = Mutable()

        iter = testTreap.iterator(None, None)
        self.assertFalse(iter.valid())
        self.assertFalse(iter.first())
        self.assertFalse(iter.last())
        self.assertFalse(iter.next())
        self.assertFalse(iter.prev())
        self.assertIsNone(iter.key())
        self.assertIsNone(iter.value())

        # Ensure Next and Prev report exhausted after forcing a reseek on an
        # empty iterator.
        iter.force_reseek()
        self.assertFalse(iter.next())
        self.assertFalse(iter.prev())

    def test_iterator_updates(self):
        # TOADD parallel

        # Create a new treap with various values inserted in no particular
        # order.  The resulting keys are the set (2, 4, 7, 11, 18, 25).
        testTreap = Mutable()
        testTreap.put(uint32_to_bytes(7), None)
        testTreap.put(uint32_to_bytes(2), None)
        testTreap.put(uint32_to_bytes(18), None)
        testTreap.put(uint32_to_bytes(11), None)
        testTreap.put(uint32_to_bytes(25), None)
        testTreap.put(uint32_to_bytes(4), None)

        # Create an iterator against the treap with a range that excludes the
        # lowest and highest entries.  The limited set is then (4, 7, 11, 18)
        iter = testTreap.iterator(uint32_to_bytes(3), uint32_to_bytes(25))

        # Delete a key from the middle of the range and notify the iterator to
        # force a reseek.
        testTreap.delete(uint32_to_bytes(11))
        iter.force_reseek()

        # Ensure that calling Next on the iterator after the forced reseek
        # gives the expected key.  The limited set of keys at this point is
        # (4, 7, 18) and the iterator has not yet been positioned.
        self.assertTrue(iter.next())
        wantKey = uint32_to_bytes(4)
        gotKey = iter.key()
        self.assertEqual(gotKey, wantKey)

        # Delete the key the iterator is currently position at and notify the
        # iterator to force a reseek.
        testTreap.delete(uint32_to_bytes(4))
        iter.force_reseek()

        # Ensure that calling Next on the iterator after the forced reseek
        # gives the expected key.  The limited set of keys at this point is
        # (7, 18) and the iterator is positioned at a deleted entry before 7.
        self.assertTrue(iter.next())
        wantKey = uint32_to_bytes(7)
        gotKey = iter.key()
        self.assertEqual(gotKey, wantKey)

        testTreap.put(uint32_to_bytes(4), None)
        iter.force_reseek()
        self.assertTrue(iter.prev())
        wantKey = uint32_to_bytes(4)
        gotKey = iter.key()
        self.assertEqual(gotKey, wantKey)

        testTreap.delete(uint32_to_bytes(7))
        iter.force_reseek()

        # Ensure that calling Next on the iterator after the forced reseek
        # gives the expected key.  The limited set of keys at this point is
        # (7, 18) and the iterator is positioned at a deleted entry before 7.
        self.assertTrue(iter.next())
        wantKey = uint32_to_bytes(18)
        gotKey = iter.key()
        self.assertEqual(gotKey, wantKey)

    def test_immutable_iterator(self):
        # TOADD parallel
        tests = [
            # No range limits.  Values are the set (0, 1, 2, ..., 49).
            # Seek existing value.
            {
                "numKeys": 50,
                "step": 1,
                "startKey": None,
                "limitKey": None,
                "expectedFirst": uint32_to_bytes(0),
                "expectedLast": uint32_to_bytes(49),
                "seekKey": uint32_to_bytes(12),
                "expectedSeek": uint32_to_bytes(12),
            },

            # Limited to range [24, end].  Values are the set
            # (0, 2, 4, ..., 48).  Seek value that doesn't exist and is
            # greater than largest existing key.
            {
                "numKeys": 50,
                "step": 2,
                "startKey": uint32_to_bytes(24),
                "limitKey": None,
                "expectedFirst": uint32_to_bytes(24),
                "expectedLast": uint32_to_bytes(48),
                "seekKey": uint32_to_bytes(49),
                "expectedSeek": None,
            },

            # Limited to range [start, 25).  Values are the set
            # (0, 3, 6, ..., 48).  Seek value that doesn't exist but is
            # before an existing value within the range.
            {
                "numKeys": 50,
                "step": 3,
                "startKey": None,
                "limitKey": uint32_to_bytes(25),
                "expectedFirst": uint32_to_bytes(0),
                "expectedLast": uint32_to_bytes(24),
                "seekKey": uint32_to_bytes(17),
                "expectedSeek": uint32_to_bytes(18),
            },

            # Limited to range [10, 21).  Values are the set
            # (0, 4, ..., 48).  Seek value that exists, but is before the
            # minimum allowed range.
            {
                "numKeys": 50,
                "step": 4,
                "startKey": uint32_to_bytes(10),
                "limitKey": uint32_to_bytes(21),
                "expectedFirst": uint32_to_bytes(12),
                "expectedLast": uint32_to_bytes(20),
                "seekKey": uint32_to_bytes(4),
                "expectedSeek": None,
            },

            # Limited by prefix {0,0,0}, range [{0,0,0}, {0,0,1}).
            # Since it's a bytewise compare,  {0,0,0,...} < {0,0,1}.
            # Seek existing value within the allowed range.
            {
                "numKeys": 300,
                "step": 1,
                "startKey": bytes([0x00, 0x00, 0x00]),
                "limitKey": bytes([0x00, 0x00, 0x01]),
                "expectedFirst": uint32_to_bytes(0),
                "expectedLast": uint32_to_bytes(255),
                "seekKey": uint32_to_bytes(100),
                "expectedSeek": uint32_to_bytes(100),
            },
        ]

        for test in tests:
            testTreap = Immutable()

            # Insert a bunch of keys.
            for i in range(0, test['numKeys'], test['step']):
                key = uint32_to_bytes(i)
                testTreap = testTreap.put(key, key)

            # Create new iterator limited by the test params.
            iter = testTreap.iterator(test['startKey'], test['limitKey'])

            # Ensure the first item is accurate.
            has_first = iter.first()
            if test['expectedFirst']:
                self.assertTrue(has_first)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedFirst'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedFirst'])

            # Ensure the iterator gives the expected items in order.
            curNum = bytes_to_uint32(test['expectedFirst'])
            while iter.next():
                curNum += test['step']

                # Ensure key is as expected.
                gotKey = iter.key()
                expectedKey = uint32_to_bytes(curNum)
                self.assertEqual(gotKey, expectedKey)

                gotVal = iter.value()
                self.assertEqual(gotVal, expectedKey)

            # Ensure iterator is exhausted.
            self.assertFalse(iter.valid())

            # Ensure the last item is accurate.
            hasLast = iter.last()
            if test['expectedLast']:
                self.assertTrue(hasLast)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedLast'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedLast'])

            # Ensure the iterator gives the expected items in reverse
            # order.
            curNum = bytes_to_uint32(test['expectedLast'])
            while iter.prev():
                curNum -= test['step']

                # Ensure key is as expected.
                gotKey = iter.key()
                expectedKey = uint32_to_bytes(curNum)
                self.assertEqual(gotKey, expectedKey)

                gotVal = iter.value()
                self.assertEqual(gotVal, expectedKey)

            # Ensure iterator is exhausted.
            self.assertFalse(iter.valid())

            # Seek to the provided key.
            seekValid = iter.seek(test['seekKey'])
            if test['expectedSeek']:
                self.assertTrue(seekValid)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedSeek'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedSeek'])

            # Recreate the iterator and ensure calling Next on it before it
            # has been positioned gives the first element.
            iter = testTreap.iterator(test['startKey'], test['limitKey'])
            hasNext = iter.next()
            if test['expectedFirst']:
                self.assertTrue(hasNext)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedFirst'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedFirst'])

            # Recreate the iterator and ensure calling Prev on it before it
            # has been positioned gives the last element.
            iter = testTreap.iterator(test['startKey'], test['limitKey'])
            hasPrev = iter.prev()
            if test['expectedLast']:
                self.assertTrue(hasPrev)

            gotKey = iter.key()
            self.assertEqual(gotKey, test['expectedLast'])

            gotVal = iter.value()
            self.assertEqual(gotVal, test['expectedLast'])

    def test_immutable_empty_iterator(self):
        # TOADD parallel

        testTreap = Immutable()

        iter = testTreap.iterator(None, None)
        self.assertFalse(iter.valid())
        self.assertFalse(iter.first())
        self.assertFalse(iter.last())
        self.assertFalse(iter.next())
        self.assertFalse(iter.prev())
        self.assertIsNone(iter.key())
        self.assertIsNone(iter.value())

        # Ensure Next and Prev report exhausted after forcing a reseek on an
        # empty iterator.
        iter.force_reseek()
        self.assertFalse(iter.next())
        self.assertFalse(iter.prev())
