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
        # TOADD parallel

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


# TestRemoveOpcodeByData ensures that removing data carrying opcodes based on
# the data they contain works as expected.
class TestRemoveOpcodeByData(unittest.TestCase):
    def test_remove_opcode(self):
        # TOADD parallel

        tests = [
            {
                "name": "nothing to do",
                "before": bytes([OP_NOP]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([OP_NOP]),
                "err": None
            },

            {
                "name": "simple case",
                "before": bytes([OP_DATA_4, 1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes(),
                "err": None
            },

            {
                "name": "simple case (miss)",
                "before": bytes([OP_DATA_4, 1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 5]),
                "after": bytes([OP_DATA_4, 1, 2, 3, 4]),
                "err": None
            },

            # padded to keep it canonical.
            {
                "name": "simple case (pushdata1)",
                "before": bytes([OP_PUSHDATA1, 76]) + bytes([0]) * 72 + bytes([1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([]),
                "err": None
            },

            {
                "name": "simple case (pushdata1 miss)",
                "before": bytes([OP_PUSHDATA1, 76]) + bytes([0]) * 72 + bytes([1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 5]),
                "after": bytes([OP_PUSHDATA1, 76]) + bytes([0]) * 72 + bytes([1, 2, 3, 4]),
                "err": None
            },

            {
                "name": "simple case (pushdata1 miss noncanonical)",
                "before": bytes([OP_PUSHDATA1, 4, 1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([OP_PUSHDATA1, 4, 1, 2, 3, 4]),
                "err": None
            },

            {
                "name": "simple case (pushdata2)",
                "before": bytes([OP_PUSHDATA2, 0, 1]) + bytes([0]) * 252 + bytes([1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([]),
                "err": None
            },

            {
                "name": "simple case (pushdata2 miss)",
                "before": bytes([OP_PUSHDATA2, 0, 1]) + bytes([0]) * 252 + bytes([1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 5]),
                "after": bytes([OP_PUSHDATA2, 0, 1]) + bytes([0]) * 252 + bytes([1, 2, 3, 4]),
                "err": None
            },

            {
                "name": "simple case (pushdata2 miss noncanonical)",
                "before": bytes([OP_PUSHDATA2, 4, 0, 1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([OP_PUSHDATA2, 4, 0, 1, 2, 3, 4]),
                "err": None
            },

            {
                "name": "simple case (pushdata4)",
                "before": bytes([OP_PUSHDATA4, 0, 0, 1, 0]) + bytes([0]) * 65532 + bytes([1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([]),
                "err": None
            },

            {
                "name": "simple case (pushdata4 miss)",
                "before": bytes([OP_PUSHDATA4, 0, 0, 1, 0]) + bytes([0]) * 65532 + bytes([1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 5]),
                "after": bytes([OP_PUSHDATA4, 0, 0, 1, 0]) + bytes([0]) * 65532 + bytes([1, 2, 3, 4]),
                "err": None
            },

            {
                "name": "simple case (pushdata4 miss noncanonical)",
                "before": bytes([OP_PUSHDATA4, 4, 0, 0, 0, 1, 2, 3, 4]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([OP_PUSHDATA4, 4, 0, 0, 0, 1, 2, 3, 4]),
                "err": None
            },

            {
                "name": "invalid opcode ",
                "before": bytes([OP_UNKNOWN187]),
                "remove": bytes([1, 2, 3, 4]),
                "after": bytes([OP_UNKNOWN187]),
                "err": None
            },

            {
                "name": "invalid length (instruction)",
                "before": bytes([OP_PUSHDATA1]),
                "remove": bytes([1, 2, 3, 4]),
                "after": None,
                "err": ScriptError(ErrorCode.ErrMalformedPush)
            },

            {
                "name": "invalid length (data)",
                "before": bytes([OP_PUSHDATA1, 255, 254]),
                "remove": bytes([1, 2, 3, 4]),
                "after": None,
                "err": ScriptError(ErrorCode.ErrMalformedPush)
            },

        ]

        def tstRemoveOpcodeByData(script, data):
            pops = parse_script(script)
            pops = remove_opcode_by_data(pops, data)
            return unparse_script(pops)

        for test in tests:
            before = test['before']
            after = test['after']

            if test['err']:
                with self.assertRaises(type(test['err'])) as cm:
                    tstRemoveOpcodeByData(before, test['remove'])
                self.assertEqual(cm.exception.c, test['err'].c)

            else:
                result = tstRemoveOpcodeByData(before, test['remove'])
                self.assertEqual(result, after)


# scriptClassTests houses several test scripts used to ensure various class
# determination is working as expected.
class TestTypeOfScriptHash(unittest.TestCase):
    def setUp(self):
        self.scriptClassTests = [
            {
                "name": "Pay Pubkey",
                "script": "DATA_65 0x0411db93e1dcdb8a016b49840f8c53bc1eb68a382e" +
                          "97b1482ecad7b148a6909a5cb2e0eaddfb84ccf9744464f82e16" +
                          "0bfa9b8b64f9d4c03f999b8643f656b412a3 CHECKSIG",
                "class": ScriptClass.PubKeyTy
            },

            # tx 599e47a8114fe098103663029548811d2651991b62397e057f0c863c2bc9f9ea
            {
                "name": "Pay PubkeyHash",
                "script": "DUP HASH160 DATA_20 0x660d4ef3a743e3e696ad990364e555" +
                          "c271ad504b EQUALVERIFY CHECKSIG",
                "class": ScriptClass.PubKeyHashTy
            },

            # part of tx 6d36bc17e947ce00bb6f12f8e7a56a1585c5a36188ffa2b05e10b4743273a74b
            # codeseparator parts have been elided. (bitcoin core's checks for
            # multisig type doesn't have codesep either).
            {
                "name": "multisig",
                "script": "1 DATA_33 0x0232abdc893e7f0631364d7fd01cb33d24da4" +
                          "5329a00357b3a7886211ab414d55a 1 CHECKMULTISIG",
                "class": ScriptClass.MultiSigTy
            },

            # tx e5779b9e78f9650debc2893fd9636d827b26b4ddfa6a8172fe8708c924f5c39d
            {
                "name": "P2SH",
                "script": "HASH160 DATA_20 0x433ec2ac1ffa1b7b7d027f564529c57197f" +
                          "9ae88 EQUAL",
                "class": ScriptClass.ScriptHashTy
            },

            # Nulldata with no data at all.
            {
                "name": "nulldata no data",
                "script": "RETURN",
                "class": ScriptClass.NullDataTy
            },

            # Nulldata with single zero push.
            {
                "name": "nulldata zero",
                "script": "RETURN 0",
                "class": ScriptClass.NullDataTy
            },

            # Nulldata with max small integer push.
            {
                "name": "nulldata max small int",
                "script": "RETURN 16",
                "class": ScriptClass.NullDataTy
            },

            # Nulldata with small data push.
            {
                "name": "nulldata small data",
                "script": "RETURN DATA_8 0x046708afdb0fe554",
                "class": ScriptClass.NullDataTy
            },

            # Canonical nulldata with 60-byte data push.
            {
                "name": "canonical nulldata 60-byte push",
                "script": "RETURN 0x3c 0x046708afdb0fe5548271967f1a67130b7105cd" +
                          "6a828e03909a67962e0ea1f61deb649f6bc3f4cef3046708afdb" +
                          "0fe5548271967f1a67130b7105cd6a",
                "class": ScriptClass.NullDataTy
            },

            # Non-canonical nulldata with 60-byte data push.
            {
                "name": "non-canonical nulldata 60-byte push",
                "script": "RETURN PUSHDATA1 0x3c 0x046708afdb0fe5548271967f1a67" +
                          "130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef3" +
                          "046708afdb0fe5548271967f1a67130b7105cd6a",
                "class": ScriptClass.NullDataTy
            },

            # Nulldata with max allowed data to be considered standard.
            {
                "name": "nulldata max standard push",
                "script": "RETURN PUSHDATA1 0x50 0x046708afdb0fe5548271967f1a67" +
                          "130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef3" +
                          "046708afdb0fe5548271967f1a67130b7105cd6a828e03909a67" +
                          "962e0ea1f61deb649f6bc3f4cef3",
                "class": ScriptClass.NullDataTy
            },

            # Nulldata with more than max allowed data to be considered
            # standard (so therefore nonstandard)
            {
                "name": "nulldata exceed max standard push",
                "script": "RETURN PUSHDATA1 0x51 0x046708afdb0fe5548271967f1a67" +
                          "130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef3" +
                          "046708afdb0fe5548271967f1a67130b7105cd6a828e03909a67" +
                          "962e0ea1f61deb649f6bc3f4cef308",
                "class": ScriptClass.NullDataTy
            },

            # Almost nulldata, but add an additional opcode after the data
            # to make it nonstandard.
            {
                "name": "almost nulldata",
                "script": "RETURN 4 TRUE",
                "class": ScriptClass.NonStandardTy
            },

            # The next few are almost multisig (it is the more complex script type)
            # but with various changes to make it fail.

            # Multisig but invalid nsigs.
            {
                "name": "strange 1",
                "script": "DUP DATA_33 0x0232abdc893e7f0631364d7fd01cb33d24da45" +
                          "329a00357b3a7886211ab414d55a 1 CHECKMULTISIG",
                "class": ScriptClass.NonStandardTy
            },

            # Multisig but invalid pubkey.
            {
                "name": "strange 2",
                "script": "1 1 1 CHECKMULTISIG",
                "class": ScriptClass.NonStandardTy
            },

            # Multisig but no matching npubkeys opcode.
            {
                "name": "strange 3",
                "script": "1 DATA_33 0x0232abdc893e7f0631364d7fd01cb33d24da4532" +
                          "9a00357b3a7886211ab414d55a DATA_33 0x0232abdc893e7f0" +
                          "631364d7fd01cb33d24da45329a00357b3a7886211ab414d55a " +
                          "CHECKMULTISIG",
                "class": ScriptClass.NonStandardTy
            },

            # Multisig but with multisigverify.
            {
                "name": "strange 4",
                "script": "1 DATA_33 0x0232abdc893e7f0631364d7fd01cb33d24da4532" +
                          "9a00357b3a7886211ab414d55a 1 CHECKMULTISIGVERIFY",
                "class": ScriptClass.NonStandardTy
            },

            # Multisig but wrong length.
            {
                "name": "strange 5",
                "script": "1 CHECKMULTISIG",
                "class": ScriptClass.NonStandardTy
            },

            {
                "name": "doesn't parse",
                "script": "DATA_5 0x01020304",
                "class": ScriptClass.NonStandardTy
            },

            {
                "name": "multisig script with wrong number of pubkeys",
                "script": "2 " +
                          "DATA_33 " +
                          "0x027adf5df7c965a2d46203c781bd4dd8" +
                          "21f11844136f6673af7cc5a4a05cd29380 " +
                          "DATA_33 " +
                          "0x02c08f3de8ee2de9be7bd770f4c10eb0" +
                          "d6ff1dd81ee96eedd3a9d4aeaf86695e80 " +
                          "3 CHECKMULTISIG",
                "class": ScriptClass.NonStandardTy
            },

            # New standard segwit script templates.

            # A pay to witness pub key hash pk script.
            {
                "name": "Pay To Witness PubkeyHash",
                "script": "0 DATA_20 0x1d0f172a0ecb48aee1be1f2687d2963ae33f71a1",
                "class": ScriptClass.WitnessV0PubKeyHashTy
            },

            # A pay to witness scripthash pk script.
            {
                "name": "Pay To Witness Scripthash",
                "script": "0 DATA_32 0x9f96ade4b41d5433f4eda31e1738ec2b36f6e7d1420d94a6af99801a88f7f7ff",
                "class": ScriptClass.WitnessV0ScriptHashTy
            },

        ]

    def is_pay_to_script_hash(self):
        # TOADD parallel

        for test in self.scriptClassTests:
            script = must_parse_short_form(test['script'])
            self.assertEqual(is_pay_to_script_hash(script), test['class'] == ScriptClass.ScriptHashTy)

    def is_pay_to_witness_script_hash(self):
        # TOADD parallel

        for test in self.scriptClassTests:
            script = must_parse_short_form(test['script'])
            self.assertEqual(is_pay_to_witness_script_hash(script), test['class'] == ScriptClass.WitnessV0ScriptHashTy)

    def test_is_pay_to_witness_pub_key_hash(self):
        # TOADD parallel

        for test in self.scriptClassTests:
            script = must_parse_short_form(test['script'])
            self.assertEqual(is_pay_to_witness_pub_key_hash(script), test['class'] == ScriptClass.WitnessV0PubKeyHashTy)


# TestHasCanonicalPushes ensures the canonicalPush function properly determines
# what is considered a canonical push for the purposes of removeOpcodeByData.
class TestHasCanonicalPushes(unittest.TestCase):
    def test_canonical_push(self):
        # TOADD parallel

        tests = [
            {
                "name": "does not parse",
                "script": "0x046708afdb0fe5548271967f1a67130b7105cd6a82" +
                          "8e03909a67962e0ea1f61d",
                "expected": False
            },

            {
                "name": "non-canonical push",
                "script": "PUSHDATA1 0x04 0x01020304",
                "expected": False
            }
        ]

        for test in tests:
            script = must_parse_short_form(test['script'])
            try:
                pops = parse_script(script)
            except ScriptError:
                self.assertFalse(test['expected'])
            else:
                for pop in pops:
                    self.assertEqual(canonical_push(pop), test['expected'])


class TestIsPushOnlyScript(unittest.TestCase):
    def test_is_push_only_script(self):
        # TOADD parallel

        tests = [
            {
                "name": "does not parse",
                "script": must_parse_short_form("0x046708afdb0fe5548271967f1a67130" +
                                                "b7105cd6a828e03909a67962e0ea1f61d"),
                "expected": False
            },

        ]

        for test in tests:
            self.assertEqual(is_push_only_script(test['script']), test['expected'])


# TestIsUnspendable ensures the IsUnspendable function returns the expected
# results.
class TestIsUnspendable(unittest.TestCase):
    def test_is_unspendable(self):
        # TOADD parallel
        tests = [

            # Unspendable
            {
                "pkScript": bytes([0x6a, 0x04, 0x74, 0x65, 0x73, 0x74]),
                "expected": True
            },

            # Spendable
            {
                "pkScript": bytes([0x76, 0xa9, 0x14, 0x29, 0x95, 0xa0,
                                   0xfe, 0x68, 0x43, 0xfa, 0x9b, 0x95, 0x45,
                                   0x97, 0xf0, 0xdc, 0xa7, 0xa4, 0x4d, 0xf6,
                                   0xfa, 0x0b, 0x5c, 0x88, 0xac]),
                "expected": False
            }

        ]

        for test in tests:
            self.assertEqual(is_unspendabe(test['pkScript']), test['expected'])
