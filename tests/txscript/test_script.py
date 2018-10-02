import unittest
import copy
from txscript.script import *
from txscript.utils import *


class TestParseOpcode(unittest.TestCase):
    def setUp(self):

        # TOADD Add tests for parse
        self.tests = [
            {
                "script": bytes([
                    OP_0
                ]),
                "opcodes": opcode_array,
                "out": [ParsedOpcode(opcode=OpCode(value=0x00,
                                                   name="OP_0",
                                                   length=1,
                                                   opfunc=opcodeFalse),
                                     data=bytes())]
            },

            {
                "script": bytes([
                    OP_2, OP_DUP, OP_1ADD
                ]),
                "opcodes": opcode_array,
                "out": [
                    ParsedOpcode(opcode=OpCode(value=0x52,
                                               name="OP_2",
                                               length=1,
                                               opfunc=opcodeN),
                                 data=bytes()),
                    ParsedOpcode(opcode=OpCode(value=0x76,
                                               name="OP_DUP",
                                               length=1,
                                               opfunc=opcodeDup),
                                 data=bytes()),
                    ParsedOpcode(opcode=OpCode(value=0x8b,
                                               name="OP_1ADD",
                                               length=1,
                                               opfunc=opcode1Add),
                                 data=bytes())
                ]
            },

            {
                "script": bytes([
                    OP_DATA_3, 0x01, 0x02, 0x03
                ]),
                "opcodes": opcode_array,
                "out": [
                    ParsedOpcode(opcode=OpCode(value=0x03,
                                               name="OP_DATA_3",
                                               length=4,
                                               opfunc=opcodePushData),
                                 data=bytes([0x01, 0x02, 0x03])),

                ]
            },

            {
                "script": bytes([
                    OP_PUSHDATA2, 0x03, 0x00, 0x03, 0x04, 0x05
                ]),
                "opcodes": opcode_array,
                "out": [
                    ParsedOpcode(opcode=OpCode(value=0x4d,
                                               name="OP_PUSHDATA2",
                                               length=-2,
                                               opfunc=opcodePushData),
                                 data=bytes([0x03, 0x04, 0x05])),

                ]
            },

        ]

        fake_array = copy.deepcopy(opcode_array)
        fake_array[OP_PUSHDATA4] = OpCode(value=OP_PUSHDATA4,
                                          name="OP_PUSHDATA4",
                                          length=-8,
                                          opfunc=opcodePushData)

        self.err_tests = [
            {
                "script": bytes([
                    OP_PUSHDATA4, 0x1, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00
                ]),
                "opcodes": fake_array,
                "err": ScriptError
            }
        ]

    def test_parse_script_template(self):
        for c in self.tests:
            out = parse_script_template(c['script'], c['opcodes'])
            self.assertTrue(list_equal(out, c['out']))

        for c in self.err_tests:
            with self.assertRaises(c['err']):
                parse_script_template(c['script'], c['opcodes'])


class TestUnparseScript(unittest.TestCase):
    def setUp(self):
        # TODO need to split some test of these to method bytes() method of ParsedOpcode
        self.tests = [
            {
                "name": "OP_FALSE",
                "pops": [
                    ParsedOpcode(opcode=OpCode(value=0x4d,
                                               name="OP_PUSHDATA2",
                                               length=-2,
                                               opfunc=opcodePushData),
                                 data=bytes([0x03, 0x04, 0x05])),
                ],
                "script": bytes([OP_PUSHDATA2, 0x03, 0x00, 0x03, 0x04, 0x05])
            }
        ]

        self.err_tests = [
            # {
            #     "pops": [],
            #     "err": None
            # }
        ]

    def test_unparse_script(self):

        for c in self.tests:
            self.assertEqual(unparse_script(c['pops']), c['script'])

        for c in self.err_tests:
            with self.assertRaises(c['err']):
                unparse_script(c['pops'])
