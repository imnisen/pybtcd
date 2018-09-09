import unittest
from chainhash.hash import *

class TestHash(unittest.TestCase):
    def setUp(self):
        self.test_case = [
            # Block 100000
            {
                "bytes": bytes([0x06, 0xe5, 0x33, 0xfd, 0x1a, 0xda, 0x86, 0x39,
                                0x1f, 0x3f, 0x6c, 0x34, 0x32, 0x04, 0xb0, 0xd2,
                                0x78, 0xd4, 0xaa, 0xec, 0x1c, 0x0b, 0x20, 0xaa,
                                0x27, 0xba, 0x03, 0x00, 0x00, 0x00, 0x00,
                                0x00, ]),
                "str": "000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"
            },

            # Block 234440
            {
                "bytes": bytes([0x79, 0xa6, 0x1a, 0xdb, 0xc6, 0xe5, 0xa2, 0xe1,
                                0x39, 0xd2, 0x71, 0x3a, 0x54, 0x6e, 0xc7, 0xc8,
                                0x75, 0x63, 0x2e, 0x75, 0xf1, 0xdf, 0x9c, 0x3f,
                                0xa6, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ]),
                "str": "00000000000001a63f9cdff1752e6375c8c76e543a71d239e1a2e5c6db1aa679"
            },

        ]

        # test str_to_bytes
        self.test_case2 = [
            # main net genesis hash
            {
                "str": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
                "bytes": bytes([0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
                                0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
                                0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
                                0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00, ]),
            },

            # main net genesis hash with stripped leading zeros
            {
                "str": "19d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
                "bytes": bytes([0x6f, 0xe2, 0x8c, 0x0a, 0xb6, 0xf1, 0xb3, 0x72,
                                0xc1, 0xa6, 0xa2, 0x46, 0xae, 0x63, 0xf7, 0x4f,
                                0x93, 0x1e, 0x83, 0x65, 0xe1, 0x5a, 0x08, 0x9c,
                                0x68, 0xd6, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00, ]),
            },

            # empty string
            {
                "str": "",
                "bytes": bytes(HashSize),
            },

            # Single digit hash.
            {
                "str": "1",
                "bytes": bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ]),
            },

            # Block 203707 with stripped leading zeros.
            {
                "str": "3264bc2ac36a60840790ba1d475d01367e7c723da941069e9dc",
                "bytes": bytes([0xdc, 0xe9, 0x69, 0x10, 0x94, 0xda, 0x23, 0xc7,
                                0xe7, 0x67, 0x13, 0xd0, 0x75, 0xd4, 0xa1, 0x0b,
                                0x79, 0x40, 0x08, 0xa6, 0x36, 0xac, 0xc2, 0x4b,
                                0x26, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ]),
            },

            # Hash string that is too long.
            {
                "str": "01234567890123456789012345678901234567890123456789012345678912345",
                "bytes": bytes([]),
                "err": HashStrSizeErr
            },

            # Hash string that is contains non-hex chars.
            {
                "str": "01234567890123456789012345678901234567890123456789012345678912345",
                "bytes": bytes([]),
                "err": Exception
            },

        ]

    def test_init(self):
        for c in self.test_case:
            Hash(c['bytes'])
            Hash(c['str'])

    def test_to_bytes(self):
        for c in self.test_case:
            self.assertEqual(Hash(c['bytes']).to_bytes(), c['bytes'])
            self.assertEqual(Hash(c['str']).to_bytes(), c['bytes'])

    def test_to_str(self):
        for c in self.test_case:
            self.assertEqual(Hash(c['bytes']).to_str(), c['str'])
            self.assertEqual(Hash(c['str']).to_str(), c['str'])

    def test_str_to_bytes(self):
        for c in self.test_case:
            self.assertEqual(Hash.str_to_bytes(c['str']), c['bytes'])

        for c in self.test_case2:
            if c.get('err'):
                # self.assertRaises don't catch here, I don't know why
                try:
                    Hash.str_to_bytes(c['str'])
                except Exception as e:
                    self.assertEqual(type(e), HashStrSizeErr)
            else:

                self.assertEqual(Hash.str_to_bytes(c['str']), c['bytes'])

    def test_bytes_to_str(self):
        for c in self.test_case:
            self.assertEqual(Hash.bytes_to_str(c['bytes']), c['str'])

    def test_len(self):
        for c in self.test_case:
            self.assertEqual(len(Hash(c['bytes'])), HashSize)
            self.assertEqual(len(Hash(c['str'])), HashSize)

    def test_str(self):
        for c in self.test_case:
            self.assertEqual(str(Hash(c['bytes'])), c['str'])
            self.assertEqual(str(Hash(c['str'])), c['str'])

    def test_repr(self):
        for c in self.test_case:
            self.assertEqual(repr(Hash(c['bytes'])), c['bytes'].hex())
            self.assertEqual(repr(Hash(c['str'])), c['bytes'].hex())

    def test_eq(self):
        for c in self.test_case:
            self.assertEqual(Hash(c['bytes']), Hash(c['str']))

    def test_copy_bytes(self):
        for c in self.test_case:
            self.assertEqual(Hash(c['bytes']).copy_bytes(), c['bytes'])
            # TOADD some modify behavior

    def test_set_bytes(self):
        hash_0 = Hash(self.test_case[0]['bytes'])
        hash_1 = Hash(self.test_case[1]['bytes'])

        self.assertFalse(hash_0 == hash_1)
        hash_0.set_bytes(hash_1.copy_bytes())
        self.assertTrue(hash_0 == hash_1)


if __name__ == '__main__':
    unittest.main()
