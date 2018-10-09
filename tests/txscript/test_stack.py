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
        tests = []

    def test_push_bool(self):
        tests = []

    def test_pop_byte_array(self):

        tests = [
            {
                "name": "pop",
                "before": [bytes([1]), bytes([2]), bytes([3]), bytes([4]), bytes([5])],
                "err": None,
                "value": bytes([5]),
                "after": [bytes([1]), bytes([2]), bytes([3]), bytes([4])],
            }
        ]

        for test in tests:
            if test['err']:
                pass
            else:
                stack = _new_stack(test['before'])
                self.assertEqual(stack.pop_byte_array(), test['value'])
                self.assertEqual(stack.stk, test['after'])

    def test_pop_int(self):
        tests = []

    def test_pop_bool(self):
        tests = []

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
                "name": "peek underflow (int)",
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
                    stack.peek_int(test['idx'])
                self.assertEqual(cm.exception.c, test['err'].c)
            else:
                pass

    def test_peek_bool(self):
        tests = [
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
                pass

    def test_nipN(self):
        tests = []

    def test_NipN(self):
        tests = []

    def test_tuck(self):
        tests = []

    def test_dropN(self):
        tests = []

    def test_dupN(self):
        tests = []

    def test_rotN(self):
        tests = []

    def test_swapN(self):
        tests = []

    def test_overN(self):
        tests = []

    def test_pickN(self):
        tests = []

    def test_rollN(self):
        tests = []

    def test_str(self):
        tests = []

    def test_from_bool(self):
        tests = []

    def test_as_bool(self):
        tests = []
