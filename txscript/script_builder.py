from .engine import *


# TOCHANGE Consider to make the err pass to raise

def canonical_data_size(data) -> int:
    """
    canonical data push rules:

    DataLen: 0
    Use: OP_0
    ==============================================================================================================
    DataLen: 1 (0x00 -> 0xff)
    Value: 0x00...0x10(16),    0x11  ->  0xff              [one exception:0x81]
    Use:   OP_1...OP_16,        OP_DATA_1                 [Use :OP_1NEGATE]
    ==============================================================================================================

    DataLen: 2bytes,   ...  , 75bytes,      76bytes - 0xffbytes,  0xff01bytes-0xffffbytes,  0xffff01-...
    Value:
    Use:     OP_DATA_2, ... , OP_DATA_75,       OP_PUSHDATA1    ,       OP_PUSHDATA2      ,  OP_PUSHDATA4


    :param bytes data:
    :return:
    """
    data_len = len(data)
    # When the data consists of a single number that can be represented
    # by one of the "small integer" opcodes, that opcode will be instead
    # of a data push opcode followed by the number.
    if data_len == 0:  # Empty bytes, Use `OP_0 or op_FLASE`
        return 1
    elif data_len == 1 and data[0] <= 16:  # One byte, 0x00-0x10 we can use `OP_0-OP16` to represent to push
        return 1
    elif data_len == 1 and data[0] == 0x81:  # One byte, 0x81(-1), as -1 we have `OP_1NEGATE` to represent to push
        return 1

    if data_len < OP_PUSHDATA1:  # 0x11 - 0x4b(OP_PUSHDATA1-1), use `OP_DATA_1-OP_DATA75 `+(1-75) bytes of data to push
        return 1 + data_len
    elif data_len <= 0xff:  # 0x4c-0xff(except 0x81), use `OP_PUSHDATA1` + one byte + data to push
        return 2 + data_len
    elif data_len <= 0xffff:  # 0xff+1 - 0xffffuse `OP_PUSHDATA2` + two bytes + data to push
        return 3 + data_len

    return 5 + data_len  # Otherwise , use `OP_PUSHDATA4` + four bytes + data to push data


class ErrScriptNotCanonical(BaseException):
    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        return self.msg


