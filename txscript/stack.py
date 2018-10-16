from .script_num import *
from .error import *


class Stack:
    def __init__(self, stk=None, verify_minimal_data=None):
        """

        :param list stk:
        :param bool verify_minimal_data:
        """
        self.stk = stk or []
        self.verify_minimal_data = verify_minimal_data or False

    # Depth returns the number of items on the stack.
    def depth(self):
        return len(self.stk)

    # PushByteArray adds the given back array to the top of the stack.
    #
    # Stack transformation: [... x1 x2] -> [... x1 x2 data]
    def push_byte_array(self, so: bytes):
        self.stk.append(so)

    # PushInt converts the provided scriptNum to a suitable byte array then pushes
    # it onto the top of the stack.
    #
    # Stack transformation: [... x1 x2] -> [... x1 x2 int]
    def push_int(self, val: ScriptNum):
        # print('cool')
        # x = val.bytes()
        # self.push_byte_array(x)

        self.push_byte_array(val.bytes())

    # PushBool converts the provided boolean to a suitable byte array then pushes
    # it onto the top of the stack.
    #
    # Stack transformation: [... x1 x2] -> [... x1 x2 bool]
    def push_bool(self, val: bool):
        self.push_byte_array(from_bool(val))

    # PopByteArray pops the value off the top of the stack and returns it.
    #
    # Stack transformation: [... x1 x2 x3] -> [... x1 x2]
    def pop_byte_array(self):
        return self.nipN(idx=0)

    # PopInt pops the value off the top of the stack, converts it into a script
    # num, and returns it.  The act of converting to a script num enforces the
    # consensus rules imposed on data interpreted as numbers.
    #
    # Stack transformation: [... x1 x2 x3] -> [... x1 x2]
    def pop_int(self):
        so = self.pop_byte_array()
        return make_script_num(so, self.verify_minimal_data, defaultScriptNumLen)

    # PopBool pops the value off the top of the stack, converts it into a bool, and
    # returns it.
    #
    # Stack transformation: [... x1 x2 x3] -> [... x1 x2]
    def pop_bool(self):
        so = self.pop_byte_array()
        return as_bool(so)

    # PeekByteArray returns the Nth item on the stack without removing it.
    def peek_byte_array(self, idx: int):
        sz = len(self.stk)
        if idx < 0 or idx > sz - 1:
            desc = "index {} is invalid for stack size {}".format(idx, len(self.stk))
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)
        return self.stk[sz - idx - 1]

    # PeekInt returns the Nth item on the stack as a script num without removing
    # it.  The act of converting to a script num enforces the consensus rules
    # imposed on data interpreted as numbers.
    def peek_int(self, idx: int):
        so = self.peek_byte_array(idx)
        return make_script_num(so, self.verify_minimal_data, defaultScriptNumLen)

    # PeekBool returns the Nth item on the stack as a bool without removing it.
    def peek_bool(self, idx: int):
        so = self.peek_byte_array(idx)
        return as_bool(so)

    # nipN is an internal function that removes the nth item on the stack and
    # returns it.
    #
    # Stack transformation:
    # nipN(0): [... x1 x2 x3] -> [... x1 x2]
    # nipN(1): [... x1 x2 x3] -> [... x1 x3]
    # nipN(2): [... x1 x2 x3] -> [... x2 x3]
    def nipN(self, idx: int) -> bytes:
        if idx < 0 or idx > len(self.stk) - 1:
            desc = "index {} is invalid for stack size {}".format(idx, len(self.stk))
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)
        return self.stk.pop(-1 - idx)

    # NipN removes the Nth object on the stack
    #
    # Stack transformation:
    # NipN(0): [... x1 x2 x3] -> [... x1 x2]
    # NipN(1): [... x1 x2 x3] -> [... x1 x3]
    # NipN(2): [... x1 x2 x3] -> [... x2 x3]
    def NipN(self, idx: int):
        self.nipN(idx)
        return

    # Tuck copies the item at the top of the stack and inserts it before the 2nd
    # to top item.
    #
    # Stack transformation: [... x1 x2] -> [... x2 x1 x2]
    def tuck(self):
        so2 = self.pop_byte_array()
        so1 = self.pop_byte_array()
        self.push_byte_array(so2)
        self.push_byte_array(so1)
        self.push_byte_array(so2)

    # DropN removes the top N items from the stack.
    #
    # Stack transformation:
    # DropN(1): [... x1 x2] -> [... x1]
    # DropN(2): [... x1 x2] -> [...]
    def dropN(self, n: int):
        if n < 1:
            desc = "attempt to drop %d items from stack".format(n)
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)

        for _ in range(n):
            self.pop_byte_array()
        return

    # DupN duplicates the top N items on the stack.
    #
    # Stack transformation:
    # DupN(1): [... x1 x2] -> [... x1 x2 x2]
    # DupN(2): [... x1 x2] -> [... x1 x2 x1 x2]
    def dupN(self, n: int):
        if n < 1:
            desc = "attempt to drop %d items from stack".format(n)
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)

        for i in range(n, 0, -1):
            so = self.peek_byte_array(n - 1)
            self.push_byte_array(so)
        return

    # RotN rotates the top 3N items on the stack to the left N times.
    #
    # Stack transformation:
    # RotN(1): [... x1 x2 x3] -> [... x2 x3 x1]
    # RotN(2): [... x1 x2 x3 x4 x5 x6] -> [... x3 x4 x5 x6 x1 x2]
    def rotN(self, n: int):
        if n < 1:
            desc = "attempt to drop %d items from stack".format(n)
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)

        entry = 3 * n - 1

        for i in range(n, 0, -1):
            so = self.nipN(entry)
            self.push_byte_array(so)
        return

    # SwapN swaps the top N items on the stack with those below them.
    #
    # Stack transformation:
    # SwapN(1): [... x1 x2] -> [... x2 x1]
    # SwapN(2): [... x1 x2 x3 x4] -> [... x3 x4 x1 x2]
    def swapN(self, n: int):
        if n < 1:
            desc = "attempt to drop %d items from stack".format(n)
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)

        entry = 2 * n - 1

        for i in range(n, 0, -1):
            so = self.nipN(entry)
            self.push_byte_array(so)
        return

    # OverN copies N items N items back to the top of the stack.
    #
    # Stack transformation:
    # OverN(1): [... x1 x2 x3] -> [... x1 x2 x3 x2]
    # OverN(2): [... x1 x2 x3 x4] -> [... x1 x2 x3 x4 x1 x2]
    def overN(self, n: int):
        if n < 1:
            desc = "attempt to drop %d items from stack".format(n)
            raise ScriptError(c=ErrorCode.ErrInvalidStackOperation, desc=desc)

        entry = 2 * n - 1

        for i in range(n, 0, -1):
            so = self.peek_byte_array(entry)
            self.push_byte_array(so)
        return

    # PickN copies the item N items back in the stack to the top.
    #
    # Stack transformation:
    # PickN(0): [x1 x2 x3] -> [x1 x2 x3 x3]
    # PickN(1): [x1 x2 x3] -> [x1 x2 x3 x2]
    # PickN(2): [x1 x2 x3] -> [x1 x2 x3 x1]
    def pickN(self, n: int):
        so = self.peek_byte_array(n)
        self.push_byte_array(so)
        return

    # RollN moves the item N items back in the stack to the top.
    #
    # Stack transformation:
    # RollN(0): [x1 x2 x3] -> [x1 x2 x3]
    # RollN(1): [x1 x2 x3] -> [x1 x3 x2]
    # RollN(2): [x1 x2 x3] -> [x2 x3 x1]
    def rollN(self, n: int):
        so = self.nipN(n)
        self.push_byte_array(so)
        return

    def __str__(self):
        result = ""
        for each in self.stk:
            if len(each) == 0:
                result += "00000000  <empty>\n"
            else:
                result += each.hex()
        return result


def from_bool(v: bool) -> bytes:
    if v:
        return bytes([0x01])
    else:
        return bytes()  # TOCHCEK TODO


# asBool gets the boolean value of the byte array.
def as_bool(t: bytes) -> bool:
    for i, each in enumerate(t):
        if each != 0x00:
            if i != len(t) - 1 and each == 0x80:
                return False
            return True
    return False
