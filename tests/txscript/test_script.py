import unittest
import copy
from txscript.script import *
from txscript.utils import *
from txscript.script_builder import *
from tests.txscript.test_reference import *

def must_parse_short_form(script: str):
    return parse_short_form(script)


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
        # TOADD more test case
        self.tests = [

            {
                "name": "OP_FALSE",
                "pops": [
                    ParsedOpcode(opcode=OpCode(value=OP_FALSE,
                                               name="OP_0",
                                               length=1,
                                               opfunc=opcodeFalse),
                                 data=bytes([])),
                ],
                "script": bytes([OP_FALSE])
            },
            {
                "name": "OP_PUSHDATA2",
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
            {
                "name": "OP_FALSE Err",
                "pops": [
                    ParsedOpcode(opcode=OpCode(value=OP_FALSE,
                                               name="OP_0",
                                               length=1,
                                               opfunc=opcodeFalse),
                                 data=bytes([0x00])),
                ],
                "err": ScriptError(c=ErrorCode.ErrInternal, desc=""),
            }
        ]

    def test_unparse_script(self):

        for c in self.tests:
            self.assertEqual(unparse_script(c['pops']), c['script'])

        for c in self.err_tests:
            with self.assertRaises(ScriptError) as cm:
                unparse_script(c['pops'])
            self.assertEqual(cm.exception.c, c['err'].c)


class TestCanonicalPush(unittest.TestCase):
    def test_canonical_push(self):
        for i in range(65535):
            script = ScriptBuilder().add_int64(i).script
            self.assertTrue(is_push_only_script(script))

            pops = parse_script(script)
            for pop in pops:
                self.assertTrue(canonical_push(pop))

        for i in range(MaxScriptElementSize):
            script = ScriptBuilder().add_data(bytes([0x49]) * i).script
            self.assertTrue(is_push_only_script(script))
            pops = parse_script(script)
            for pop in pops:
                self.assertTrue(canonical_push(pop))


# TestGetPreciseSigOps ensures the more precise signature operation counting
# mechanism which includes signatures in P2SH scripts works as expected.
class TestGetPreciseSigOps(unittest.TestCase):
    # TOCHECK add case that nsigOPs greater than 0
    def test_get_precise_sig_ops(self):
        tests = [
            {
                "name": "scriptSig doesn't parse",
                "scriptSig": must_parse_short_form("PUSHDATA1 0x02"),
                "nSigOps": 0
            },

            {
                "name": "scriptSig isn't push only",
                "scriptSig": must_parse_short_form("1 DUP"),
                "nSigOps": 0
            },

            {
                "name": "scriptSig length 0",
                "scriptSig": None,
                "nSigOps": 0
            },

            {
                "name": "No script at the end",
                "scriptSig": must_parse_short_form("1 1"),
                "nSigOps": 0
            },

            {
                "name": "pushed script doesn't parse",
                "scriptSig": must_parse_short_form("DATA_2 PUSHDATA1 0x02"),
                "nSigOps": 0
            },

        ]
        pkScript = must_parse_short_form("HASH160 DATA_20 0x433ec2ac1ffa1b7b7d0 27f564529c57197f9ae88 EQUAL")
        for test in tests:
            count = get_precise_sig_op_count(test['scriptSig'], pkScript, bip16=True)
            self.assertEqual(count, test['nSigOps'])


