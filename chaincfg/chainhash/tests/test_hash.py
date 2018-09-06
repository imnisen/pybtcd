import unittest
from ..hash import *

MainNetGenesisHash = Hash(bytes([0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
                                 0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
                                 0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
                                 0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00]))


class TestHash(unittest.TestCase):
    def setUp(self):
        self.blockHashStr = "14a0810ac680a3eb3f82edc878cea25ec41d6b790744e5daeef"
        self.buf = bytes([0x79, 0xa6, 0x1a, 0xdb, 0xc6, 0xe5, 0xa2, 0xe1,
                          0x39, 0xd2, 0x71, 0x3a, 0x54, 0x6e, 0xc7, 0xc8,
                          0x75, 0x63, 0x2e, 0x75, 0xf1, 0xdf, 0x9c, 0x3f,
                          0xa6, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ])
        self.blockHash = new_hash_from_str(self.blockHashStr)

    def test_new_hash(self):
        hash = Hash(self.buf)

        # Ensure proper size.
        self.assertEqual(len(hash), HashSize,
                         msg='NewHash: hash length mismatch - got: {}, want: {}'.format(len(hash), HashSize))

        # Ensure contents match.
        self.assertEqual(hash.content, self.buf)

        # Ensure contents of hash of block 234440 don't match 234439.
        self.assertFalse(hash.is_equal(self.blockHash))

        # Set hash from byte slice and ensure contents match.
        hash.set_bytes(self.blockHash.clone_bytes())

        self.assertTrue(hash.is_equal(self.blockHash))

        #  Ensure nil hashes are handled properly. TODO

        # Invalid size for SetBytes.
        self.assertRaises(Err, hash.set_bytes(bytes([0x00])))

        # Invalid size for NewHash. TODO


#
#
# class TestHashString(unittest.TestCase):
#     def test_too_large(self):
#         pass
#
#
# class TestNewHashFromString(unittest.TestCase):
#     def test_too_large(self):
#         pass
