# import unittest
# from txscript.engine import *
# from wire.msg_tx import TxIn,OutPoint
#
#
# class TestBadPC(unittest.TestCase):
#     def test_bad_pc(self):
#         tests = [
#             {"script": 2, "off": 0},
#             {"script": 0, "off": 2},
#         ]
#
#         tx = MsgTx(version=1,
#                    tx_ins=[
#                        TxIn(
#                            previous_out_point=OutPoint(
#                                hash=Hash(bytes([
#                                    0xc9, 0x97, 0xa5, 0xe5,
#                                     0x6e, 0x10, 0x41, 0x02,
#                                     0xfa, 0x20, 0x9c, 0x6a,
#                                     0x85, 0x2d, 0xd9, 0x06,
#                                     0x60, 0xa2, 0x0b, 0x2d,
#                                     0x9c, 0x35, 0x24, 0x23,
#                                     0xed, 0xce, 0x25, 0x85,
#                                     0x7f, 0xcd, 0x37, 0x04,
#                                ])),
#                                index=0
#                        ),
#                            signature_script=
#
#                        )
#                    ])