import unittest
from txscript.opcode import *


class TestOpCode(unittest.TestCase):
    def test_opcode_disabled(self):
        tests = bytes([
            OP_CAT, OP_SUBSTR, OP_LEFT, OP_RIGHT, OP_INVERT,
            OP_AND, OP_OR, OP_2MUL, OP_2DIV, OP_MUL, OP_DIV, OP_MOD,
            OP_LSHIFT, OP_RSHIFT
        ])

        for c in tests:
            pop = ParsedOpcode(opcode=opcode_array[c], data=None)
            with self.assertRaises(ScriptError) as cm:
                opcodeDisabled(pop, vm=None)
            self.assertEqual(cm.exception.c, ErrorCode.ErrDisabledOpcode)