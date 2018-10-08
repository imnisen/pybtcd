import unittest
from txscript.script_num import *


def hex_to_bytes(s):
    return bytes.fromhex(s)


class TestScriptNum(unittest.TestCase):
    def test_bytes(self):
        tests = [
            {"num": 0, "serialized": bytes()},
            {"num": 1, "serialized": hex_to_bytes("01")},
            {"num": -1, "serialized": hex_to_bytes("81")},
            {"num": 127, "serialized": hex_to_bytes("7f")},
            {"num": -127, "serialized": hex_to_bytes("ff")},
            {"num": 128, "serialized": hex_to_bytes("8000")},
            {"num": -128, "serialized": hex_to_bytes("8080")},
            {"num": 129, "serialized": hex_to_bytes("8100")},
            {"num": -129, "serialized": hex_to_bytes("8180")},
            {"num": 256, "serialized": hex_to_bytes("0001")},
            {"num": -256, "serialized": hex_to_bytes("0081")},
            {"num": 32767, "serialized": hex_to_bytes("ff7f")},
            {"num": -32767, "serialized": hex_to_bytes("ffff")},
            {"num": 32768, "serialized": hex_to_bytes("008000")},
            {"num": -32768, "serialized": hex_to_bytes("008080")},
            {"num": 65535, "serialized": hex_to_bytes("ffff00")},
            {"num": -65535, "serialized": hex_to_bytes("ffff80")},
            {"num": 524288, "serialized": hex_to_bytes("000008")},
            {"num": -524288, "serialized": hex_to_bytes("000088")},
            {"num": 7340032, "serialized": hex_to_bytes("000070")},
            {"num": -7340032, "serialized": hex_to_bytes("0000f0")},
            {"num": 8388608, "serialized": hex_to_bytes("00008000")},
            {"num": -8388608, "serialized": hex_to_bytes("00008080")},
            {"num": 2147483647, "serialized": hex_to_bytes("ffffff7f")},
            {"num": -2147483647, "serialized": hex_to_bytes("ffffffff")},

            # Values that are out of range for data that is interpreted as
            # numbers, but are allowed as the result of numeric operations.
            {"num": 2147483648, "serialized": hex_to_bytes("0000008000")},
            {"num": -2147483648, "serialized": hex_to_bytes("0000008080")},
            {"num": 2415919104, "serialized": hex_to_bytes("0000009000")},
            {"num": -2415919104, "serialized": hex_to_bytes("0000009080")},
            {"num": 4294967295, "serialized": hex_to_bytes("ffffffff00")},
            {"num": -4294967295, "serialized": hex_to_bytes("ffffffff80")},
            {"num": 4294967296, "serialized": hex_to_bytes("0000000001")},
            {"num": -4294967296, "serialized": hex_to_bytes("0000000081")},
            {"num": 281474976710655, "serialized": hex_to_bytes("ffffffffffff00")},
            {"num": -281474976710655, "serialized": hex_to_bytes("ffffffffffff80")},
            {"num": 72057594037927935, "serialized": hex_to_bytes("ffffffffffffff00")},
            {"num": -72057594037927935, "serialized": hex_to_bytes("ffffffffffffff80")},
            {"num": 9223372036854775807, "serialized": hex_to_bytes("ffffffffffffff7f")},
            {"num": -9223372036854775807, "serialized": hex_to_bytes("ffffffffffffffff")},
        ]

        for c in tests:
            self.assertEqual(ScriptNum(c['num']).bytes(), c['serialized'])

    def test_make_script_num(self):
        tests = [
            # Minimal encoding must reject negative 0.
            {"serialized": hex_to_bytes("80"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},

            # Minimally encoded valid values with minimal encoding flag.
            # Should not error and return expected integral number.
            {"serialized": bytes(), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("01"), "num": 1, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("81"), "num": -1, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("7f"), "num": 127, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ff"), "num": -127, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("8000"), "num": 128, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("8080"), "num": -128, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("8100"), "num": 129, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("8180"), "num": -129, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("0001"), "num": 256, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("0081"), "num": -256, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ff7f"), "num": 32767, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffff"), "num": -32767, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("008000"), "num": 32768, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("008080"), "num": -32768, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("ffff00"), "num": 65535, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffff80"), "num": -65535, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("000008"), "num": 524288, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("000088"), "num": -524288, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("000070"), "num": 7340032, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("0000f0"), "num": -7340032, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("00008000"), "num": 8388608, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("00008080"), "num": -8388608, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("ffffff7f"), "num": 2147483647, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("ffffffff"), "num": -2147483647, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("ffffffff7f"), "num": 549755813887, "numLen": 5, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffffffffff"), "num": -549755813887, "numLen": 5, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffffffffffffff7f"), "num": 9223372036854775807, "numLen": 8,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("ffffffffffffffff"), "num": -9223372036854775807, "numLen": 8,
             "minimalEncoding": True, "err": None},
            {"serialized": hex_to_bytes("ffffffffffffffff7f"), "num": -1, "numLen": 9, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffffffffffffffffff"), "num": 1, "numLen": 9, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffffffffffffffffff7f"), "num": -1, "numLen": 10, "minimalEncoding": True,
             "err": None},
            {"serialized": hex_to_bytes("ffffffffffffffffffff"), "num": 1, "numLen": 10, "minimalEncoding": True,
             "err": None},

            # Minimally encoded values that are out of range for data that
            # is interpreted as script numbers with the minimal encoding
            # flag set.  Should error and return 0.
            {"serialized": hex_to_bytes("0000008000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("0000008080"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("0000009000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("0000009080"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffff00"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffff80"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("0000000001"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("0000000081"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffffffff00"), "num": 0, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffffffff80"), "num": 0, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffffffffff00"), "num": 0, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffffffffff80"), "num": 0, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffffffffff7f"), "num": 0, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": ErrorCode.ErrNumberTooBig},
            {"serialized": hex_to_bytes("ffffffffffffffff"), "num": 0, "numLen": defaultScriptNumLen,
             "minimalEncoding": True, "err": ErrorCode.ErrNumberTooBig},

            # Non-minimally encoded, but otherwise valid values with
            # minimal encoding flag.  Should error and return 0.
            {"serialized": hex_to_bytes("00"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 0
            {"serialized": hex_to_bytes("0100"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 1
            {"serialized": hex_to_bytes("7f00"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 127
            {"serialized": hex_to_bytes("800000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 128
            {"serialized": hex_to_bytes("810000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 129
            {"serialized": hex_to_bytes("000100"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 256
            {"serialized": hex_to_bytes("ff7f00"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 32767
            {"serialized": hex_to_bytes("00800000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 32768
            {"serialized": hex_to_bytes("ffff0000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 65535
            {"serialized": hex_to_bytes("00000800"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 524288
            {"serialized": hex_to_bytes("00007000"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 7340032
            {"serialized": hex_to_bytes("0009000100"), "num": 0, "numLen": 5, "minimalEncoding": True,
             "err": ErrorCode.ErrMinimalData},  # 16779520

            # Non-minimally encoded, but otherwise valid values without
            # minimal encoding flag.  Should not error and return expected
            # integral number.
            {"serialized": hex_to_bytes("00"), "num": 0, "numLen": defaultScriptNumLen, "minimalEncoding": False,
             "err": None},
            {"serialized": hex_to_bytes("0100"), "num": 1, "numLen": defaultScriptNumLen, "minimalEncoding": False,
             "err": None},
            {"serialized": hex_to_bytes("7f00"), "num": 127, "numLen": defaultScriptNumLen, "minimalEncoding": False,
             "err": None},
            {"serialized": hex_to_bytes("800000"), "num": 128, "numLen": defaultScriptNumLen, "minimalEncoding": False,
             "err": None},
            {"serialized": hex_to_bytes("810000"), "num": 129, "numLen": defaultScriptNumLen, "minimalEncoding": False,
             "err": None},
            {"serialized": hex_to_bytes("000100"), "num": 256, "numLen": defaultScriptNumLen, "minimalEncoding": False,
             "err": None},
            {"serialized": hex_to_bytes("ff7f00"), "num": 32767, "numLen": defaultScriptNumLen,
             "minimalEncoding": False, "err": None},
            {"serialized": hex_to_bytes("00800000"), "num": 32768, "numLen": defaultScriptNumLen,
             "minimalEncoding": False, "err": None},
            {"serialized": hex_to_bytes("ffff0000"), "num": 65535, "numLen": defaultScriptNumLen,
             "minimalEncoding": False, "err": None},
            {"serialized": hex_to_bytes("00000800"), "num": 524288, "numLen": defaultScriptNumLen,
             "minimalEncoding": False, "err": None},
            {"serialized": hex_to_bytes("00007000"), "num": 7340032, "numLen": defaultScriptNumLen,
             "minimalEncoding": False, "err": None},
            {"serialized": hex_to_bytes("0009000100"), "num": 16779520, "numLen": 5, "minimalEncoding": False,
             "err": None},
        ]

        for c in tests:
            if c['err']:
                with self.assertRaises(ScriptError) as cm:
                    make_script_num(c['serialized'], c['minimalEncoding'], c['numLen'])
                self.assertEqual(cm.exception.c, c['err'])
            else:
                self.assertEqual(make_script_num(c['serialized'], c['minimalEncoding'], c['numLen']), c['num'])

    def test_int32(self):
        tests = [
            # Values inside the valid int32 range are just the values
            # themselves cast to an int32.
            {"in": 0, "want": 0},
            {"in": 1, "want": 1},
            {"in": -1, "want": -1},
            {"in": 127, "want": 127},
            {"in": -127, "want": -127},
            {"in": 128, "want": 128},
            {"in": -128, "want": -128},
            {"in": 129, "want": 129},
            {"in": -129, "want": -129},
            {"in": 256, "want": 256},
            {"in": -256, "want": -256},
            {"in": 32767, "want": 32767},
            {"in": -32767, "want": -32767},
            {"in": 32768, "want": 32768},
            {"in": -32768, "want": -32768},
            {"in": 65535, "want": 65535},
            {"in": -65535, "want": -65535},
            {"in": 524288, "want": 524288},
            {"in": -524288, "want": -524288},
            {"in": 7340032, "want": 7340032},
            {"in": -7340032, "want": -7340032},
            {"in": 8388608, "want": 8388608},
            {"in": -8388608, "want": -8388608},
            {"in": 2147483647, "want": 2147483647},
            {"in": -2147483647, "want": -2147483647},
            {"in": -2147483648, "want": -2147483648},

            # Values outside of the valid int32 range are limited to int32.
            {"in": 2147483648, "want": 2147483647},
            {"in": -2147483649, "want": -2147483648},
            {"in": 1152921504606846975, "want": 2147483647},
            {"in": -1152921504606846975, "want": -2147483648},
            {"in": 2305843009213693951, "want": 2147483647},
            {"in": -2305843009213693951, "want": -2147483648},
            {"in": 4611686018427387903, "want": 2147483647},
            {"in": -4611686018427387903, "want": -2147483648},
            {"in": 9223372036854775807, "want": 2147483647},
            {"in": -9223372036854775808, "want": -2147483648},
        ]

        for c in tests:
            self.assertEqual(ScriptNum(c['in']).int32(), c['want'])
