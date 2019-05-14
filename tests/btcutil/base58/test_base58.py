import unittest

from btcutil.base58 import *
from tests.utils import hex_to_bytes

string_tests = [
    {"in": "", "out": ""},
    {"in": " ", "out": "Z"},
    {"in": "-", "out": "n"},
    {"in": "0", "out": "q"},
    {"in": "1", "out": "r"},
    {"in": "-1", "out": "4SU"},
    {"in": "11", "out": "4k8"},
    {"in": "abc", "out": "ZiCa"},
    {"in": "1234598760", "out": "3mJr7AoUXx2Wqd"},
    {"in": "abcdefghijklmnopqrstuvwxyz", "out": "3yxU3u1igY8WkgtjK92fbJQCd4BZiiT1v25f"},
    {"in": "00000000000000000000000000000000000000000000000000000000000000",
     "out": "3sN2THZeE9Eh9eYrwkvZqNstbHGvrxSAM7gXUXvyFQP8XvQLUqNCS27icwUeDT7ckHm4FUHM2mTVh1vbLmk7y"},
]

invalid_string_tests = [
    {"in": "0", "out": ""},
    {"in": "O", "out": ""},
    {"in": "I", "out": ""},
    {"in": "l", "out": ""},
    {"in": "3mJr0", "out": ""},
    {"in": "O3yxU", "out": ""},
    {"in": "3sNI", "out": ""},
    {"in": "4kl8", "out": ""},
    {"in": "0OIl", "out": ""},
    {"in": "!@#$%^&*()-_=+~`", "out": ""},

]

hex_tests = [
    {"in": "61", "out": "2g"},
    {"in": "626262", "out": "a3gV"},
    {"in": "636363", "out": "aPEr"},
    {"in": "73696d706c792061206c6f6e6720737472696e67", "out": "2cFupjhnEsSn59qHXstmK2ffpLv2"},
    {"in": "00eb15231dfceb60925886b67d065299925915aeb172c06647", "out": "1NS17iag9jJgTHD1VXjvLCEnZuQ3rJDE9L"},
    {"in": "516b6fcd0f", "out": "ABnLTmg"},
    {"in": "bf4f89001e670274dd", "out": "3SEo3LWLoPntC"},
    {"in": "572e4794", "out": "3EFU7m"},
    {"in": "ecac89cad93923c02321", "out": "EJDM8drfXA6uyA"},
    {"in": "10c8511e", "out": "Rt5zm"},
    {"in": "00000000000000000000", "out": "1111111111"},
]


class TestBase58(unittest.TestCase):
    def test_encode(self):
        for test in string_tests:
            self.assertEqual(encode(test['in']), test['out'])

    def test_decode(self):
        for test in hex_tests:
            self.assertEqual(decode(test['out']), hex_to_bytes(test['in']))

        for test in invalid_string_tests:
            self.assertEqual(decode(test['in']), test['out'])
