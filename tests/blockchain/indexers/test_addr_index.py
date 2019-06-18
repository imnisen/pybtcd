import unittest
from blockchain.indexers.addr_index import *
import copy


class AddrIndexBucket:
    def __init__(self, levels: dict):
        self.levels = levels

    def clone(self):
        return AddrIndexBucket(levels=copy.deepcopy(self.levels))

    def get(self, key):
        return self.levels[key]

    def put(self, key, value):
        self.levels[key] = value
        return

    def delete(self, key):
        del self.levels[key]
        return

    # TODO confused by the logic here. not implemted.
    # sanityCheck ensures that all data stored in the bucket for the given address
    # adheres to the level-based rules described by the address index
    # documentation.
    def sanity_check(self, addr_key, expected_total):
        pass


class TestAddrIndexLevels(unittest.TestCase):

    # TODO
    def test_put_remove_and_sanity_check(self):
        tests = [
            {
                "name": "level 0 not full",
                "numInsert": level0MaxEntries - 1,
                "key": bytes(),
            },
            {
                "name": "level 1 half",
                "numInsert": level0MaxEntries + 1,
                "key": bytes(),

            },
            {
                "name": "level 1 full",
                "numInsert": level0MaxEntries * 2 + 1,
                "key": bytes(),
            },
            {
                "name": "level 2 half, level 1 half",
                "numInsert": level0MaxEntries * 3 + 1,
                "key": bytes(),
            },
            {
                "name": "level 2 half, level 1 full",
                "numInsert": level0MaxEntries * 4 + 1,
                "key": bytes(),
            },
            {
                "name": "level 2 full, level 1 half",
                "numInsert": level0MaxEntries * 5 + 1,
                "key": bytes(),
            },
            {
                "name": "level 2 full, level 1 full",
                "numInsert": level0MaxEntries * 6 + 1,
                "key": bytes(),
            },
            {
                "name": "level 3 half, level 2 half, level 1 half",
                "numInsert": level0MaxEntries * 7 + 1,
                "key": bytes(),
            },
            {
                "name": "level 3 full, level 2 half, level 1 full",
                "numInsert": level0MaxEntries * 12 + 1,
                "key": bytes(),
            },
        ]
        pass
