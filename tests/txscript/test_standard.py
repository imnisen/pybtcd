import unittest
from tests.txscript.test_reference import *
from txscript.standard import *


def must_parse_short_form(script: str):
    return parse_short_form(script)


class TestStandard(unittest.TestCase):
    def test_mustParseShortForm(self):  # Refer to script_test
        pass

    def test_PushedData(self):
        tests = [
            {
                "script": "0 IF 0 ELSE 2 ENDIF",
                "out": [bytes(), bytes()],
                "valid": True
            },

            {
                "script": "16777216 10000000",
                "out": [bytes([0x00, 0x00, 0x00, 0x01]),   # 16777216
                        bytes([0x80, 0x96, 0x98, 0x00])],  # 10000000
                "valid": True
            },
            {
                "script": "DUP HASH160 '17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem' EQUALVERIFY CHECKSIG",
                "out": [bytes([
                    # 17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem
                    0x31, 0x37, 0x56, 0x5a, 0x4e, 0x58, 0x31, 0x53, 0x4e, 0x35,
                    0x4e, 0x74, 0x4b, 0x61, 0x38, 0x55, 0x51, 0x46, 0x78, 0x77,
                    0x51, 0x62, 0x46, 0x65, 0x46, 0x63, 0x33, 0x69, 0x71, 0x52,
                    0x59, 0x68, 0x65, 0x6d,
                ])],
                "valid": True
            },

            {
                "script": "PUSHDATA4 1000 EQUAL",
                "out": None,
                "valid": False
            },

        ]

        for test in tests:
            script = must_parse_short_form(test['script'])

            if test['valid']:
                data = pushed_data(script)
                self.assertEqual(data, test['out'])
            else:
                with self.assertRaises(Exception):
                    pushed_data(script)



