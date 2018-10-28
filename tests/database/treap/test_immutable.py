import unittest
from database.treap.immutable import *
from pyutil import sha256


def uint32_to_bytes(i):
    return i.to_bytes(4, "big")


class TestImmutable(unittest.TestCase):
    def test_immutable_empty(self):
        # TOADD parallel

        treap = Immutable()
        self.assertEqual(treap.len(), 0)
        self.assertEqual(treap.size(), 0)

        key = uint32_to_bytes(0)
        self.assertFalse(treap.has(key))

        self.assertIsNone(treap.get(key))

        treap.delete(key)

        num_iterated = 0
        for key, value in treap.for_each2():
            num_iterated += 1
        self.assertEqual(num_iterated, 0)

    def test_immutable_sequential(self):
        # TOADD parallel

        expectedSize = 0
        numItems = 1000
        testTreap = Immutable()
        for i in range(numItems):
            key = uint32_to_bytes(i)
            testTreap = testTreap.put(key, key)
            self.assertEqual(testTreap.len(), i + 1)
            self.assertTrue(testTreap.has(key))
            self.assertEqual(testTreap.get(key), key)
            expectedSize += (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

        numIterated = 0
        for key, value in testTreap.for_each2():
            want_key = uint32_to_bytes(numIterated)
            self.assertEqual(key, want_key)
            self.assertEqual(value, want_key)
            numIterated += 1

        self.assertEqual(numIterated, numItems)

        for i in range(numItems):
            key = uint32_to_bytes(i)
            testTreap = testTreap.delete(key)

            self.assertEqual(testTreap.len(), numItems - i - 1)
            self.assertFalse(testTreap.has(key))
            expectedSize -= (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_immutable_reverse_sequential(self):
        expectedSize = 0
        numItems = 1000
        testTreap = Immutable()
        for i in range(numItems):
            key = uint32_to_bytes(numItems - i - 1)
            testTreap = testTreap.put(key, key)
            self.assertEqual(testTreap.len(), i + 1)
            self.assertTrue(testTreap.has(key))
            self.assertEqual(testTreap.get(key), key)
            expectedSize += (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

        numIterated = 0
        for key, value in testTreap.for_each2():
            want_key = uint32_to_bytes(numIterated)
            self.assertEqual(key, want_key)
            self.assertEqual(value, want_key)
            numIterated += 1

        self.assertEqual(numIterated, numItems)

        for i in range(numItems):
            key = uint32_to_bytes(i)
            testTreap = testTreap.delete(key)

            self.assertEqual(testTreap.len(), numItems - i - 1)
            self.assertFalse(testTreap.has(key))
            expectedSize -= (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_immutable_unordered(self):
        # TOADD parallel

        expectedSize = 0
        numItems = 1000
        testTreap = Immutable()
        for i in range(numItems):
            key = sha256(uint32_to_bytes(i))
            testTreap = testTreap.put(key, key)
            self.assertEqual(testTreap.len(), i + 1)
            self.assertTrue(testTreap.has(key))
            self.assertEqual(testTreap.get(key), key)
            expectedSize += (nodeFieldsSize + len(key) * 2)
            self.assertEqual(testTreap.size(), expectedSize)

        for i in range(numItems):
            key = sha256(uint32_to_bytes(i))
            testTreap = testTreap.delete(key)

            self.assertEqual(testTreap.len(), numItems - i - 1)
            self.assertFalse(testTreap.has(key))
            expectedSize -= (nodeFieldsSize + 64)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_immutable_duplicate_put(self):
        # TOADD parallel

        expectedVal = b"testval"
        expectedSize = 0
        numItems = 1000
        testTreap = Immutable()

        for i in range(numItems):
            key = uint32_to_bytes(i)
            testTreap = testTreap.put(key, key)
            expectedSize += (nodeFieldsSize + len(key) + len(key))

            testTreap = testTreap.put(key, expectedVal)
            self.assertTrue(testTreap.has(key))
            self.assertEqual(testTreap.get(key), expectedVal)

            expectedSize -= len(key)
            expectedSize += len(expectedVal)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_immutable_null_value(self):
        key = uint32_to_bytes(0)
        val = None

        testTreap = Immutable()
        testTreap = testTreap.put(key, val)
        self.assertTrue(testTreap.has(key))
        expectedVal = bytes()
        self.assertEqual(testTreap.get(key), expectedVal)
        self.assertEqual(len(testTreap.get(key)), 0)

    def test_immutable_snapshot(self):
        # TOADD parallel

        expectedSize = 0
        numItems = 1000
        testTreap = Immutable()
        for i in range(numItems):
            treapSnap = testTreap
            key = uint32_to_bytes(i)
            testTreap = testTreap.put(key, key)

            self.assertEqual(treapSnap.len(), i)
            self.assertEqual(testTreap.len(), i + 1)

            self.assertFalse(treapSnap.has(key))
            self.assertTrue(testTreap.has(key))

            self.assertIsNone(treapSnap.get(key))
            self.assertEqual(testTreap.get(key), key)

            self.assertEqual(treapSnap.size(), expectedSize)
            expectedSize += (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

        for i in range(numItems):
            treapSnap = testTreap

            key = uint32_to_bytes(i)
            testTreap = testTreap.delete(key)

            self.assertEqual(treapSnap.len(), numItems - i)
            self.assertEqual(testTreap.len(), numItems - i - 1)

            self.assertTrue(treapSnap.has(key))
            self.assertFalse(testTreap.has(key))

            self.assertEqual(treapSnap.get(key), key)
            self.assertIsNone(testTreap.get(key))

            self.assertEqual(treapSnap.size(), expectedSize)
            expectedSize -= (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)
