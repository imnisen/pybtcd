import unittest
import wire
import chainhash
import blockchain
import btcutil
from mining.policy import *
from tests.utils import *


# newUtxoViewpoint returns a new utxo view populated with outputs of the
# provided source transactions as if there were available at the respective
# block height specified in the heights slice.  The length of the source txns
# and source tx heights must match or it will panic.
def new_utxo_viewpoint(source_txns: [wire.MsgTx], source_tx_heights: [int]) -> blockchain.UtxoViewpoint:
    if len(source_txns) != len(source_tx_heights):
        raise Exception("each transaction must have its block height specified")
    view = blockchain.UtxoViewpoint()
    for i in range(len(source_txns)):
        view.add_tx_outs(btcutil.Tx.from_msg_tx(source_txns[i]), source_tx_heights[i])
    return view


class TestPolicy(unittest.TestCase):

    # TestCalcPriority ensures the priority calculations work as intended.
    def test_calc_priority(self):
        # commonSourceTx1 is a valid transaction used in the tests below as an
        # input to transactions that are having their priority calculated.
        #
        # From block 7 in main blockchain.
        # tx 0437cd7f8525ceed2324359c2d0ba26006d92d856a9c20fa0241106ee5a597c9
        common_source_tx1 = wire.MsgTx(
            version=1,
            tx_ins=[
                wire.TxIn(
                    previous_out_point=wire.OutPoint(
                        hash=chainhash.Hash(),
                        index=wire.MaxPrevOutIndex
                    ),
                    signature_script=hex_to_bytes("04ffff001d0134"),
                    sequence=0xffffffff
                ),
            ],
            tx_outs=[
                wire.TxOut(
                    value=5000000000,
                    pk_script=hex_to_bytes("410411db93e1dcdb8a016b49840f8c5" +
                                           "3bc1eb68a382e97b1482ecad7b148a6909a5cb2e0ead" +
                                           "dfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8" +
                                           "643f656b412a3ac")
                )
            ],
            lock_time=0
        )

        # commonRedeemTx1 is a valid transaction used in the tests below as the
        # transaction to calculate the priority for.
        #
        # It originally came from block 170 in main blockchain.
        common_redeem_tx1 = wire.MsgTx(
            version=1,
            tx_ins=[
                wire.TxIn(
                    previous_out_point=wire.OutPoint(
                        hash=chainhash.Hash("0437cd7f8525ceed232435" +
                                            "9c2d0ba26006d92d856a9c20fa0241106ee5" +
                                            "a597c9"),
                        index=0
                    ),
                    signature_script=hex_to_bytes("47304402204e45e16932b8af" +
                                                  "514961a1d3a1a25fdf3f4f7732e9d624c6c61548ab5f" +
                                                  "b8cd410220181522ec8eca07de4860a4acdd12909d83" +
                                                  "1cc56cbbac4622082221a8768d1d0901"),
                    sequence=0xffffffff
                ),
            ],
            tx_outs=[
                wire.TxOut(
                    value=1000000000,
                    pk_script=hex_to_bytes("4104ae1a62fe09c5f51b13905f07f06" +
                                           "b99a2f7159b2225f374cd378d71302fa28414e7aab37" +
                                           "397f554a7df5f142c21c1b7303b8a0626f1baded5c72" +
                                           "a704f7e6cd84cac")
                ),
                wire.TxOut(
                    value=4000000000,
                    pk_script=hex_to_bytes("410411db93e1dcdb8a016b49840f8c5" +
                                           "3bc1eb68a382e97b1482ecad7b148a6909a5cb2e0ead" +
                                           "dfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8" +
                                           "643f656b412a3ac")
                ),

            ],
            lock_time=0
        )

        tests = [
            {
                "name": "one height 7 input, prio tx height 169",
                "tx": common_redeem_tx1,
                "utxo_view": new_utxo_viewpoint([common_source_tx1], [7]),
                "next_height": 169,
                "want": 5e9
            },

            {
                "name": "one height 100 input, prio tx height 169",
                "tx": common_redeem_tx1,
                "utxo_view": new_utxo_viewpoint([common_source_tx1], [100]),
                "next_height": 169,
                "want": 2129629629.6296296
            },

            {
                "name": "one height 7 input, prio tx height 100000",
                "tx": common_redeem_tx1,
                "utxo_view": new_utxo_viewpoint([common_source_tx1], [7]),
                "next_height": 100000,
                "want": 3086203703703.7036
            },

            {
                "name": "one height 100 input, prio tx height 100000",
                "tx": common_redeem_tx1,
                "utxo_view": new_utxo_viewpoint([common_source_tx1], [100]),
                "next_height": 100000,
                "want": 3083333333333.3335
            },

        ]

        for test in tests:
            got = calc_priority(test['tx'], test['utxo_view'], test['next_height'])
            self.assertEqual(got, test['want'])
