from txscript.opcode import *
from txscript.script_builder import *

# shortFormOps holds a map of opcode names to values for use in short form
# parsing.  It is declared here so it only needs to be created once.
shortFormOps = {}


def parse_int(s):
    try:
        num = int(s)
        return num
    except ValueError:
        return None


def parse_hex(s):
    try:
        if s.startswith("0x"):
            s = s[2:]
        if len(s) % 2 != 0:
            s = s[:-1]
        bts = bytes.fromhex(s)
        return bts
    except ValueError:
        return None


class BadTokenErr(Exception):
    pass


# parseShortForm parses a string as as used in the Bitcoin Core reference tests
# into the script it came from.
#
# The format used for these tests is pretty simple if ad-hoc:
#   - Opcodes other than the push opcodes and unknown are present as
#     either OP_NAME or just NAME
#   - Plain numbers are made into push operations
#   - Numbers beginning with 0x are inserted into the []byte as-is (so
#     0x14 is OP_DATA_20)
#   - Single quoted strings are pushed as data
#   - Anything else is an error
def parse_short_form(script: str):
    # Only create the short form opcode map once.
    global shortFormOps
    if not shortFormOps:
        ops = {}
        for opcode_name, opcode_value in OpcodeByName.items():

            if "OP_UNKNOWN" not in opcode_name:
                ops[opcode_name] = opcode_value

                # The opcodes named OP_# can't have the OP_ prefix
                # stripped or they would conflict with the plain
                # numbers.  Also, since OP_FALSE and OP_TRUE are
                # aliases for the OP_0, and OP_1, respectively, they
                # have the same value, so detect those by name and
                # allow them.
                if opcode_name == "OP_FALSE" or opcode_name == "OP_TRUE" or \
                        (opcode_value != OP_0 and (opcode_value < OP_1 or opcode_value > OP_16)):
                    ops[opcode_name.replace("OP_", "", 1)] = opcode_value

        shortFormOps = ops

    if not script:
        return bytes()

    # Split only does one separator so convert all \n and tab into  space.
    script.replace("\n", " ")
    script.replace("\t", " ")
    token = script.split(" ")
    builder = ScriptBuilder()

    for tok in token:
        if len(tok) == 0:
            continue

        num = parse_int(tok)
        if num is not None:
            builder.add_int64(num)
        else:
            bts = parse_hex(tok)
            if bts is not None:
                builder.script += bts
            else:
                if len(tok) >= 2 and tok[0] == "'" and tok[-1] == "'":
                    builder.add_full_data(tok[1:-1].encode())
                elif tok in shortFormOps:
                    builder.add_op(bytes([shortFormOps[tok]]))
                else:
                    raise BadTokenErr
    return builder.script
