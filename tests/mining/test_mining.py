# import unittest
# import wire
# import chainhash
# import blockchain
# import btcutil
# import random
# from mining.mining import *
# from tests.utils import *
#
#
# class TestMining(unittest.TestCase):
#     # TestTxFeePrioHeap ensures the priority queue for transaction fees and
#     # priorities works as expected.
#     def test_tx_fee_prio_heap(self):
#         # Create some fake priority items that exercise the expected sort
#         # edge conditions.
#         test_items = [
#             TxPrioItem(fee_per_kb=5678, priority=3),
#             TxPrioItem(fee_per_kb=5678, priority=3),
#             TxPrioItem(fee_per_kb=5678, priority=1),
#             TxPrioItem(fee_per_kb=5678, priority=1),  # Duplicate fee and prio
#             TxPrioItem(fee_per_kb=5678, priority=5),
#             TxPrioItem(fee_per_kb=5678, priority=2),
#             TxPrioItem(fee_per_kb=1234, priority=3),
#             TxPrioItem(fee_per_kb=1234, priority=1),
#             TxPrioItem(fee_per_kb=1234, priority=5),
#             TxPrioItem(fee_per_kb=1234, priority=5),  # Duplicate fee and prio
#             TxPrioItem(fee_per_kb=1234, priority=2),
#             TxPrioItem(fee_per_kb=10000, priority=0),  # Higher fee, smaller prio
#             TxPrioItem(fee_per_kb=0, priority=10000),  # Higher prio, lower fee
#         ]
#         # Add random data in addition to the edge conditions already manually
#         # specified.
#         for i in range(1000):
#             test_items.append(
#                 TxPrioItem(fee_per_kb=int(random.random() * btcutil.SatoshiPerBitcoin),
#                            priority=random.random() * 100),
#             )
#
#         # Test sorting by fee per KB then priority.
#         highest = None
#         priority_queue = new_tx_priority_queue(len(test_items), sort_by_fee=True)
#         for item in test_items:
#             if highest is None:
#                 highest = item
#
#             if item.fee_per_kb >= highest.fee_per_kb and \
#                     item.priority > highest.priority:
#                 highest = item
#
#             priority_queue.push(item)
#
#         for _ in range(len(test_items)):
#             item = priority_queue.pop()
#             self.assertFalse(item.fee_per_kb >= highest.fee_per_kb and item.priority > highest.priority)
#             highest = item
#
#         # Test sorting by priority then fee per KB.
#         highest = None
#         priority_queue = new_tx_priority_queue(len(test_items), sort_by_fee=False)
#         for item in test_items:
#             if highest is None:
#                 highest = item
#
#             if item.priority >= highest.priority and \
#                     item.fee_per_kb > highest.fee_per_kb:
#                 highest = item
#
#             priority_queue.push(item)
#
#         for _ in range(len(test_items)):
#             item = priority_queue.pop()
#             self.assertFalse(item.priority >= highest.priority and item.fee_per_kb > highest.fee_per_kb)
#             highest = item
