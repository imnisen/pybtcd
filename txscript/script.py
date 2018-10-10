from enum import Enum
import io
from .opcode import *
from .error import *
from wire.msg_tx import MsgTx, write_tx_out
from chainhash import *

MaxOpsPerScript = 201  # Max number of non-push operations.
MaxPubKeysPerMultiSig = 20  # Multisig can't have more sigs than this.
MaxScriptElementSize = 520  # Max bytes pushable to the stack.


# SigHashType represents hash type bits at the end of a signature.
class SigHashType(Enum):
    SigHashOld = 0x0
    SigHashAll = 0x1
    SigHashNone = 0x2
    SigHashSingle = 0x3
    SigHashAnyOneCanPay = 0x80


# is_small_int returns whether or not the opcode is considered a small integer,
# which is an OP_0, or OP_1 through OP_16.
def is_small_int(op) -> bool:
    if op.value == OP_0 or (op.value >= OP_1 and op.value <= OP_16):
        return True
    else:
        return False


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
    script = bytearray()
    for pop in pops:
        script.extend(pop.bytes())
    return script


# calcHashPrevOuts calculates a single hash of all the previous outputs
# (txid:index) referenced within the passed transaction. This calculated hash
# can be re-used when validating all inputs spending segwit outputs, with a
# signature hash type of SigHashAll. This allows validation to re-use previous
# hashing computation, reducing the complexity of validating SigHashAll inputs
# from  O(N^2) to O(N).
def calc_hash_prevouts(tx: MsgTx):
    """

    :param wire.MsgTx tx:
    :return:
    """
    buffer = io.BytesIO()
    for tx_in in tx.tx_ins:
        # First write out the 32-byte transaction ID one of whose
        # outputs are being referenced by this input.
        buffer.write(tx_in.previous_out_point.hash.to_bytes())

        # Next, we'll encode the index of the referenced output as a
        # little endian integer.
        buffer.write(tx_in.previous_out_point.index.to_bytes(4, byteorder="little"))

    return double_hash_h(buffer.getvalue())


# calcHashSequence computes an aggregated hash of each of the sequence numbers
# within the inputs of the passed transaction. This single hash can be re-used
# when validating all inputs spending segwit outputs, which include signatures
# using the SigHashAll sighash type. This allows validation to re-use previous
# hashing computation, reducing the complexity of validating SigHashAll inputs
# from O(N^2) to O(N).
def calc_hash_sequence(tx: MsgTx):
    """

    :param wire.MsgTx tx:
    :return:
    """
    buffer = io.BytesIO()
    for tx_in in tx.tx_ins:
        buffer.write(tx_in.sequence.to_bytes(4, byteorder="little"))

    return double_hash_h(buffer.getvalue())


# calcHashOutputs computes a hash digest of all outputs created by the
# transaction encoded using the wire format. This single hash can be re-used
# when validating all inputs spending witness programs, which include
# signatures using the SigHashAll sighash type. This allows computation to be
# cached, reducing the total hashing complexity from O(N^2) to O(N).
def calc_hash_outputs(tx: MsgTx):
    """

    :param wire.MsgTx tx:
    :return:
    """
    buffer = io.BytesIO()
    for tx_out in tx.tx_outs:
        write_tx_out(buffer, 0, 0, tx_out)

    return double_hash_h(buffer.getvalue())
