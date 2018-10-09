import unittest
from txscript.stack import *


def _new_stack(before):
    stack = Stack()
    for each in before:
        stack.push_byte_array(each)
    return stack


class TestStack(unittest.TestCase):
    def test_depth(self):
        tests = []

    def test_push_byte_array(self):
        tests = []

    def test_push_int(self):
        tests = [
            {
                "name": "PushInt 0",
                "before": [],
                "to_push": ScriptNum(0),
                "err": None,
                "after": [bytes([])]
            },

            {
                "name": "PushInt 1",
                "before": [],
                "to_push": ScriptNum(1),
                "err": None,
                "after": [bytes([0x1])]
            },

            {
                "name": "PushInt -1",
                "before": [],
                "to_push": ScriptNum(-1),
                "err": None,
                "after": [bytes([0x81])]
            },

            {
                "name": "PushInt two bytes",
                "before": [],
                "to_push": ScriptNum(256),
                "err": None,
                "after": [bytes([0x00, 0x01])]
            },

            {
                "name": "PushInt leading zeros",
                "before": [],
                "to_push": ScriptNum(128),
                "err": None,
                "after": [bytes([0x80, 0x00])]
            },

        ]

        for test in tests:
            if test['err']:
                pass
            else:
                stack = _new_stack(test['before'])
                stack.push_int(test['to_push'])
                self.assertEqual(stack.stk, test['after'])

    def test_push_bool(self):
        tests = [
            {
                "name": "PushBool true",
                "before": [],
                "err": None,
                "value": True,
                "after": [bytes([1])],
            },

            {
                "name": "PushBool false",
                "before": [],
                "err": None,
                "value": False,
                "after": [bytes([])],
            },

        ]

        for test in tests:
            if test['err']:
                pass
            else:
                stack = _new_stack(test['before'])
                stack.push_bool(test['value'])
                self.assertEqual(stack.stk, test['after'])

    def test_pop_byte_array(self):

        tests = [
            {
                "name": "pop",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "err": None,
                "value": bytes([5]),
                "after": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
            },

        ]

        for test in tests:
            if test['err']:
                pass
            else:
                stack = _new_stack(test['before'])
                self.assertEqual(stack.pop_byte_array(), test['value'])
                self.assertEqual(stack.stk, test['after'])

        multi_tests = [
            {
                "name": "pop everything",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "err": None,
                "times": 5,
                "value": [bytes([5]), bytes([4]), bytes([3]), bytes([2]), bytes([1])],
                "after": [],
            },

            {
                "name": "pop underflow",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "times": 6,
                "value": None,
                "after": [],
            },

        ]

        for test in multi_tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    for i in range(test['times']):
                        stack.pop_byte_array()
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                for i in range(test['times']):
                    self.assertEqual(stack.pop_byte_array(), test['value'][i])
                self.assertEqual(stack.stk, test['after'])

    def test_pop_int(self):
        tests = [
            {
                "name": "popInt 0",
                "before": [bytes([0x0])],
                "err": None,
                "value": 0,
                "after": [],
            },

            {
                "name": "popInt -0",
                "before": [bytes([0x80])],
                "err": None,
                "value": 0,
                "after": [],
            },

            {
                "name": "popInt 1",
                "before": [bytes([0x01])],
                "err": None,
                "value": 1,
                "after": [],
            },

            {
                "name": "popInt 1 leading 0",
                "before": [bytes([0x01, 0x00, 0x00, 0x00])],
                "err": None,
                "value": 1,
                "after": [],
            },

            {
                "name": "popInt -1",
                "before": [bytes([0x81])],
                "err": None,
                "value": -1,
                "after": [],
            },

            {
                "name": "popInt -1 leading 0",
                "before": [bytes([0x01, 0x00, 0x00, 0x80])],
                "err": None,
                "value": -1,
                "after": [],
            },

            {
                "name": "popInt -513",
                "before": [bytes([0x1, 0x82])],
                "err": None,
                "value": -513,
                "after": [],
            },

            {
                "name": "popInt empty ",
                "before": [],
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "value": None,
                "after": None,
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.pop_int()
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                self.assertEqual(stack.pop_int(), test['value'])
                self.assertEqual(stack.stk, test['after'])

    def test_pop_bool(self):
        tests = [
            {
                "name": "pop bool",
                "before": [bytes([])],
                "err": None,
                "value": False,
                "after": [],
            },

            {
                "name": "pop bool",
                "before": [bytes([1])],
                "err": None,
                "value": True,
                "after": [],
            },

            {
                "name": "pop bool",
                "before": [],
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "value": True,
                "after": None,
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.pop_bool()
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                self.assertEqual(stack.pop_bool(), test['value'])
                self.assertEqual(stack.stk, test['after'])

    def test_peek_byte_array(self):
        tests = [
            {
                "name": "peek underflow (byte)",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "idx": 5,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            }

        ]

        for test in tests:
            if test['err']:
                with self.assertRaises(ScriptError) as cm:
                    stack = _new_stack(test['before'])
                    stack.peek_byte_array(test['idx'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                pass

    def test_peek_int(self):
        tests = [
            {
                "name": "Peek int",
                "before": [bytes([1])],
                "idx": 0,
                "err": None,
                "value": 1,
                "after": [bytes([1])]
            },

            {
                "name": "Peek int 2",
                "before": [bytes([0])],
                "idx": 0,
                "err": None,
                "value": 0,
                "after": [bytes([0])]
            },

            {
                "name": "peekint nomodify -1",
                "before": [bytes([0x01, 0x00, 0x00, 0x80])],
                "idx": 0,
                "err": None,
                "value": -1,
                "after": [bytes([0x01, 0x00, 0x00, 0x80])]
            },

            {
                "name": "peek underflow (int)",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "idx": 5,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                with self.assertRaises(ScriptError) as cm:
                    stack = _new_stack(test['before'])
                    stack.peek_int(test['idx'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                self.assertEqual(stack.peek_int(test['idx']), test['value'])
                self.assertEqual(stack.stk, test['after'])

    def test_peek_bool(self):
        tests = [
            {
                "name": "Peek bool",
                "before": [bytes([1])],
                "idx": 0,
                "err": None,
                "value": True,
                "after": [bytes([1])]
            },

            {
                "name": "Peek bool 2",
                "before": [bytes([])],
                "idx": 0,
                "err": None,
                "value": False,
                "after": [bytes([])]
            },

            {
                "name": "peek underflow (bool)",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "idx": 5,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            }
        ]

        for test in tests:
            if test['err']:
                with self.assertRaises(ScriptError) as cm:
                    stack = _new_stack(test['before'])
                    stack.peek_bool(test['idx'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                self.assertEqual(stack.peek_bool(test['idx']), test['value'])
                self.assertEqual(stack.stk, test['after'])

    def test_nipN(self):
        pass

    def test_NipN(self):
        tests = [
            {
                "name": "Nip top",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 0,
                "err": None,
                "after": [bytes([1]), bytes([2])]
            },

            {
                "name": "Nip middle",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([3])]
            },

            {
                "name": "Nip low",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 2,
                "err": None,
                "after": [bytes([2]), bytes([3])]
            },

            {
                "name": "Nip too much",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 3,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },
        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.NipN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.NipN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_tuck(self):
        tests = [
            {
                "name": "keep on tucking",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "err": None,
                "after": [bytes([1]), bytes([3]), bytes([2]), bytes([3])]
            },

            {
                "name": "a little tucked up",
                "before": [bytes([1])],
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "all tucked up",
                "before": [],
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.tuck()
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.tuck()
                self.assertEqual(stack.stk, test['after'])

    def test_dropN(self):
        tests = [
            {
                "name": "drop 1",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([3])]
            },

            {
                "name": "drop 2",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 2,
                "err": None,
                "after": [bytes([1]), bytes([2])]
            },

            {
                "name": "drop 3",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 3,
                "err": None,
                "after": [bytes([1])]
            },

            {
                "name": "drop 4",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 4,
                "err": None,
                "after": []
            },

            {
                "name": "drop 4/5",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 5,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "drop invalid",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 0,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.dropN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.dropN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_dupN(self):
        tests = [

            {
                "name": "dup",
                "before": [bytes([0x1])],
                "n": 1,
                "err": None,
                "after": [bytes([0x1]), bytes([0x1])]
            },

            {
                "name": "dup2",
                "before": [bytes([0x1]), bytes([0x2])],
                "n": 2,
                "err": None,
                "after": [bytes([0x1]), bytes([0x2]), bytes([0x1]), bytes([0x2])]
            },

            {
                "name": "dup3",
                "before": [bytes([0x1]), bytes([0x2]), bytes([0x3])],
                "n": 3,
                "err": None,
                "after": [bytes([0x1]), bytes([0x2]), bytes([0x3]), bytes([0x1]), bytes([0x2]), bytes([0x3])]
            },

            {
                "name": "dup0",
                "before": [bytes([0x1])],
                "n": 0,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "dup-1",
                "before": [bytes([0x1])],
                "n": -1,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "dup too much",
                "before": [bytes([0x1])],
                "n": 2,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.dupN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.dupN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_rotN(self):
        tests = [
            {
                "name": "Rot1",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([3]), bytes([4]), bytes([2])]
            },

            {
                "name": "Rot2",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5]), bytes([6])],
                "n": 2,
                "err": None,
                "after": [bytes([3]), bytes([4]), bytes([5]), bytes([6]), bytes([1]), bytes([2])]
            },

            {
                "name": "Rot too little",
                "before": [bytes([1]), bytes([2])],
                "n": 1,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "Rot0",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 0,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.rotN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.rotN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_swapN(self):
        tests = [
            {
                "name": "Swap1",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([4]), bytes([3])]
            },

            {
                "name": "Swap2",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 2,
                "err": None,
                "after": [bytes([3]), bytes([4]), bytes([1]), bytes([2])]
            },

            {
                "name": "Swap too little",
                "before": [bytes([1])],
                "n": 1,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "Swap0",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 0,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.swapN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.swapN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_overN(self):
        tests = [
            {
                "name": "Over1",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([3])]
            },

            {
                "name": "Over2",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 2,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([1]), bytes([2])]
            },

            {
                "name": "Over too little",
                "before": [bytes([1])],
                "n": 1,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

            {
                "name": "Over0",
                "before": [bytes([1]), bytes([2]), bytes([3])],
                "n": 0,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },

        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.overN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.overN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_pickN(self):
        tests = [
            {
                "name": "Pick1",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([3])]
            },

            {
                "name": "Pick2",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 2,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([2])]
            },

            {
                "name": "Pick too little",
                "before": [bytes([1])],
                "n": 1,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },
        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.pickN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.pickN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_rollN(self):
        tests = [
            {
                "name": "Roll1",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 1,
                "err": None,
                "after": [bytes([1]), bytes([2]), bytes([4]), bytes([3])]
            },

            {
                "name": "Roll2",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
                "n": 2,
                "err": None,
                "after": [bytes([1]), bytes([3]), bytes([4]), bytes([2])]
            },

            {
                "name": "Roll too little",
                "before": [bytes([1])],
                "n": 1,
                "err": ScriptError(ErrorCode.ErrInvalidStackOperation),
                "after": None
            },
        ]

        for test in tests:
            if test['err']:
                stack = _new_stack(test['before'])
                with self.assertRaises(ScriptError) as cm:
                    stack.rollN(test['n'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                stack = _new_stack(test['before'])
                stack.rollN(test['n'])
                self.assertEqual(stack.stk, test['after'])

    def test_str(self):
        pass

    def test_from_bool(self):
        pass

    def test_as_bool(self):
        pass

    # TOADD
    def test_union_operation(self):
        pass
