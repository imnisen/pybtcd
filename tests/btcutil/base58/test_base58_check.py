import unittest

from btcutil.base58.base58_check import *
from tests.utils import *

check_encoding_string_tests = [
    {"version": 20, "in": "", "out": "3MNQE1X"},
    {"version": 20, "in": " ", "out": "B2Kr6dBE"},
    {"version": 20, "in": "-", "out": "B3jv1Aft"},
    {"version": 20, "in": "0", "out": "B482yuaX"},
    {"version": 20, "in": "1", "out": "B4CmeGAC"},
    {"version": 20, "in": "-1", "out": "mM7eUf6kB"},
    {"version": 20, "in": "11", "out": "mP7BMTDVH"},
    {"version": 20, "in": "abc", "out": "4QiVtDjUdeq"},
    {"version": 20, "in": "1234598760", "out": "ZmNb8uQn5zvnUohNCEPP"},
    {"version": 20, "in": "abcdefghijklmnopqrstuvwxyz", "out": "K2RYDcKfupxwXdWhSAxQPCeiULntKm63UXyx5MvEH2"},
    {"version": 20, "in": "00000000000000000000000000000000000000000000000000000000000000",
     "out": "bi1EWXwJay2udZVxLJozuTb8Meg4W9c6xnmJaRDjg6pri5MBAxb9XwrpQXbtnqEoRV5U2pixnFfwyXC8tRAVC8XxnjK"},

]


class TestBase58Check(unittest.TestCase):
    def test_check_encode(self):
        for test in check_encoding_string_tests:
            self.assertEqual(check_encode(b=str_to_bytes(test['in']),
                                          version=test['version']),
                             test['out'])

    def test_check_decode(self):
        for test in check_encoding_string_tests:
            b, version = check_decode(test['out'])
            self.assertEqual(version, test['version'])
            self.assertEqual(bytes_to_str(b), test['in'])

        # Test checksum error
        with self.assertRaises(ErrChecksum):
            check_decode("3MNQE1Y")

        # Test invalid formats (string lengths below 5 mean the version byte and/or the checksum bytes are missing).
        s = ""
        for i in range(3):
            with self.assertRaises(ErrInvalidFormat):
                check_decode(s)
            s += '1'
