from enum import Enum
from .opcode import *
from .error import *


# SigHashType represents hash type bits at the end of a signature.
class SigHashType(Enum):
    SigHashOld = 0x0
    SigHashAll = 0x1
    SigHashNone = 0x2
    SigHashSingle = 0x3
    SigHashAnyOneCanPay = 0x80


def parse_script_template(script, opcodes):
    """
    Parse script to ParsedOpcode list
    :param []byte script: bytes of script to parse
    :param [] opcodes:  opcode_array, contains all OpCode
    :return:
    """

    return_script = []

    i = 0
    while i < len(script):
        instruction = script[i]
        op = opcodes[instruction]
        pop = ParsedOpcode(opcode=op)

        if op.length == 1:
            i += 1

        elif op.length > 1:
            if len(script[i:]) < op.length:  # TODO check if this len(script[i+1:]) or len(script[i:]?)
                desc = "opcode {} requires {} bytes, but script only has {} remaining".format(op.name, op.length,
                                                                                              len(script[i:]))
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc)

            pop.data = script[i + 1: i + op.length]
            i += op.length

        elif op.length < 0:
            off = i + 1
            if len(script[off:]) < -op.length:  # TODO check if this len(script[i+1:]) or len(script[i:]?)
                desc = "opcode {} requires {} bytes, but script only has {} remaining".format(op.name, op.length,
                                                                                              len(script[i:]))
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc)

            if op.length == -1:
                l = script[off]
            elif op.length == -2:
                l = script[off] | (script[off + 1] << 8)
            elif op.length == -4:
                l = script[off] | (script[off + 1] << 8) | (script[off + 2] << 16) | (script[off + 3] << 24)
            else:
                desc = "invalid opcode length {}".format(op.length)
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc)

            off += -op.length

            if l < 0 or l > len(script[off:]):  # TOCHANGE Consider to split l<0 error
                desc = "opcode {} pushes {} bytes, but script only has {} remaining".format(op.name, op.length,
                                                                                            len(script[off:]))
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc)

            pop.data = script[off: off + l]
            i += (1 - op.length + l)

        return_script.append(pop)
    return return_script


def parse_script(script):
    return parse_script_template(script, opcode_array)


def unparse_script(pops):
    scripts = []
    for pop in pops:
        scripts.append(pop.bytes())
    return scripts