# ScriptBuilder provides a facility for building custom scripts.  It allows
# you to push opcodes, ints, and data while respecting canonical encoding.  In
# general it does not ensure the script will execute correctly, however any
# data pushes which would exceed the maximum allowed script engine limits and
# are therefore guaranteed not to execute will not be pushed and will result in
# the Script function returning an error.
#
# For example, the following would build a 2-of-3 multisig script for usage in
# a pay-to-script-hash (although in this situation MultiSigScript() would be a
# better choice to generate the script):
# 	builder := txscript.NewScriptBuilder()
# 	builder.AddOp(txscript.OP_2).AddData(pubKey1).AddData(pubKey2)
# 	builder.AddData(pubKey3).AddOp(txscript.OP_3)
# 	builder.AddOp(txscript.OP_CHECKMULTISIG)
# 	script, err := builder.Script()
# 	if err != nil {
# 		# Handle the error.
# 		return
# 	}
# 	fmt.Printf("Final multi-sig script: %x\n", script)
class ScriptBuilder:
    def __init__(self, script=None, err=None):
        """

        :param bytes script:
        # :param ErrScriptNotCanonical err:
        """
        self.script = script or bytes()
        # self.err = err

    # AddOp pushes the passed opcode to the end of the script.  The script will not
    # be modified if pushing the opcode would cause the script to exceed the
    # maximum allowed script engine size.
    def add_op(self, opcode):
        """

        :param byte opcode:
        :return:
        """
        # if self.err:
        #     return self

        if len(self.script) + 1 > MaxScriptSize:
            msg = "adding an opcode would exceed the maximum allowed canonical script length of %d" % MaxScriptSize
            raise ErrScriptNotCanonical(msg)
            # self.err = ErrScriptNotCanonical(msg)
            # return self

        self.script += opcode

    # AddOps pushes the passed opcode to the end of the script.  The script will not
    # be modified if pushing the opcode would cause the script to exceed the
    # maximum allowed script engine size.
    def add_ops(self, opcodes):
        """

        :param bytes opcodes:
        :return:
        """
        # if self.err:
        #     return self

        if len(self.script) + 1 > MaxScriptSize:
            msg = "adding an opcode would exceed the maximum allowed canonical script length of %d" % MaxScriptSize
            raise ErrScriptNotCanonical(msg)
            # self.err = ErrScriptNotCanonical(msg)
            # return self

        self.script += opcodes

    # _add_data is the internal function that actually pushes the passed data to the
    # end of the script.  It automatically chooses canonical opcodes depending on
    # the length of the data.  A zero length buffer will lead to a push of empty
    # data onto the stack (OP_0).  No data limits are enforced with this function.
    def _add_data(self, data: bytes):
        data_len = len(data)

        # When the data consists of a single number that can be represented
        # by one of the "small integer" opcodes, use that opcode instead of
        # a data push opcode followed by the number.

        if data_len == 0 or (data_len == 1 and data[0] == 0):
            self.script += bytes([OP_0])
            return self
        elif data_len == 1 and data[0] <= 16:
            self.script += bytes([(OP_1 - 1 + data[0])])  # Use OP_1 - OP_16
            return self
        elif data_len == 1 and data[0] == 0x81:
            self.script += bytes([OP_1NEGATE])  # use OP_1NEGATE to represent -1
            return self
        else:
            pass

        # Use one of the OP_DATA_# opcodes if the length of the data is small
        # enough so the data push instruction is only a single byte.
        # Otherwise, choose the smallest possible OP_PUSHDATA# opcode that
        # can represent the length of the data.
        if data_len < OP_PUSHDATA1:
            self.script += bytes([OP_DATA_1 - 1 + data_len])  # Use OP_DATA_1 - OP_DATA_16
            self.script += data  # push actual data
        elif data_len <= 0xff:
            self.script += bytes([OP_PUSHDATA1])  # Use OP_PUSHDATA1
            self.script += data_len.to_bytes(1, "little")
            self.script += data
        elif data_len <= 0xffff:
            self.script += bytes([OP_PUSHDATA2])  # Use OP_PUSHDATA1
            self.script += data_len.to_bytes(2, "little")
            self.script += data
        else:
            self.script += bytes([OP_PUSHDATA4])  # Use OP_PUSHDATA4
            self.script += data_len.to_bytes(4, "little")
            self.script += data
        return self

    # add_full_data should not typically be used by ordinary users as it does not
    # include the checks which prevent data pushes larger than the maximum allowed
    # sizes which leads to scripts that can't be executed.  This is provided for
    # testing purposes such as regression tests where sizes are intentionally made
    # larger than allowed.
    #
    # Use add_data instead.
    def add_full_data(self, data: bytes):
        # if self.err:
        #     return self
        return self._add_data(data)

    # AddData pushes the passed data to the end of the script.  It automatically
    # chooses canonical opcodes depending on the length of the data.  A zero length
    # buffer will lead to a push of empty data onto the stack (OP_0) and any push
    # of data greater than MaxScriptElementSize will not modify the script since
    # that is not allowed by the script engine.  Also, the script will not be
    # modified if pushing the data would cause the script to exceed the maximum
    # allowed script engine size.
    def add_data(self, data: bytes):
        """
        This method do some checks of data size and generated scripts size, the call _add_data

        :param data:
        :return:
        """
        # if self.err:
        #     return self

        # Pushes that would cause the script to exceed the largest allowed
        # script size would result in a non-canonical script.
        data_size = canonical_data_size(data)
        if len(self.script) + data_size > MaxScriptSize:
            msg = "adding %d bytes of data would exceed the maximum allowed canonical script length of %d" % (
                data_size, MaxScriptSize)
            raise ErrScriptNotCanonical(msg)
            # self.err = ErrScriptNotCanonical(msg)
            # return self

        # Pushes larger than the max script element size would result in a
        # script that is not canonical.
        data_len = len(data)
        if data_len > MaxScriptElementSize:
            msg = "adding a data element of %d bytes would exceed the maximum allowed script element size of %d" % (
                data_len, MaxScriptElementSize)
            raise ErrScriptNotCanonical(msg)
            # self.err = ErrScriptNotCanonical(msg)
            # return self

        return self._add_data(data)

    # AddInt64 pushes the passed integer to the end of the script.  The script will
    # not be modified if pushing the data would cause the script to exceed the
    # maximum allowed script engine size.
    def add_int64(self, val: int):

        # if self.err:
        #     return self

        # Pushes that would cause the script to exceed the largest allowed
        # script size would result in a non-canonical script.
        if len(self.script) + 1 > MaxScriptSize:
            msg = "adding an integer would exceed the maximum allowed canonical script length of %d" % MaxScriptSize
            raise ErrScriptNotCanonical(msg)
            # self.err = ErrScriptNotCanonical(msg)
            # return self

        # Fast path for small integers and OP_1NEGATE.
        if val == 0:
            self.script += bytes([OP_0])
            return self

        if val == -1 or 1 <= val <= 16:
            self.script += bytes([(OP_1 - 1 + val)])
            return self

        return self.add_data(ScriptNum(val).bytes())

    # Reset resets the script so it has no content.
    def reset(self):
        self.script = bytes()
        return self

    # # Script returns the currently built script.  When any errors occurred while
    # # building the script, the script will be returned up the point of the first
    # # error along with the error.
    # def get_script(self):
    #     return self.script, self.err
