import unittest
from txscript.engine import *
from tests.txscript.test_reference import *


def must_parse_short_form(script: str):
    return parse_short_form(script)


def hex_to_bytes(s):
    return bytes.fromhex(s)


class TestBadPC(unittest.TestCase):
    def test_bad_pc(self):
        # TOADD parallel
        tests = [
            {"script": 2, "off": 0},
            {"script": 0, "off": 2},
        ]

        tx = wire.MsgTx(version=1,
                        tx_ins=[
                            wire.TxIn(
                                previous_out_point=wire.OutPoint(
                                    hash=chainhash.Hash(bytes([
                                        0xc9, 0x97, 0xa5, 0xe5,
                                        0x6e, 0x10, 0x41, 0x02,
                                        0xfa, 0x20, 0x9c, 0x6a,
                                        0x85, 0x2d, 0xd9, 0x06,
                                        0x60, 0xa2, 0x0b, 0x2d,
                                        0x9c, 0x35, 0x24, 0x23,
                                        0xed, 0xce, 0x25, 0x85,
                                        0x7f, 0xcd, 0x37, 0x04,
                                    ])),
                                    index=0
                                ),
                                signature_script=must_parse_short_form("NOP"),
                                sequence=4294967295

                            )
                        ],
                        tx_outs=[
                            wire.TxOut(
                                value=1000000000,
                                pk_script=bytes()
                            )
                        ],
                        lock_time=0
                        )

        pkScript = must_parse_short_form("NOP")

        for test in tests:
            vm = new_engine(script_pub_key=pkScript,
                            tx=tx,
                            tx_idx=0,
                            flags=0,
                            sig_cache=None,
                            hash_cache=None,
                            input_amount=-1)
            vm.script_idx = test['script']
            vm.script_off = test['off']

            with self.assertRaises(ScriptError):
                vm.step()

            with self.assertRaises(ScriptError):
                vm.disasm_pc()


class TestCheckErrorCondition(unittest.TestCase):
    def test_check_error_condition(self):
        # TOADD Parallel

        tx = wire.MsgTx(version=1,
                        tx_ins=[
                            wire.TxIn(
                                previous_out_point=wire.OutPoint(
                                    hash=chainhash.Hash(bytes([
                                        0xc9, 0x97, 0xa5, 0xe5,
                                        0x6e, 0x10, 0x41, 0x02,
                                        0xfa, 0x20, 0x9c, 0x6a,
                                        0x85, 0x2d, 0xd9, 0x06,
                                        0x60, 0xa2, 0x0b, 0x2d,
                                        0x9c, 0x35, 0x24, 0x23,
                                        0xed, 0xce, 0x25, 0x85,
                                        0x7f, 0xcd, 0x37, 0x04,
                                    ])),
                                    index=0
                                ),
                                signature_script=None,
                                sequence=4294967295

                            )
                        ],
                        tx_outs=[
                            wire.TxOut(
                                value=1000000000,
                                pk_script=bytes()
                            )
                        ],
                        lock_time=0
                        )
        pkScript = must_parse_short_form("NOP NOP NOP NOP NOP NOP NOP NOP NOP NOP TRUE")
        vm = new_engine(script_pub_key=pkScript,
                        tx=tx,
                        tx_idx=0,
                        flags=0,
                        sig_cache=None,
                        hash_cache=None,
                        input_amount=-1)

        for i in range(len(pkScript) - 1):
            done = vm.step()
            self.assertEqual(done, False)

            with self.assertRaises(ScriptError) as cm:
                vm.check_error_condition(final_script=False)
            self.assertEqual(cm.exception.c, ErrorCode.ErrScriptUnfinished)

        done = vm.step()
        self.assertEqual(done, True)

        vm.check_error_condition(final_script=False)


class TestInvalidFlagCombinations(unittest.TestCase):
    def test_new_engine(self):
        # TOADD Parallel

        tests = [
            ScriptFlags(ScriptFlag.ScriptVerifyCleanStack)
        ]

        tx = tx = wire.MsgTx(version=1,
                             tx_ins=[
                                 wire.TxIn(
                                     previous_out_point=wire.OutPoint(
                                         hash=chainhash.Hash(bytes([
                                             0xc9, 0x97, 0xa5, 0xe5,
                                             0x6e, 0x10, 0x41, 0x02,
                                             0xfa, 0x20, 0x9c, 0x6a,
                                             0x85, 0x2d, 0xd9, 0x06,
                                             0x60, 0xa2, 0x0b, 0x2d,
                                             0x9c, 0x35, 0x24, 0x23,
                                             0xed, 0xce, 0x25, 0x85,
                                             0x7f, 0xcd, 0x37, 0x04,
                                         ])),
                                         index=0
                                     ),
                                     signature_script=bytes([OP_NOP]),
                                     sequence=4294967295

                                 )
                             ],
                             tx_outs=[
                                 wire.TxOut(
                                     value=1000000000,
                                     pk_script=bytes()
                                 )
                             ],
                             lock_time=0
                             )
        pkScript = bytes([OP_NOP])
        for test in tests:
            with self.assertRaises(ScriptError) as cm:
                new_engine(pkScript, tx, 0, test, sig_cache=None,
                           hash_cache=None, input_amount=-1)
            self.assertEqual(cm.exception.c, ErrorCode.ErrInvalidFlags)


