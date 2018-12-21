from .opcode import *


# Bip16Activation is the timestamp where BIP0016 is valid to use in the
# blockchain.  To be used to determine if BIP0016 should be called for or not.
# This timestamp corresponds to Sun Apr 1 00:00:00 UTC 2012.
Bip16Activation = 1333238400


# payToWitnessPubKeyHashDataSize is the size of the witness program's
# data push for a pay-to-witness-pub-key-hash output.
payToWitnessPubKeyHashDataSize = 20

# payToWitnessScriptHashDataSize is the size of the witness program's
# data push for a pay-to-witness-script-hash output.
payToWitnessScriptHashDataSize = 32


# is_small_int returns whether or not the opcode is considered a small integer,
# which is an OP_0, or OP_1 through OP_16.
def is_small_int(op) -> bool:
    if op.value == OP_0 or OP_1 <= op.value <= OP_16:
        return True
    else:
        return False


# --------


def is_pay_to_witness_pub_key_hash(script) -> bool:
    try:
        pops = parse_script(script)
    except ScriptError:
        return False
    return is_witness_pub_key_hash(pops)


# --------

# isScriptHash returns true if the script passed is a pay-to-script-hash
# transaction, false otherwise.
def is_script_hash(pops) -> bool:
    return len(pops) == 3 and \
           pops[0].opcode.value == OP_HASH160 and \
           pops[1].opcode.value == OP_DATA_20 and \
           pops[2].opcode.value == OP_EQUAL


# IsPayToScriptHash returns true if the script is in the standard
# pay-to-script-hash (P2SH) format, false otherwise.
def is_pay_to_script_hash(script) -> bool:
    try:
        pops = parse_script(script)
    except ScriptError:
        return False
    return is_script_hash(pops)


# --------

# isWitnessScriptHash returns true if the passed script is a
# pay-to-witness-script-hash transaction, false otherwise.
def is_witness_script_hash(pops) -> bool:
    return len(pops) == 2 and pops[0].opcode.value == OP_0 and pops[1].opcode.value == OP_DATA_32


# IsPayToWitnessScriptHash returns true if the is in the standard
# pay-to-witness-script-hash (P2WSH) format, false otherwise.
def is_pay_to_witness_script_hash(script) -> bool:
    try:
        pops = parse_script(script)
    except ScriptError:
        return False
    return is_witness_script_hash(pops)


# --------

# isPushOnly returns true if the script only pushes data, false otherwise.
def is_push_only(pops) -> bool:
    # NOTE: This function does NOT verify opcodes directly since it is
    # internal and is only called with parsed opcodes for scripts that did
    # not have any parse errors.  Thus, consensus is properly maintained.

    for pop in pops:
        if pop.opcode.value > OP_16:
            return False
    return True


# IsPushOnlyScript returns whether or not the passed script only pushes data.
#
# False will be returned when the script does not parse
def is_push_only_script(script: bytes) -> bool:
    try:
        pops = parse_script(script)
    except ScriptError:
        return False
    return is_push_only(pops)


# IsWitnessProgram returns true if the passed script is a valid witness
# program which is encoded according to the passed witness program version. A
# witness program must be a small integer (from 0-16), followed by 2-40 bytes
# of pushed data.
def is_script_witness_program(script: bytes) -> bool:
    # The length of the script must be between 4 and 42 bytes. The
    # smallest program is the witness version, followed by a data push of
    # 2 bytes.  The largest allowed witness program has a data push of
    # 40-bytes.
    if len(script) < 4 or len(script) > 42:
        return False

    pops = parse_script(script)
    return is_pops_witness_program(pops)


# isWitnessProgram returns true if the passed script is a witness program, and
# false otherwise. A witness program MUST adhere to the following constraints:
# there must be exactly two pops (program version and the program itself), the
# first opcode MUST be a small integer (0-16), the push data MUST be
# canonical, and finally the size of the push data must be between 2 and 40
# bytes.
def is_pops_witness_program(pops):
    return len(pops) == 2 and \
           is_small_int(pops[0].opcode) and \
           canonical_push(pops[1]) and \
           2 <= len(pops[1].data) <= 40


# ExtractWitnessProgramInfo attempts to extract the witness program version,
# as well as the witness program itself from the passed script.
def extract_witness_program_info(script: bytes):
    pops = parse_script(script)

    # If at this point, the scripts doesn't resemble a witness program,
    # then we'll exit early as there isn't a valid version or program to
    # extract.
    if not is_pops_witness_program(pops):
        # desc = "script is not a witness program, unable to extract version or witness program"
        raise NotWitnessProgramError

    witness_version = as_small_int(pops[0].opcode)
    witness_program = pops[1].data
    return witness_version, witness_program


# asSmallInt returns the passed opcode, which must be true according to
# isSmallInt(), as an integer.
def as_small_int(op) -> int:
    if op.value == OP_0:
        return 0
    return int(op.value - (OP_1 - 1))


# getSigOpCount is the implementation function for counting the number of
# signature operations in the script provided by pops. If precise mode is
# requested then we attempt to count the number of operations for a multisig
# op. Otherwise we use the maximum.
def get_sig_op_count_inner(pops, precise) -> int:
    nsigs = 0
    for i, pop in enumerate(pops):
        value = pop.opcode.value
        if value in (OP_CHECKSIG, OP_CHECKSIGVERIFY):
            nsigs += 1
        elif value in (OP_CHECKMULTISIG, OP_CHECKMULTISIGVERIFY):
            if precise and i > 0 and OP_1 <= pops[i - 1].opcode.value <= OP_16:
                nsigs += as_small_int(pops[i - 1].opcode)
            else:
                nsigs += MaxPubKeysPerMultiSig
        else:
            # not a sigop
            pass
    return nsigs


