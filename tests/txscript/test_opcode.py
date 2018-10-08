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

    def test_bytes(self):
        tests = [

            {
                "name": "OP_FALSE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_FALSE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_FALSE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_FALSE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_1 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_1],
                    data=None,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_1",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_1],
                    data=bytes([0x00]),
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_1 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_1],
                    data=bytes([0x00]) * 2,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_2 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_2],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_2",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_2],
                    data=bytes([0x00]) * 2,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_2 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_2],
                    data=bytes([0x00]) * 3,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_3 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_3],
                    data=bytes([0x00]) * 2,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_3",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_3],
                    data=bytes([0x00]) * 3,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_3 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_3],
                    data=bytes([0x00]) * 4,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_4 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_4],
                    data=bytes([0x00]) * 3,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_4",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_4],
                    data=bytes([0x00]) * 4,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_4 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_4],
                    data=bytes([0x00]) * 5,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_5 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_5],
                    data=bytes([0x00]) * 4,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_5",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_5],
                    data=bytes([0x00]) * 5,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_5 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_5],
                    data=bytes([0x00]) * 6,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_6 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_6],
                    data=bytes([0x00]) * 5,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_6",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_6],
                    data=bytes([0x00]) * 6,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_6 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_6],
                    data=bytes([0x00]) * 7,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_7 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_7],
                    data=bytes([0x00]) * 6,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_7",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_7],
                    data=bytes([0x00]) * 7,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_7 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_7],
                    data=bytes([0x00]) * 8,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_8 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_8],
                    data=bytes([0x00]) * 7,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_8",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_8],
                    data=bytes([0x00]) * 8,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_8 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_8],
                    data=bytes([0x00]) * 9,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_9 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_9],
                    data=bytes([0x00]) * 8,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_9",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_9],
                    data=bytes([0x00]) * 9,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_9 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_9],
                    data=bytes([0x00]) * 10,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_10 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_10],
                    data=bytes([0x00]) * 9,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_10",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_10],
                    data=bytes([0x00]) * 10,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_10 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_10],
                    data=bytes([0x00]) * 11,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_11 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_11],
                    data=bytes([0x00]) * 10,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_11",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_11],
                    data=bytes([0x00]) * 11,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_11 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_11],
                    data=bytes([0x00]) * 12,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_12 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_12],
                    data=bytes([0x00]) * 11,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_12",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_12],
                    data=bytes([0x00]) * 12,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_12 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_12],
                    data=bytes([0x00]) * 13,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_13 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_13],
                    data=bytes([0x00]) * 12,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_13",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_13],
                    data=bytes([0x00]) * 13,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_13 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_13],
                    data=bytes([0x00]) * 14,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_14 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_14],
                    data=bytes([0x00]) * 13,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_14",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_14],
                    data=bytes([0x00]) * 14,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_14 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_14],
                    data=bytes([0x00]) * 15,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_15 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_15],
                    data=bytes([0x00]) * 14,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_15",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_15],
                    data=bytes([0x00]) * 15,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_15 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_15],
                    data=bytes([0x00]) * 16,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_16 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_16],
                    data=bytes([0x00]) * 15,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_16",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_16],
                    data=bytes([0x00]) * 16,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_16 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_16],
                    data=bytes([0x00]) * 17,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_17 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_17],
                    data=bytes([0x00]) * 16,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_17",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_17],
                    data=bytes([0x00]) * 17,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_17 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_17],
                    data=bytes([0x00]) * 18,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_18 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_18],
                    data=bytes([0x00]) * 17,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_18",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_18],
                    data=bytes([0x00]) * 18,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_18 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_18],
                    data=bytes([0x00]) * 19,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_19 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_19],
                    data=bytes([0x00]) * 18,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_19",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_19],
                    data=bytes([0x00]) * 19,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_19 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_19],
                    data=bytes([0x00]) * 20,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_20 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_20],
                    data=bytes([0x00]) * 19,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_20",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_20],
                    data=bytes([0x00]) * 20,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_20 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_20],
                    data=bytes([0x00]) * 21,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_21 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_21],
                    data=bytes([0x00]) * 20,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_21",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_21],
                    data=bytes([0x00]) * 21,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_21 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_21],
                    data=bytes([0x00]) * 22,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_22 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_22],
                    data=bytes([0x00]) * 21,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_22",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_22],
                    data=bytes([0x00]) * 22,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_22 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_22],
                    data=bytes([0x00]) * 23,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_23 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_23],
                    data=bytes([0x00]) * 22,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_23",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_23],
                    data=bytes([0x00]) * 23,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_23 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_23],
                    data=bytes([0x00]) * 24,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_24 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_24],
                    data=bytes([0x00]) * 23,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_24",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_24],
                    data=bytes([0x00]) * 24,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_24 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_24],
                    data=bytes([0x00]) * 25,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_25 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_25],
                    data=bytes([0x00]) * 24,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_25",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_25],
                    data=bytes([0x00]) * 25,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_25 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_25],
                    data=bytes([0x00]) * 26,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_26 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_26],
                    data=bytes([0x00]) * 25,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_26",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_26],
                    data=bytes([0x00]) * 26,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_26 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_26],
                    data=bytes([0x00]) * 27,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_27 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_27],
                    data=bytes([0x00]) * 26,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_27",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_27],
                    data=bytes([0x00]) * 27,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_27 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_27],
                    data=bytes([0x00]) * 28,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_28 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_28],
                    data=bytes([0x00]) * 27,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_28",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_28],
                    data=bytes([0x00]) * 28,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_28 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_28],
                    data=bytes([0x00]) * 29,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_29 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_29],
                    data=bytes([0x00]) * 28,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_29",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_29],
                    data=bytes([0x00]) * 29,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_29 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_29],
                    data=bytes([0x00]) * 30,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_30 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_30],
                    data=bytes([0x00]) * 29,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_30",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_30],
                    data=bytes([0x00]) * 30,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_30 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_30],
                    data=bytes([0x00]) * 31,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_31 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_31],
                    data=bytes([0x00]) * 30,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_31",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_31],
                    data=bytes([0x00]) * 31,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_31 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_31],
                    data=bytes([0x00]) * 32,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_32 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_32],
                    data=bytes([0x00]) * 31,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_32",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_32],
                    data=bytes([0x00]) * 32,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_32 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_32],
                    data=bytes([0x00]) * 33,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_33 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_33],
                    data=bytes([0x00]) * 32,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_33",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_33],
                    data=bytes([0x00]) * 33,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_33 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_33],
                    data=bytes([0x00]) * 34,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_34 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_34],
                    data=bytes([0x00]) * 33,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_34",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_34],
                    data=bytes([0x00]) * 34,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_34 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_34],
                    data=bytes([0x00]) * 35,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_35 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_35],
                    data=bytes([0x00]) * 34,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_35",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_35],
                    data=bytes([0x00]) * 35,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_35 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_35],
                    data=bytes([0x00]) * 36,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_36 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_36],
                    data=bytes([0x00]) * 35,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_36",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_36],
                    data=bytes([0x00]) * 36,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_36 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_36],
                    data=bytes([0x00]) * 37,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_37 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_37],
                    data=bytes([0x00]) * 36,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_37",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_37],
                    data=bytes([0x00]) * 37,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_37 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_37],
                    data=bytes([0x00]) * 38,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_38 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_38],
                    data=bytes([0x00]) * 37,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_38",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_38],
                    data=bytes([0x00]) * 38,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_38 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_38],
                    data=bytes([0x00]) * 39,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_39 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_39],
                    data=bytes([0x00]) * 38,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_39",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_39],
                    data=bytes([0x00]) * 39,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_39 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_39],
                    data=bytes([0x00]) * 40,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_40 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_40],
                    data=bytes([0x00]) * 39,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_40",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_40],
                    data=bytes([0x00]) * 40,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_40 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_40],
                    data=bytes([0x00]) * 41,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_41 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_41],
                    data=bytes([0x00]) * 40,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_41",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_41],
                    data=bytes([0x00]) * 41,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_41 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_41],
                    data=bytes([0x00]) * 42,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_42 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_42],
                    data=bytes([0x00]) * 41,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_42",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_42],
                    data=bytes([0x00]) * 42,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_42 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_42],
                    data=bytes([0x00]) * 43,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_43 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_43],
                    data=bytes([0x00]) * 42,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_43",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_43],
                    data=bytes([0x00]) * 43,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_43 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_43],
                    data=bytes([0x00]) * 44,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_44 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_44],
                    data=bytes([0x00]) * 43,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_44",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_44],
                    data=bytes([0x00]) * 44,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_44 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_44],
                    data=bytes([0x00]) * 45,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_45 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_45],
                    data=bytes([0x00]) * 44,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_45",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_45],
                    data=bytes([0x00]) * 45,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_45 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_45],
                    data=bytes([0x00]) * 46,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_46 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_46],
                    data=bytes([0x00]) * 45,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_46",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_46],
                    data=bytes([0x00]) * 46,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_46 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_46],
                    data=bytes([0x00]) * 47,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_47 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_47],
                    data=bytes([0x00]) * 46,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_47",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_47],
                    data=bytes([0x00]) * 47,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_47 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_47],
                    data=bytes([0x00]) * 48,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_48 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_48],
                    data=bytes([0x00]) * 47,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_48",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_48],
                    data=bytes([0x00]) * 48,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_48 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_48],
                    data=bytes([0x00]) * 49,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_49 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_49],
                    data=bytes([0x00]) * 48,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_49",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_49],
                    data=bytes([0x00]) * 49,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_49 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_49],
                    data=bytes([0x00]) * 50,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_50 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_50],
                    data=bytes([0x00]) * 49,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_50",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_50],
                    data=bytes([0x00]) * 50,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_50 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_50],
                    data=bytes([0x00]) * 51,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_51 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_51],
                    data=bytes([0x00]) * 50,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_51",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_51],
                    data=bytes([0x00]) * 51,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_51 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_51],
                    data=bytes([0x00]) * 52,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_52 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_52],
                    data=bytes([0x00]) * 51,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_52",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_52],
                    data=bytes([0x00]) * 52,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_52 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_52],
                    data=bytes([0x00]) * 53,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_53 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_53],
                    data=bytes([0x00]) * 52,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_53",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_53],
                    data=bytes([0x00]) * 53,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_53 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_53],
                    data=bytes([0x00]) * 54,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_54 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_54],
                    data=bytes([0x00]) * 53,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_54",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_54],
                    data=bytes([0x00]) * 54,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_54 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_54],
                    data=bytes([0x00]) * 55,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_55 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_55],
                    data=bytes([0x00]) * 54,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_55",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_55],
                    data=bytes([0x00]) * 55,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_55 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_55],
                    data=bytes([0x00]) * 56,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_56 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_56],
                    data=bytes([0x00]) * 55,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_56",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_56],
                    data=bytes([0x00]) * 56,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_56 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_56],
                    data=bytes([0x00]) * 57,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_57 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_57],
                    data=bytes([0x00]) * 56,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_57",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_57],
                    data=bytes([0x00]) * 57,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_57 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_57],
                    data=bytes([0x00]) * 58,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_58 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_58],
                    data=bytes([0x00]) * 57,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_58",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_58],
                    data=bytes([0x00]) * 58,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_58 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_58],
                    data=bytes([0x00]) * 59,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_59 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_59],
                    data=bytes([0x00]) * 58,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_59",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_59],
                    data=bytes([0x00]) * 59,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_59 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_59],
                    data=bytes([0x00]) * 60,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_60 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_60],
                    data=bytes([0x00]) * 59,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_60",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_60],
                    data=bytes([0x00]) * 60,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_60 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_60],
                    data=bytes([0x00]) * 61,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_61 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_61],
                    data=bytes([0x00]) * 60,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_61",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_61],
                    data=bytes([0x00]) * 61,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_61 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_61],
                    data=bytes([0x00]) * 62,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_62 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_62],
                    data=bytes([0x00]) * 61,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_62",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_62],
                    data=bytes([0x00]) * 62,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_62 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_62],
                    data=bytes([0x00]) * 63,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_63 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_63],
                    data=bytes([0x00]) * 62,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_63",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_63],
                    data=bytes([0x00]) * 63,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_63 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_63],
                    data=bytes([0x00]) * 64,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_64 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_64],
                    data=bytes([0x00]) * 63,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_64",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_64],
                    data=bytes([0x00]) * 64,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_64 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_64],
                    data=bytes([0x00]) * 65,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_65 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_65],
                    data=bytes([0x00]) * 64,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_65",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_65],
                    data=bytes([0x00]) * 65,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_65 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_65],
                    data=bytes([0x00]) * 66,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_66 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_66],
                    data=bytes([0x00]) * 65,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_66",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_66],
                    data=bytes([0x00]) * 66,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_66 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_66],
                    data=bytes([0x00]) * 67,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_67 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_67],
                    data=bytes([0x00]) * 66,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_67",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_67],
                    data=bytes([0x00]) * 67,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_67 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_67],
                    data=bytes([0x00]) * 68,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_68 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_68],
                    data=bytes([0x00]) * 67,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_68",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_68],
                    data=bytes([0x00]) * 68,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_68 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_68],
                    data=bytes([0x00]) * 69,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_69 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_69],
                    data=bytes([0x00]) * 68,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_69",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_69],
                    data=bytes([0x00]) * 69,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_69 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_69],
                    data=bytes([0x00]) * 70,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_70 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_70],
                    data=bytes([0x00]) * 69,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_70",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_70],
                    data=bytes([0x00]) * 70,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_70 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_70],
                    data=bytes([0x00]) * 71,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_71 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_71],
                    data=bytes([0x00]) * 70,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_71",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_71],
                    data=bytes([0x00]) * 71,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_71 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_71],
                    data=bytes([0x00]) * 72,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_72 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_72],
                    data=bytes([0x00]) * 71,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_72",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_72],
                    data=bytes([0x00]) * 72,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_72 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_72],
                    data=bytes([0x00]) * 73,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_73 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_73],
                    data=bytes([0x00]) * 72,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_73",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_73],
                    data=bytes([0x00]) * 73,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_73 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_73],
                    data=bytes([0x00]) * 74,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_74 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_74],
                    data=bytes([0x00]) * 73,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_74",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_74],
                    data=bytes([0x00]) * 74,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_74 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_74],
                    data=bytes([0x00]) * 75,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_75 short",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_75],
                    data=bytes([0x00]) * 74,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DATA_75",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_75],
                    data=bytes([0x00]) * 75,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DATA_75 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DATA_75],
                    data=bytes([0x00]) * 76,
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_PUSHDATA1",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUSHDATA1],
                    data=bytes([0x01, 0x02, 0x03, 0x04]),
                ),
                "expected_err": None,
            },
            {
                "name": "OP_PUSHDATA2",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUSHDATA2],
                    data=bytes([0x01, 0x02, 0x03, 0x04]),
                ),
                "expected_err": None,
            },
            {
                "name": "OP_PUSHDATA4",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUSHDATA1],
                    data=bytes([0x01, 0x02, 0x03, 0x04]),
                ),
                "expected_err": None,
            },
            {
                "name": "OP_1NEGATE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_1NEGATE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_1NEGATE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_1NEGATE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RESERVED",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RESERVED],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RESERVED long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RESERVED],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_TRUE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_TRUE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_TRUE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_TRUE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_3",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_3],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_3 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_3],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_4",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_4],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_4 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_4],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_5",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_5],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_5 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_5],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_6",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_6],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_6 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_6],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_7",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_7],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_7 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_7],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_8",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_8],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_8 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_8],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_9",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_9],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_9 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_9],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_10",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_10],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_10 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_10],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_11",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_11],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_11 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_11],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_12",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_12],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_12 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_12],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_13",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_13],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_13 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_13],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_14",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_14],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_14 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_14],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_15",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_15],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_15 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_15],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_16",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_16],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_16 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_16],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_VER",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VER],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_VER long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VER],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_IF",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_IF],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_IF long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_IF],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOTIF",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOTIF],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOTIF long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOTIF],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_VERIF",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VERIF],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_VERIF long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VERIF],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_VERNOTIF",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VERNOTIF],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_VERNOTIF long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VERNOTIF],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_ELSE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ELSE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_ELSE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ELSE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_ENDIF",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ENDIF],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_ENDIF long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ENDIF],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_VERIFY",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VERIFY],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_VERIFY long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_VERIFY],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RETURN",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RETURN],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RETURN long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RETURN],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_TOALTSTACK",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_TOALTSTACK],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_TOALTSTACK long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_TOALTSTACK],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_FROMALTSTACK",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_FROMALTSTACK],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_FROMALTSTACK long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_FROMALTSTACK],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2DROP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2DROP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2DROP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2DROP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2DUP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2DUP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2DUP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2DUP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_3DUP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_3DUP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_3DUP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_3DUP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2OVER",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2OVER],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2OVER long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2OVER],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2ROT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2ROT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2ROT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2ROT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2SWAP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2SWAP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2SWAP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2SWAP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_IFDUP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_IFDUP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_IFDUP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_IFDUP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DEPTH",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DEPTH],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DEPTH long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DEPTH],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DROP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DROP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DROP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DROP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DUP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DUP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DUP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DUP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NIP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NIP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NIP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NIP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_OVER",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_OVER],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_OVER long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_OVER],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_PICK",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PICK],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_PICK long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PICK],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_ROLL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ROLL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_ROLL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ROLL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_ROT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ROT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_ROT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ROT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_SWAP",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SWAP],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_SWAP long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SWAP],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_TUCK",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_TUCK],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_TUCK long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_TUCK],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_CAT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CAT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_CAT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CAT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_SUBSTR",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SUBSTR],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_SUBSTR long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SUBSTR],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_LEFT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LEFT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_LEFT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LEFT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_LEFT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LEFT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_LEFT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LEFT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RIGHT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RIGHT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RIGHT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RIGHT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_SIZE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SIZE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_SIZE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SIZE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_INVERT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_INVERT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_INVERT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_INVERT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_AND",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_AND],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_AND long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_AND],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_OR",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_OR],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_OR long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_OR],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_XOR",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_XOR],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_XOR long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_XOR],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_EQUAL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_EQUAL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_EQUAL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_EQUAL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_EQUALVERIFY",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_EQUALVERIFY],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_EQUALVERIFY long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_EQUALVERIFY],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RESERVED1",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RESERVED1],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RESERVED1 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RESERVED1],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RESERVED2",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RESERVED2],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RESERVED2 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RESERVED2],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_1ADD",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_1ADD],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_1ADD long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_1ADD],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_1SUB",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_1SUB],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_1SUB long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_1SUB],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2MUL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2MUL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2MUL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2MUL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_2DIV",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2DIV],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_2DIV long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_2DIV],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NEGATE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NEGATE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NEGATE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NEGATE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_ABS",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ABS],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_ABS long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ABS],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_0NOTEQUAL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_0NOTEQUAL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_0NOTEQUAL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_0NOTEQUAL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_ADD",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ADD],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_ADD long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_ADD],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_SUB",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SUB],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_SUB long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SUB],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_MUL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MUL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_MUL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MUL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_DIV",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DIV],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_DIV long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_DIV],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_MOD",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MOD],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_MOD long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MOD],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_LSHIFT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LSHIFT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_LSHIFT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LSHIFT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RSHIFT",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RSHIFT],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RSHIFT long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RSHIFT],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_BOOLAND",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_BOOLAND],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_BOOLAND long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_BOOLAND],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_BOOLOR",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_BOOLOR],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_BOOLOR long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_BOOLOR],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NUMEQUAL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NUMEQUAL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NUMEQUAL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NUMEQUAL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NUMEQUALVERIFY",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NUMEQUALVERIFY],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NUMEQUALVERIFY long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NUMEQUALVERIFY],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NUMNOTEQUAL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NUMNOTEQUAL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NUMNOTEQUAL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NUMNOTEQUAL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_LESSTHAN",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LESSTHAN],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_LESSTHAN long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LESSTHAN],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_GREATERTHAN",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_GREATERTHAN],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_GREATERTHAN long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_GREATERTHAN],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_LESSTHANOREQUAL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LESSTHANOREQUAL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_LESSTHANOREQUAL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_LESSTHANOREQUAL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_GREATERTHANOREQUAL",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_GREATERTHANOREQUAL],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_GREATERTHANOREQUAL long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_GREATERTHANOREQUAL],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_MIN",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MIN],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_MIN long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MIN],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_MAX",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MAX],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_MAX long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_MAX],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_WITHIN",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_WITHIN],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_WITHIN long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_WITHIN],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_RIPEMD160",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RIPEMD160],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_RIPEMD160 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_RIPEMD160],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_SHA1",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SHA1],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_SHA1 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SHA1],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_SHA256",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SHA256],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_SHA256 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_SHA256],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_HASH160",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_HASH160],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_HASH160 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_HASH160],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_HASH256",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_HASH256],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_HASH256 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_HASH256],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_CODESAPERATOR",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CODESEPARATOR],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_CODESEPARATOR long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CODESEPARATOR],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_CHECKSIG",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKSIG],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_CHECKSIG long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKSIG],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_CHECKSIGVERIFY",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKSIGVERIFY],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_CHECKSIGVERIFY long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKSIGVERIFY],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_CHECKMULTISIG",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKMULTISIG],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_CHECKMULTISIG long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKMULTISIG],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_CHECKMULTISIGVERIFY",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKMULTISIGVERIFY],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_CHECKMULTISIGVERIFY long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_CHECKMULTISIGVERIFY],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP1",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP1],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP1 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP1],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP2",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP2],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP2 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP2],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP3",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP3],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP3 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP3],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP4",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP4],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP4 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP4],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP5",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP5],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP5 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP5],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP6",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP6],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP6 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP6],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP7",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP7],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP7 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP7],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP8",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP8],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP8 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP8],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP9",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP9],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP9 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP9],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_NOP10",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP10],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_NOP10 long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_NOP10],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_PUBKEYHASH",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUBKEYHASH],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_PUBKEYHASH long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUBKEYHASH],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_PUBKEY",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUBKEY],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_PUBKEY long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_PUBKEY],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },
            {
                "name": "OP_INVALIDOPCODE",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_INVALIDOPCODE],
                    data=None,
                ),
                "expected_err": None,
            },
            {
                "name": "OP_INVALIDOPCODE long",
                "pop": ParsedOpcode(
                    opcode=opcode_array[OP_INVALIDOPCODE],
                    data=bytes([0x00]),
                ),
                "expected_err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            },

        ]

        for c in tests:
            if c['expected_err']:
                with self.assertRaises(ScriptError) as cm:
                    c['pop'].bytes()
                self.assertEqual(cm.exception.c, c['expected_err'].c)
            else:
                c['pop'].bytes()
