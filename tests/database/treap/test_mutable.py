import unittest
from database.treap.mutable import *
from pyutil import sha256


def uint32_to_bytes(i):
    return i.to_bytes(4, "big")


class TestMutable(unittest.TestCase):
    def test_mutable_empty(self):
        # TOADD parallel

        treap = Mutable()
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

    def test_mutable_reset(self):
        # TOADD parallel

        numItems = 10
        testTreap = Mutable()

        for i in range(numItems):
            key = uint32_to_bytes(i)
            testTreap.put(key, key)

        testTreap.reset()

        self.assertEqual(testTreap.len(), 0)
        self.assertEqual(testTreap.size(), 0)

        for i in range(numItems):
            key = uint32_to_bytes(i)
            self.assertFalse(testTreap.has(key))
            self.assertIsNone(testTreap.get(key))

        num_iterated = 0
        for key, value in testTreap.for_each2():
            num_iterated += 1
        self.assertEqual(num_iterated, 0)

    def test_mutable_sequential(self):
        # TOADD parallel

        expectedSize = 0
        numItems = 1000
        testTreap = Mutable()
        for i in range(numItems):
            key = uint32_to_bytes(i)
            testTreap.put(key, key)
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
            testTreap.delete(key)

            self.assertEqual(testTreap.len(), numItems - i - 1)
            self.assertFalse(testTreap.has(key))
            expectedSize -= (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_mutable_reverse_sequential(self):
        expectedSize = 0
        numItems = 1000
        testTreap = Mutable()
        for i in range(numItems):
            key = uint32_to_bytes(numItems - i - 1)
            testTreap.put(key, key)
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
            testTreap.delete(key)

            self.assertEqual(testTreap.len(), numItems - i - 1)
            self.assertFalse(testTreap.has(key))
            expectedSize -= (nodeFieldsSize + 8)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_mutable_unordered(self):
        # TOADD parallel

        expectedSize = 0
        numItems = 1000
        testTreap = Mutable()
        for i in range(numItems):
            key = sha256(uint32_to_bytes(i))
            testTreap.put(key, key)
            self.assertEqual(testTreap.len(), i + 1)
            self.assertTrue(testTreap.has(key))
            self.assertEqual(testTreap.get(key), key)
            expectedSize += (nodeFieldsSize + len(key) * 2)
            self.assertEqual(testTreap.size(), expectedSize)

        for i in range(numItems):
            key = sha256(uint32_to_bytes(i))
            testTreap.delete(key)

            self.assertEqual(testTreap.len(), numItems - i - 1)
            self.assertFalse(testTreap.has(key))
            expectedSize -= (nodeFieldsSize + 64)
            self.assertEqual(testTreap.size(), expectedSize)

    def test_mutable_duplicate_put(self):
        # TOADD parallel

        key = uint32_to_bytes(0)
        val = b"testval"

        testTreap = Mutable()
        testTreap.put(key, key)
        testTreap.put(key, val)

        self.assertTrue(testTreap.has(key))
        self.assertEqual(testTreap.get(key), val)

        expectedSize = nodeFieldsSize + len(key) + len(val)
        self.assertEqual(testTreap.size(), expectedSize)

    def test_mutable_null_value(self):
        key = sha256(uint32_to_bytes(0))
        val = None

        testTreap = Mutable()
        testTreap.put(key, val)
        self.assertTrue(testTreap.has(key))
        expectedVal = bytes()
        self.assertEqual(testTreap.get(key), expectedVal)
        self.assertEqual(len(testTreap.get(key)), 0)
