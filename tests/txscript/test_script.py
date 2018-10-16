import unittest
import copy
import wire
from txscript.script import *
from txscript.utils import *
from txscript.script_builder import *
from tests.txscript.test_script_num import hex_to_bytes
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


class TestGetWitnessSigOpCount(unittest.TestCase):
    def test_get_witness_sig_op_count(self):
        # TOADD parallel

        tests = [
            # A regualr p2wkh witness program. The output being spent
            # should only have a single sig-op counted.
            {
                "name": "p2wkh",
                "sigScript": bytes(),
                "pkScript": must_parse_short_form("OP_0 DATA_20 0x365ab47888e150ff46f8d51bce36dcd680f1283f"),
                "witness": wire.TxWitness(data=[
                    hex_to_bytes("3045022100ee9fe8f9487afa977" + "6647ebcf0883ce0cd37454d7ce19889d34ba2c9" + \
                                 "9ce5a9f402200341cb469d0efd3955acb9e46" + "f568d7e2cc10f9084aaff94ced6dc50a59134ad01"),
                    hex_to_bytes("03f0000d0639a22bfaf217e4c9428" + "9c2b0cc7fa1036f7fd5d9f61a9d6ec153100e")
                ]),
                "numSigOps": 1
            },

            # A p2wkh witness program nested within a p2sh output script.
            # The pattern should be recognized properly and attribute only
            # a single sig op.
            {
                "name": "nested p2sh",
                "sigScript": hex_to_bytes("160014ad0ffa2e387f07e7ead14dc56d5a97dbd6ff5a23"),
                "pkScript": must_parse_short_form("HASH160 DATA_20 0xb3a84b564602a9d68b4c9f19c2ea61458ff7826c EQUAL"),
                "witness": wire.TxWitness([
                    hex_to_bytes("3045022100cb1c2ac1ff1d57d" + "db98f7bdead905f8bf5bcc8641b029ce8eef25" + \
                                 "c75a9e22a4702203be621b5c86b771288706be5" + "a7eee1db4fceabf9afb7583c1cc6ee3f8297b21201"),
                    hex_to_bytes("03f0000d0639a22bfaf217e4c9" + "4289c2b0cc7fa1036f7fd5d9f61a9d6ec153100e")
                ]),
                "numSigOps": 1
            },

            # A p2sh script that spends a 2-of-2 multi-sig output.
            {
                "name": "p2wsh multi-sig spend",
                "sigScript": bytes(),
                "pkScript": hex_to_bytes("0020e112b88a0cd87ba387f" + "449d443ee2596eb353beb1f0351ab2cba8909d875db23"),
                "witness": wire.TxWitness([
                    hex_to_bytes("522103b05faca7ceda92b493" + "3f7acdf874a93de0dc7edc461832031cd69cbb1d1e" +
                                 "6fae2102e39092e031c1621c902e3704424e8d8" + "3ca481d4d4eeae1b7970f51c78231207e52ae")
                ]),
                "numSigOps": 2

            },

            # A p2wsh witness program. However, the witness script fails
            # to parse after the valid portion of the script. As a result,
            # the valid portion of the script should still be counted.
            {
                "name": "witness script doesn't parse",
                "sigScript": bytes(),
                "pkScript": hex_to_bytes("0020e112b88a0cd87ba387f44" + "9d443ee2596eb353beb1f0351ab2cba8909d875db23"),
                "witness": wire.TxWitness([
                    must_parse_short_form(
                        "DUP HASH160 '17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem' EQUALVERIFY CHECKSIG DATA_20 0x91")
                ]),
                "numSigOps": 1

            }

        ]

        for test in tests:
            count = get_witness_sig_op_count(test["sigScript"], test["pkScript"], test["witness"])
            self.assertEqual(count, test["numSigOps"])


class TestRemoveOpcodes(unittest.TestCase):
    def test_remove_opcode(self):
        tests = [
            # Nothing to remove.
            {
                "name": "nothing to remove",
                "before": "NOP",
                "remove": OP_CODESEPARATOR,
                "after": "NOP",
                "err": None
            },

            # Test basic opcode removal
            {
                "name": "codeseparator 1",
                "before": "NOP CODESEPARATOR TRUE",
                "remove": OP_CODESEPARATOR,
                "after": "NOP TRUE",
                "err": None
            },

            # The opcode in question is actually part of the data
            # in a previous opcode.
            {
                "name": "codeseparator by coincidence",
                "before": "NOP DATA_1 CODESEPARATOR TRUE",
                "remove": OP_CODESEPARATOR,
                "after": "NOP DATA_1 CODESEPARATOR TRUE",
                "err": None
            },

            {
                "name": "invalid opcode",
                "before": "CAT",
                "remove": OP_CODESEPARATOR,
                "after": "CAT",
                "err": None
            },

            {
                "name": "invalid length (instruction)",
                "before": "PUSHDATA1",
                "remove": OP_CODESEPARATOR,
                "after": None,
                "err": ScriptError(ErrorCode.ErrMalformedPush)
            },

            {
                "name": "invalid length (data)",
                "before": "PUSHDATA1 0xff 0xfe",
                "remove": OP_CODESEPARATOR,
                "after": None,
                "err": ScriptError(ErrorCode.ErrMalformedPush)
            },

        ]

        def tstRemoveOpcode(script, opcode):
            pops = parse_script(script)
            pops = remove_opcode(pops, opcode)
            return unparse_script(pops)

        for test in tests:
            before = must_parse_short_form(test['before'])
            after = must_parse_short_form(test['after'])

            if test['err']:
                with self.assertRaises(type(test['err'])) as cm:
                    tstRemoveOpcode(before, test['remove'])
                self.assertEqual(cm.exception.c, test['err'].c)

            else:
                result = tstRemoveOpcode(before, test['remove'])
                self.assertEqual(result, after)