class TestCheckPubKeyEncoding(unittest.TestCase):
    def test_check_pub_key_encoding(self):
        # TODOADD parallel

        tests = [
            {
                "name": "uncompressed ok",
                "key": hex_to_bytes("0411db93e1dcdb8a016b49840f8c53bc1eb68" +
                                    "a382e97b1482ecad7b148a6909a5cb2e0eaddfb84ccf" +
                                    "9744464f82e160bfa9b8b64f9d4c03f999b8643f656b" +
                                    "412a3"),
                "isValid": True,
            },
            {
                "name": "compressed ok",
                "key": hex_to_bytes("02ce0b14fb842b1ba549fdd675c98075f12e9" +
                                    "c510f8ef52bd021a9a1f4809d3b4d"),
                "isValid": True,
            },
            {
                "name": "compressed ok",
                "key": hex_to_bytes("032689c7c2dab13309fb143e0e8fe39634252" +
                                    "1887e976690b6b47f5b2a4b7d448e"),
                "isValid": True,
            },
            {
                "name": "hybrid",
                "key": hex_to_bytes("0679be667ef9dcbbac55a06295ce870b07029" +
                                    "bfcdb2dce28d959f2815b16f81798483ada7726a3c46" +
                                    "55da4fbfc0e1108a8fd17b448a68554199c47d08ffb1" +
                                    "0d4b8"),
                "isValid": False,
            },
            {
                "name": "empty",
                "key": bytes(),
                "isValid": False,
            },
        ]
        vm = Engine(flags=ScriptFlags(ScriptFlag.ScriptVerifyStrictEncoding))
        for test in tests:
            if test['isValid']:
                vm.check_pub_key_encoding(test['key'])
            else:
                with self.assertRaises(ScriptError):
                    vm.check_pub_key_encoding(test['key'])


class TestCheckSignatureEncoding(unittest.TestCase):
    def test_check_pub_key_encoding(self):
        # TODOADD parallel

        tests = [

            {
                "name": "valid signature",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": True,
            },
            {
                "name": "empty.",
                "sig": bytes(),
                "isValid": False,
            },
            {
                "name": "bad magic",
                "sig": hex_to_bytes("314402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "bad 1st int marker magic",
                "sig": hex_to_bytes("304403204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "bad 2nd int marker",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41032018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "short len",
                "sig": hex_to_bytes("304302204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "long len",
                "sig": hex_to_bytes("304502204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "long X",
                "sig": hex_to_bytes("304402424e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "long Y",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022118152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "short Y",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41021918152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "trailing crap",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d0901"),
                "isValid": False,
            },
            {
                "name": "X == N ",
                "sig": hex_to_bytes("30440220fffffffffffffffffffffffffffff" +
                                    "ffebaaedce6af48a03bbfd25e8cd0364141022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "X == N ",
                "sig": hex_to_bytes("30440220fffffffffffffffffffffffffffff" +
                                    "ffebaaedce6af48a03bbfd25e8cd0364142022018152" +
                                    "2ec8eca07de4860a4acdd12909d831cc56cbbac46220" +
                                    "82221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "Y == N",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd410220fffff" +
                                    "ffffffffffffffffffffffffffebaaedce6af48a03bb" +
                                    "fd25e8cd0364141"),
                "isValid": False,
            },
            {
                "name": "Y > N",
                "sig": hex_to_bytes("304402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd410220fffff" +
                                    "ffffffffffffffffffffffffffebaaedce6af48a03bb" +
                                    "fd25e8cd0364142"),
                "isValid": False,
            },
            {
                "name": "0 len X",
                "sig": hex_to_bytes("302402000220181522ec8eca07de4860a4acd" +
                                    "d12909d831cc56cbbac4622082221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "0 len Y",
                "sig": hex_to_bytes("302402204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd410200"),
                "isValid": False,
            },
            {
                "name": "extra R padding",
                "sig": hex_to_bytes("30450221004e45e16932b8af514961a1d3a1a" +
                                    "25fdf3f4f7732e9d624c6c61548ab5fb8cd410220181" +
                                    "522ec8eca07de4860a4acdd12909d831cc56cbbac462" +
                                    "2082221a8768d1d09"),
                "isValid": False,
            },
            {
                "name": "extra S padding",
                "sig": hex_to_bytes("304502204e45e16932b8af514961a1d3a1a25" +
                                    "fdf3f4f7732e9d624c6c61548ab5fb8cd41022100181" +
                                    "522ec8eca07de4860a4acdd12909d831cc56cbbac462" +
                                    "2082221a8768d1d09"),
                "isValid": False,
            },
        ]
        vm = Engine(flags=ScriptFlags(ScriptFlag.ScriptVerifyStrictEncoding))
        for test in tests:
            if test['isValid']:
                vm.check_signature_encoding(test['sig'])
            else:
                with self.assertRaises(ScriptError):
                    vm.check_signature_encoding(test['sig'])