# GetSigOpCount provides a quick count of the number of signature operations
# in a script. a CHECKSIG operations counts for 1, and a CHECK_MULTISIG for 20.
# If the script fails to parse, then the count up to the point of failure is
# returned.
def get_sig_op_count(script: bytes):
    pops = parse_script_no_err(script)
    return get_sig_op_count_inner(pops, False)


# GetPreciseSigOpCount returns the number of signature operations in
# scriptPubKey.  If bip16 is true then scriptSig may be searched for the
# Pay-To-Script-Hash script in order to find the precise number of signature
# operations in the transaction.  If the script fails to parse, then the count
# up to the point of failure is returned.
def get_precise_sig_op_count(script_sig, script_pub_key, bip16):
    pops = parse_script_no_err(script_pub_key)

    # Treat non P2SH transactions as normal.
    if not (bip16 and is_script_hash(pops)):
        return get_sig_op_count_inner(pops, precise=True)

    # The public key script is a pay-to-script-hash, so parse the signature
    # script to get the final item.  Scripts that fail to fully parse count
    # as 0 signature operations.
    try:
        sig_pops = parse_script(script_sig)
    except ScriptError:
        return 0

    # The signature script must only push data to the stack for P2SH to be
    # a valid pair, so the signature operation count is 0 when that is not
    # the case.
    if (not is_push_only(sig_pops)) or len(sig_pops) == 0:
        return 0

    # The P2SH script is the last item the signature script pushes to the
    # stack.  When the script is empty, there are no signature operations.
    sh_script = sig_pops[-1].data
    if len(sh_script) == 0:
        return 0

    # Parse the P2SH script and don't check the error since parseScript
    # returns the parsed-up-to-error list of pops and the consensus rules
    # dictate signature operations are counted up to the first parse
    # failure.
    sh_pops = parse_script_no_err(sh_script)
    return get_sig_op_count_inner(sh_pops, precise=True)


def get_witness_sig_op_count(sig_script, pk_script, witness) -> int:
    # If this is a regular witness program, then we can proceed directly
    # to counting its signature operations without any further processing.
    if is_script_witness_program(pk_script):
        return _get_witness_sig_op_count(pk_script, witness)

    # Next, we'll check the sigScript to see if this is a nested p2sh
    # witness program. This is a case wherein the sigScript is actually a
    # datapush of a p2wsh witness program.
    try:
        sig_pops = parse_script(sig_script)
    except:
        return 0

    if is_pay_to_script_hash(pk_script) and is_push_only(sig_pops) and is_script_witness_program(sig_script[1:]):
        return _get_witness_sig_op_count(sig_script[1:], witness)

    return 0


# getWitnessSigOps returns the number of signature operations generated by
# spending the passed witness program wit the passed witness. The exact
# signature counting heuristic is modified by the version of the passed
# witness program. If the version of the witness program is unable to be
# extracted, then 0 is returned for the sig op count.
def _get_witness_sig_op_count(pk_script, witness) -> int:
    # Attempt to extract the witness program version.
    try:
        witness_version, witness_program = extract_witness_program_info(pk_script)
    except Exception:
        return 0

    if witness_version == 0:
        if len(witness_program) == payToWitnessPubKeyHashDataSize:
            return 1
        elif len(witness_program) == payToWitnessScriptHashDataSize and len(witness) > 0:
            witness_script = witness[-1]
            pops = parse_script_no_err(witness_script)
            return get_sig_op_count_inner(pops, precise=True)

    return 0








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
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc, extra_data=return_script)

            pop.data = script[i + 1: i + op.length]
            i += op.length

        elif op.length < 0:
            off = i + 1
            if len(script[off:]) < -op.length:  # TODO check if this len(script[i+1:]) or len(script[i:]?)
                desc = "opcode {} requires {} bytes, but script only has {} remaining".format(op.name, op.length,
                                                                                              len(script[i:]))
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc, extra_data=return_script)

            if op.length == -1:
                l = script[off]
            elif op.length == -2:
                l = script[off] | (script[off + 1] << 8)
            elif op.length == -4:
                l = script[off] | (script[off + 1] << 8) | (script[off + 2] << 16) | (script[off + 3] << 24)
            else:
                desc = "invalid opcode length {}".format(op.length)
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc, extra_data=return_script)

            off += -op.length

            if l < 0 or l > len(script[off:]):  # TOCHANGE Consider to split l<0 error
                desc = "opcode {} pushes {} bytes, but script only has {} remaining".format(op.name, op.length,
                                                                                            len(script[off:]))
                raise ScriptError(c=ErrorCode.ErrMalformedPush, desc=desc, extra_data=return_script)

            pop.data = script[off: off + l]
            i += (1 - op.length + l)

        return_script.append(pop)
    return return_script


def parse_script_no_err(script):
    try:
        pops = parse_script_template(script, opcode_array)
    except ScriptError as e:
        pops = e.extra_data
    return pops


def parse_script(script):
    return parse_script_template(script, opcode_array)


# IsUnspendable returns whether the passed public key script is unspendable, or
# guaranteed to fail at execution.  This allows inputs to be pruned instantly
# when entering the UTXO set.
def is_unspendabe(pk_script) -> bool:
    try:
        pops = parse_script(pk_script)
    except ScriptError:
        return True

    return len(pops) > 0 and pops[0].opcode.value == OP_RETURN
