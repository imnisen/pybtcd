import unittest
from txscript.engine import *
from tests.txscript.test_reference import *


def must_parse_short_form(script: str):
    return parse_short_form(script)


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
        pkScript = must_parse_short_form("NOP NOP NOP NOP NOP NOP NOP NOP NOP NOP TRUE" )
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





















