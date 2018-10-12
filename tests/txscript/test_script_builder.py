import unittest
from txscript.script_builder import *


class TestScriptBuilder(unittest.TestCase):
    def test_add_op(self):
        # parallel? TOADD

        tests = [
            {
                "name": "push OP_0",
                "opcodes": bytes([OP_0]),
                "expected": bytes([OP_0]),
            },

            {
                "name": "push OP_1 OP_2",
                "opcodes": bytes([OP_1, OP_2]),
                "expected": bytes([OP_1, OP_2]),
            },

            {
                "name": "push OP_HASH160 OP_EQUAL",
                "opcodes": bytes([OP_HASH160, OP_EQUAL]),
                "expected": bytes([OP_HASH160, OP_EQUAL]),
            },
        ]

        builder = ScriptBuilder()
        for test in tests:
            builder.reset()
            for opcode in test['opcodes']:
                builder.add_op(bytes([opcode]))

            self.assertEqual(builder.script, test['expected'])

        for test in tests:
            builder.reset()
            builder.add_ops(test['opcodes'])

            self.assertEqual(builder.script, test['expected'])

    def test_add_int64(self):
        # parallel? TOADD

        tests = [
            {"name": "push -1", "val": -1, "expected": bytes([OP_1NEGATE])},
            {"name": "push small int 0", "val": 0, "expected": bytes([OP_0])},
            {"name": "push small int 1", "val": 1, "expected": bytes([OP_1])},
            {"name": "push small int 2", "val": 2, "expected": bytes([OP_2])},
            {"name": "push small int 3", "val": 3, "expected": bytes([OP_3])},
            {"name": "push small int 4", "val": 4, "expected": bytes([OP_4])},
            {"name": "push small int 5", "val": 5, "expected": bytes([OP_5])},
            {"name": "push small int 6", "val": 6, "expected": bytes([OP_6])},
            {"name": "push small int 7", "val": 7, "expected": bytes([OP_7])},
            {"name": "push small int 8", "val": 8, "expected": bytes([OP_8])},
            {"name": "push small int 9", "val": 9, "expected": bytes([OP_9])},
            {"name": "push small int 10", "val": 10, "expected": bytes([OP_10])},
            {"name": "push small int 11", "val": 11, "expected": bytes([OP_11])},
            {"name": "push small int 12", "val": 12, "expected": bytes([OP_12])},
            {"name": "push small int 13", "val": 13, "expected": bytes([OP_13])},
            {"name": "push small int 14", "val": 14, "expected": bytes([OP_14])},
            {"name": "push small int 15", "val": 15, "expected": bytes([OP_15])},
            {"name": "push small int 16", "val": 16, "expected": bytes([OP_16])},
            {"name": "push 17", "val": 17, "expected": bytes([OP_DATA_1, 0x11])},
            {"name": "push 65", "val": 65, "expected": bytes([OP_DATA_1, 0x41])},
            {"name": "push 127", "val": 127, "expected": bytes([OP_DATA_1, 0x7f])},
            {"name": "push 128", "val": 128, "expected": bytes([OP_DATA_2, 0x80, 0])},
            {"name": "push 255", "val": 255, "expected": bytes([OP_DATA_2, 0xff, 0])},
            {"name": "push 256", "val": 256, "expected": bytes([OP_DATA_2, 0, 0x01])},
            {"name": "push 32767", "val": 32767, "expected": bytes([OP_DATA_2, 0xff, 0x7f])},
            {"name": "push 32768", "val": 32768, "expected": bytes([OP_DATA_3, 0, 0x80, 0])},
            {"name": "push -2", "val": -2, "expected": bytes([OP_DATA_1, 0x82])},
            {"name": "push -3", "val": -3, "expected": bytes([OP_DATA_1, 0x83])},
            {"name": "push -4", "val": -4, "expected": bytes([OP_DATA_1, 0x84])},
            {"name": "push -5", "val": -5, "expected": bytes([OP_DATA_1, 0x85])},
            {"name": "push -17", "val": -17, "expected": bytes([OP_DATA_1, 0x91])},
            {"name": "push -65", "val": -65, "expected": bytes([OP_DATA_1, 0xc1])},
            {"name": "push -127", "val": -127, "expected": bytes([OP_DATA_1, 0xff])},
            {"name": "push -128", "val": -128, "expected": bytes([OP_DATA_2, 0x80, 0x80])},
            {"name": "push -255", "val": -255, "expected": bytes([OP_DATA_2, 0xff, 0x80])},
            {"name": "push -256", "val": -256, "expected": bytes([OP_DATA_2, 0x00, 0x81])},
            {"name": "push -32767", "val": -32767, "expected": bytes([OP_DATA_2, 0xff, 0xff])},
            {"name": "push -32768", "val": -32768, "expected": bytes([OP_DATA_3, 0x00, 0x80, 0x80])},
        ]

        builder = ScriptBuilder()
        for test in tests:
            builder.reset().add_int64(test['val'])
            self.assertEqual(builder.script, test['expected'])

    def test_add_data(self):
        # parallel? TOADD

        tests = [
            # BIP0062: Pushing an empty byte sequence must use OP_0.
            {"name": "push empty byte sequence", "data": bytes(), "expected": bytes([OP_0])},
            {"name": "push 1 byte 0x00", "data": bytes([0x00]), "expected": bytes([OP_0])},

            # BIP0062: Pushing a 1-byte sequence of byte 0x01 through 0x10 must use OP_n.
            {"name": "push 1 byte 0x01", "data": bytes([0x01]), "expected": bytes([OP_1])},
            {"name": "push 1 byte 0x02", "data": bytes([0x02]), "expected": bytes([OP_2])},
            {"name": "push 1 byte 0x03", "data": bytes([0x03]), "expected": bytes([OP_3])},
            {"name": "push 1 byte 0x04", "data": bytes([0x04]), "expected": bytes([OP_4])},
            {"name": "push 1 byte 0x05", "data": bytes([0x05]), "expected": bytes([OP_5])},
            {"name": "push 1 byte 0x06", "data": bytes([0x06]), "expected": bytes([OP_6])},
            {"name": "push 1 byte 0x07", "data": bytes([0x07]), "expected": bytes([OP_7])},
            {"name": "push 1 byte 0x08", "data": bytes([0x08]), "expected": bytes([OP_8])},
            {"name": "push 1 byte 0x09", "data": bytes([0x09]), "expected": bytes([OP_9])},
            {"name": "push 1 byte 0x0a", "data": bytes([0x0a]), "expected": bytes([OP_10])},
            {"name": "push 1 byte 0x0b", "data": bytes([0x0b]), "expected": bytes([OP_11])},
            {"name": "push 1 byte 0x0c", "data": bytes([0x0c]), "expected": bytes([OP_12])},
            {"name": "push 1 byte 0x0d", "data": bytes([0x0d]), "expected": bytes([OP_13])},
            {"name": "push 1 byte 0x0e", "data": bytes([0x0e]), "expected": bytes([OP_14])},
            {"name": "push 1 byte 0x0f", "data": bytes([0x0f]), "expected": bytes([OP_15])},
            {"name": "push 1 byte 0x10", "data": bytes([0x10]), "expected": bytes([OP_16])},

            # BIP0062: Pushing the byte 0x81 must use OP_1NEGATE.
            {"name": "push 1 byte 0x81", "data": bytes([0x81]), "expected": bytes([OP_1NEGATE])},

            # BIP0062: Pushing any other byte sequence up to 75 bytes must
            # use the normal data push (opcode byte n, with n the number of
            # bytes, followed n bytes of data being pushed)
            {"name": "push 1 byte 0x11", "data": bytes([0x11]), "expected": bytes([OP_DATA_1, 0x11])},
            {"name": "push 1 byte 0x80", "data": bytes([0x80]), "expected": bytes([OP_DATA_1, 0x80])},
            {"name": "push 1 byte 0x82", "data": bytes([0x82]), "expected": bytes([OP_DATA_1, 0x82])},
            {"name": "push 1 byte 0xff", "data": bytes([0xff]), "expected": bytes([OP_DATA_1, 0xff])},
            {
                "name": "push data len 17",
                "data": bytes([0x49]) * 17,
                "expected": bytes([OP_DATA_17]) + bytes([0x49]) * 17,
            },
            {
                "name": "push data len 75",
                "data": bytes([0x49]) * 75,
                "expected": bytes([OP_DATA_75]) + bytes([0x49]) * 75,
            },

            # BIP0062: Pushing 76 to 255 bytes must use OP_PUSHDATA1.
            {
                "name": "push data len 76",
                "data": bytes([0x49]) * 76,
                "expected": bytes([OP_PUSHDATA1, 76]) + bytes([0x49]) * 76,
            },
            {
                "name": "push data len 255",
                "data": bytes([0x49]) * 255,
                "expected": bytes([OP_PUSHDATA1, 255]) + bytes([0x49]) * 255,
            },

            # BIP0062: Pushing 256 to 520 bytes must use OP_PUSHDATA2.
            {
                "name": "push data len 256",
                "data": bytes([0x49]) * 256,
                "expected": bytes([OP_PUSHDATA2, 0, 1]) + bytes([0x49]) * 256,
            },
            {
                "name": "push data len 520",
                "data": bytes([0x49]) * 520,
                "expected": bytes([OP_PUSHDATA2, 0x08, 0x02]) + bytes([0x49]) * 520,
            },

            # BIP0062: OP_PUSHDATA4 can never be used, as pushes over 520
            # bytes are not allowed, and those below can be done using
            # other operators.
            {
                "name": "push data len 521",
                "data": bytes([0x49]) * 521,
                "expected": None,
                "err": ErrScriptNotCanonical
            },

            {
                "name": "push data len 32767 (canonical)",
                "data": bytes([0x49]) * 32767,
                "expected": None,
                "err": ErrScriptNotCanonical
            },

            {
                "name": "push data len 65536 (canonical)",
                "data": bytes([0x49]) * 65536,
                "expected": None,
                "err": ErrScriptNotCanonical
            },

        ]

        builder = ScriptBuilder()
        for test in tests:
            if 'err' not in test:
                builder.reset().add_data(test['data'])
                self.assertEqual(builder.script, test['expected'])
            else:
                with self.assertRaises(test['err']) as cm:
                    builder.reset().add_data(test['data'])

        # Additional tests for the PushFullData function that
        # intentionally allows data pushes to exceed the limit for
        # regression testing purposes.
        tests_2 = [

            # 3-byte data push via OP_PUSHDATA_2.
            {
                "name": "push data len 32767 (non-canonical)",
                "data": bytes([0x49]) * 32767,
                "expected": bytes([OP_PUSHDATA2, 255, 127]) + bytes([0x49]) * 32767,

            },

            # 5-byte data push via OP_PUSHDATA_4.
            {
                "name": "push data len 65536 (non-canonical)",
                "data": bytes([0x49]) * 65536,
                "expected": bytes([OP_PUSHDATA4, 0, 0, 1, 0]) + bytes([0x49]) * 65536,

            },

        ]
        builder = ScriptBuilder()
        for test in tests_2:
            builder.reset().add_full_data(test['data'])
            self.assertEqual(builder.script, test['expected'])

    def test_exceed_max_script_size(self):
        # parallel? TOADD

        builder = ScriptBuilder()
        builder.add_full_data(bytes(MaxScriptSize - 3))
        with self.assertRaises(ErrScriptNotCanonical):
            builder.add_data(bytes([0x00]))

        builder = ScriptBuilder()
        builder.add_full_data(bytes(MaxScriptSize - 3))
        with self.assertRaises(ErrScriptNotCanonical):
            builder.add_op(bytes([OP_0]))

        builder = ScriptBuilder()
        builder.add_full_data(bytes(MaxScriptSize - 3))
        with self.assertRaises(ErrScriptNotCanonical):
            builder.add_int64(0)

        # TOCHECK maybe when raise error, we can still got to add, not to top caller?
        # just like golang use pass err, not raise, but consider later
        # To ensures that all of the functions that can be used to add
        # data to a script don't modify the script once an error has happened.
        # TODO
