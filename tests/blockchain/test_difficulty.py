import unittest
from blockchain.difficulty import *


class TestDifficulty(unittest.TestCase):
    def test_big_to_compact_to_big(self):
        tests = [
            {"big": 0, "compact": 0, "to_big": 0},
            {"big": -1, "compact": 25231360, "to_big": -1},

            {"big": 100, "compact": 23330816, "to_big": 100},
            {"big": -100, "compact": 31719424, "to_big": -100},

            {"big": 255, "compact": 33619712, "to_big": 255},
            {"big": -255, "compact": 42008320, "to_big": -255},

            {"big": 65538, "compact": 50397186, "to_big": 65538},
            {"big": -65538, "compact": 58785794, "to_big": -65538},

            {"big": 6553800, "compact": 56885448, "to_big": 6553800},
            {"big": -6553800, "compact": 65274056, "to_big": -6553800},

            {"big": 8388607, "compact": 58720255, "to_big": 8388607},
            {"big": -8388607, "compact": 67108863, "to_big": -8388607},

            {"big": 10000000, "compact": 67147926, "to_big": 9999872},
            {"big": -10000000, "compact": 75536534, "to_big": -9999872},

        ]
        for test in tests:
            self.assertEqual(big_to_compact(test['big']), test['compact'])
            self.assertEqual(compact_to_big(test['compact']), test['to_big'])

    def test_calc_work(self):
        tests = [
            {"in": 10000000, 'out': 0},
            {"in": 25231360, 'out': 0},
            {"in": 56885448, 'out': 17667928769475331250303600156411204406918974907178378476773643875960397},
            {"in": 67147926, 'out': 11579355981552585260189902912635781259748997278829497538564498169918070}
        ]
        for test in tests:
            self.assertEqual(calc_work(test['in']), test['out'])
