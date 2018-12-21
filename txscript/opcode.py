import wire
import btcec
import chainhash
from .utils import *
from .script_flag import *
from .stack import *
from .hash_cache import *
from enum import Enum, IntEnum

# These constants are the values of the official opcodes used on the btc wiki,
# in bitcoin core and in most if not all other references and software related
# to handling BTC scripts
OP_0 = 0x00  # 0
OP_FALSE = 0x00  # 0 - AKA OP_0
OP_DATA_1 = 0x01  # 1
OP_DATA_2 = 0x02  # 2
OP_DATA_3 = 0x03  # 3
OP_DATA_4 = 0x04  # 4
OP_DATA_5 = 0x05  # 5
OP_DATA_6 = 0x06  # 6
OP_DATA_7 = 0x07  # 7
OP_DATA_8 = 0x08  # 8
OP_DATA_9 = 0x09  # 9
OP_DATA_10 = 0x0a  # 10
OP_DATA_11 = 0x0b  # 11
OP_DATA_12 = 0x0c  # 12
OP_DATA_13 = 0x0d  # 13
OP_DATA_14 = 0x0e  # 14
OP_DATA_15 = 0x0f  # 15
OP_DATA_16 = 0x10  # 16
OP_DATA_17 = 0x11  # 17
OP_DATA_18 = 0x12  # 18
OP_DATA_19 = 0x13  # 19
OP_DATA_20 = 0x14  # 20
OP_DATA_21 = 0x15  # 21
OP_DATA_22 = 0x16  # 22
OP_DATA_23 = 0x17  # 23
OP_DATA_24 = 0x18  # 24
OP_DATA_25 = 0x19  # 25
OP_DATA_26 = 0x1a  # 26
OP_DATA_27 = 0x1b  # 27
OP_DATA_28 = 0x1c  # 28
OP_DATA_29 = 0x1d  # 29
OP_DATA_30 = 0x1e  # 30
OP_DATA_31 = 0x1f  # 31
OP_DATA_32 = 0x20  # 32
OP_DATA_33 = 0x21  # 33
OP_DATA_34 = 0x22  # 34
OP_DATA_35 = 0x23  # 35
OP_DATA_36 = 0x24  # 36
OP_DATA_37 = 0x25  # 37
OP_DATA_38 = 0x26  # 38
OP_DATA_39 = 0x27  # 39
OP_DATA_40 = 0x28  # 40
OP_DATA_41 = 0x29  # 41
OP_DATA_42 = 0x2a  # 42
OP_DATA_43 = 0x2b  # 43
OP_DATA_44 = 0x2c  # 44
OP_DATA_45 = 0x2d  # 45
OP_DATA_46 = 0x2e  # 46
OP_DATA_47 = 0x2f  # 47
OP_DATA_48 = 0x30  # 48
OP_DATA_49 = 0x31  # 49
OP_DATA_50 = 0x32  # 50
OP_DATA_51 = 0x33  # 51
OP_DATA_52 = 0x34  # 52
OP_DATA_53 = 0x35  # 53
OP_DATA_54 = 0x36  # 54
OP_DATA_55 = 0x37  # 55
OP_DATA_56 = 0x38  # 56
OP_DATA_57 = 0x39  # 57
OP_DATA_58 = 0x3a  # 58
OP_DATA_59 = 0x3b  # 59
OP_DATA_60 = 0x3c  # 60
OP_DATA_61 = 0x3d  # 61
OP_DATA_62 = 0x3e  # 62
OP_DATA_63 = 0x3f  # 63
OP_DATA_64 = 0x40  # 64
OP_DATA_65 = 0x41  # 65
OP_DATA_66 = 0x42  # 66
OP_DATA_67 = 0x43  # 67
OP_DATA_68 = 0x44  # 68
OP_DATA_69 = 0x45  # 69
OP_DATA_70 = 0x46  # 70
OP_DATA_71 = 0x47  # 71
OP_DATA_72 = 0x48  # 72
OP_DATA_73 = 0x49  # 73
OP_DATA_74 = 0x4a  # 74
OP_DATA_75 = 0x4b  # 75
OP_PUSHDATA1 = 0x4c  # 76
OP_PUSHDATA2 = 0x4d  # 77
OP_PUSHDATA4 = 0x4e  # 78
OP_1NEGATE = 0x4f  # 79
OP_RESERVED = 0x50  # 80
OP_1 = 0x51  # 81 - AKA OP_TRUE
OP_TRUE = 0x51  # 81
OP_2 = 0x52  # 82
OP_3 = 0x53  # 83
OP_4 = 0x54  # 84
OP_5 = 0x55  # 85
OP_6 = 0x56  # 86
OP_7 = 0x57  # 87
OP_8 = 0x58  # 88
OP_9 = 0x59  # 89
OP_10 = 0x5a  # 90
OP_11 = 0x5b  # 91
OP_12 = 0x5c  # 92
OP_13 = 0x5d  # 93
OP_14 = 0x5e  # 94
OP_15 = 0x5f  # 95
OP_16 = 0x60  # 96
OP_NOP = 0x61  # 97
OP_VER = 0x62  # 98
OP_IF = 0x63  # 99
OP_NOTIF = 0x64  # 100
OP_VERIF = 0x65  # 101
OP_VERNOTIF = 0x66  # 102
OP_ELSE = 0x67  # 103
OP_ENDIF = 0x68  # 104
OP_VERIFY = 0x69  # 105
OP_RETURN = 0x6a  # 106
OP_TOALTSTACK = 0x6b  # 107
OP_FROMALTSTACK = 0x6c  # 108
OP_2DROP = 0x6d  # 109
OP_2DUP = 0x6e  # 110
OP_3DUP = 0x6f  # 111
OP_2OVER = 0x70  # 112
OP_2ROT = 0x71  # 113
OP_2SWAP = 0x72  # 114
OP_IFDUP = 0x73  # 115
OP_DEPTH = 0x74  # 116
OP_DROP = 0x75  # 117
OP_DUP = 0x76  # 118
OP_NIP = 0x77  # 119
OP_OVER = 0x78  # 120
OP_PICK = 0x79  # 121
OP_ROLL = 0x7a  # 122
OP_ROT = 0x7b  # 123
OP_SWAP = 0x7c  # 124
OP_TUCK = 0x7d  # 125
OP_CAT = 0x7e  # 126
OP_SUBSTR = 0x7f  # 127
OP_LEFT = 0x80  # 128
OP_RIGHT = 0x81  # 129
OP_SIZE = 0x82  # 130
OP_INVERT = 0x83  # 131
OP_AND = 0x84  # 132
OP_OR = 0x85  # 133
OP_XOR = 0x86  # 134
OP_EQUAL = 0x87  # 135
OP_EQUALVERIFY = 0x88  # 136
OP_RESERVED1 = 0x89  # 137
OP_RESERVED2 = 0x8a  # 138
OP_1ADD = 0x8b  # 139
OP_1SUB = 0x8c  # 140
OP_2MUL = 0x8d  # 141
OP_2DIV = 0x8e  # 142
OP_NEGATE = 0x8f  # 143
OP_ABS = 0x90  # 144
OP_NOT = 0x91  # 145
OP_0NOTEQUAL = 0x92  # 146
OP_ADD = 0x93  # 147
OP_SUB = 0x94  # 148
OP_MUL = 0x95  # 149
OP_DIV = 0x96  # 150
OP_MOD = 0x97  # 151
OP_LSHIFT = 0x98  # 152
OP_RSHIFT = 0x99  # 153
OP_BOOLAND = 0x9a  # 154
OP_BOOLOR = 0x9b  # 155
OP_NUMEQUAL = 0x9c  # 156
OP_NUMEQUALVERIFY = 0x9d  # 157
OP_NUMNOTEQUAL = 0x9e  # 158
OP_LESSTHAN = 0x9f  # 159
OP_GREATERTHAN = 0xa0  # 160
OP_LESSTHANOREQUAL = 0xa1  # 161
OP_GREATERTHANOREQUAL = 0xa2  # 162
OP_MIN = 0xa3  # 163
OP_MAX = 0xa4  # 164
OP_WITHIN = 0xa5  # 165
OP_RIPEMD160 = 0xa6  # 166
OP_SHA1 = 0xa7  # 167
OP_SHA256 = 0xa8  # 168
OP_HASH160 = 0xa9  # 169
OP_HASH256 = 0xaa  # 170
OP_CODESEPARATOR = 0xab  # 171
OP_CHECKSIG = 0xac  # 172
OP_CHECKSIGVERIFY = 0xad  # 173
OP_CHECKMULTISIG = 0xae  # 174
OP_CHECKMULTISIGVERIFY = 0xaf  # 175
OP_NOP1 = 0xb0  # 176
OP_NOP2 = 0xb1  # 177
OP_CHECKLOCKTIMEVERIFY = 0xb1  # 177 - AKA OP_NOP2
OP_NOP3 = 0xb2  # 178
OP_CHECKSEQUENCEVERIFY = 0xb2  # 178 - AKA OP_NOP3
OP_NOP4 = 0xb3  # 179
OP_NOP5 = 0xb4  # 180
OP_NOP6 = 0xb5  # 181
OP_NOP7 = 0xb6  # 182
OP_NOP8 = 0xb7  # 183
OP_NOP9 = 0xb8  # 184
OP_NOP10 = 0xb9  # 185
OP_UNKNOWN186 = 0xba  # 186
OP_UNKNOWN187 = 0xbb  # 187
OP_UNKNOWN188 = 0xbc  # 188
OP_UNKNOWN189 = 0xbd  # 189
OP_UNKNOWN190 = 0xbe  # 190
OP_UNKNOWN191 = 0xbf  # 191
OP_UNKNOWN192 = 0xc0  # 192
OP_UNKNOWN193 = 0xc1  # 193
OP_UNKNOWN194 = 0xc2  # 194
OP_UNKNOWN195 = 0xc3  # 195
OP_UNKNOWN196 = 0xc4  # 196
OP_UNKNOWN197 = 0xc5  # 197
OP_UNKNOWN198 = 0xc6  # 198
OP_UNKNOWN199 = 0xc7  # 199
OP_UNKNOWN200 = 0xc8  # 200
OP_UNKNOWN201 = 0xc9  # 201
OP_UNKNOWN202 = 0xca  # 202
OP_UNKNOWN203 = 0xcb  # 203
OP_UNKNOWN204 = 0xcc  # 204
OP_UNKNOWN205 = 0xcd  # 205
OP_UNKNOWN206 = 0xce  # 206
OP_UNKNOWN207 = 0xcf  # 207
OP_UNKNOWN208 = 0xd0  # 208
OP_UNKNOWN209 = 0xd1  # 209
OP_UNKNOWN210 = 0xd2  # 210
OP_UNKNOWN211 = 0xd3  # 211
OP_UNKNOWN212 = 0xd4  # 212
OP_UNKNOWN213 = 0xd5  # 213
OP_UNKNOWN214 = 0xd6  # 214
OP_UNKNOWN215 = 0xd7  # 215
OP_UNKNOWN216 = 0xd8  # 216
OP_UNKNOWN217 = 0xd9  # 217
OP_UNKNOWN218 = 0xda  # 218
OP_UNKNOWN219 = 0xdb  # 219
OP_UNKNOWN220 = 0xdc  # 220
OP_UNKNOWN221 = 0xdd  # 221
OP_UNKNOWN222 = 0xde  # 222
OP_UNKNOWN223 = 0xdf  # 223
OP_UNKNOWN224 = 0xe0  # 224
OP_UNKNOWN225 = 0xe1  # 225
OP_UNKNOWN226 = 0xe2  # 226
OP_UNKNOWN227 = 0xe3  # 227
OP_UNKNOWN228 = 0xe4  # 228
OP_UNKNOWN229 = 0xe5  # 229
OP_UNKNOWN230 = 0xe6  # 230
OP_UNKNOWN231 = 0xe7  # 231
OP_UNKNOWN232 = 0xe8  # 232
OP_UNKNOWN233 = 0xe9  # 233
OP_UNKNOWN234 = 0xea  # 234
OP_UNKNOWN235 = 0xeb  # 235
OP_UNKNOWN236 = 0xec  # 236
OP_UNKNOWN237 = 0xed  # 237
OP_UNKNOWN238 = 0xee  # 238
OP_UNKNOWN239 = 0xef  # 239
OP_UNKNOWN240 = 0xf0  # 240
OP_UNKNOWN241 = 0xf1  # 241
OP_UNKNOWN242 = 0xf2  # 242
OP_UNKNOWN243 = 0xf3  # 243
OP_UNKNOWN244 = 0xf4  # 244
OP_UNKNOWN245 = 0xf5  # 245
OP_UNKNOWN246 = 0xf6  # 246
OP_UNKNOWN247 = 0xf7  # 247
OP_UNKNOWN248 = 0xf8  # 248
OP_UNKNOWN249 = 0xf9  # 249
OP_SMALLINTEGER = 0xfa  # 250 - bitcoin core internal
OP_PUBKEYS = 0xfb  # 251 - bitcoin core internal
OP_UNKNOWN252 = 0xfc  # 252
OP_PUBKEYHASH = 0xfd  # 253 - bitcoin core internal
OP_PUBKEY = 0xfe  # 254 - bitcoin core internal
OP_INVALIDOPCODE = 0xff  # 255 - bitcoin core internal

# Conditional execution constants.
OpCondFalse = 0
OpCondTrue = 1
OpCondSkip = 2

# opcodeOnelineRepls defines opcode names which are replaced when doing a
# one-line disassembly.  This is done to match the output of the reference
# implementation while not changing the opcode names in the nicer full
# disassembly.
OpcodeOnelineRepls = {
    "OP_1NEGATE": "-1",
    "OP_0": "0",
    "OP_1": "1",
    "OP_2": "2",
    "OP_3": "3",
    "OP_4": "4",
    "OP_5": "5",
    "OP_6": "6",
    "OP_7": "7",
    "OP_8": "8",
    "OP_9": "9",
    "OP_10": "10",
    "OP_11": "11",
    "OP_12": "12",
    "OP_13": "13",
    "OP_14": "14",
    "OP_15": "15",
    "OP_16": "16",
}


# An opcode defines the information related to a txscript opcode.  opfunc, if
# present, is the function to call to perform the opcode on the script.  The
# current script is passed in as a slice with the first member being the opcode
# itself.
class OpCode:
    def __init__(self, value=None, name=None, length=None, opfunc=None):
        """

        :param byte value:
        :param string name:
        :param int length:
        :param func opfunc:
        """
        self.value = value or 0x00
        self.name = name or ""
        self.length = length or 0
        self.opfunc = opfunc or None  # TOCHECK

    def __eq__(self, other):
        return self.value == other.value and \
               self.name == other.name and \
               self.length == other.length and \
               self.opfunc == other.opfunc

    def __repr__(self):
        return self.name


class ParsedOpcode:
    def __init__(self, opcode=None, data=None):
        """

        :param OpCode opcode:
        :param []byte data:
        """
        self.opcode = opcode or OpCode()
        self.data = data or bytes()

    def __eq__(self, other):
        return self.opcode == other.opcode and \
               self.data == other.data

    # Return the opcode if marked as disabled
    # If any opcode marked as disabled is present in a script, it must abort and fail.
    def is_disabled(self) -> bool:
        value = self.opcode.value
        if value == OP_CAT:
            return True
        if value == OP_SUBSTR:
            return True
        if value == OP_LEFT:
            return True
        if value == OP_RIGHT:
            return True
        if value == OP_INVERT:
            return True
        if value == OP_AND:
            return True
        if value == OP_OR:
            return True
        if value == OP_XOR:
            return True
        if value == OP_2MUL:
            return True
        if value == OP_2DIV:
            return True
        if value == OP_MUL:
            return True
        if value == OP_DIV:
            return True
        if value == OP_MOD:
            return True
        if value == OP_LSHIFT:
            return True
        if value == OP_RSHIFT:
            return True
        return False

    # alwaysIllegal returns whether or not the opcode is always illegal when passed
    # over by the program counter even if in a non-executed branch (it isn't a
    # coincidence that they are conditionals).
    def always_illegal(self) -> bool:
        value = self.opcode.value
        if value == OP_VERIF:
            return True
        if value == OP_VERNOTIF:
            return True
        return False

    # isConditional returns whether or not the opcode is a conditional opcode which
    # changes the conditional execution stack when executed.
    def is_conditional(self) -> bool:
        value = self.opcode.value
        if value == OP_IF:
            return True
        if value == OP_NOTIF:
            return True
        if value == OP_ELSE:
            return True
        if value == OP_ENDIF:
            return True
        return False

    # checkMinimalDataPush returns whether or not the current data push uses the
    # smallest possible opcode to represent it.  For example, the value 15 could
    # be pushed with OP_DATA_1 15 (among other variations); however, OP_15 is a
    # single opcode that represents the same value and is only a single byte versus
    # two bytes.
    def check_minimal_data_push(self):
        data = self.data
        data_len = len(self.data)
        opcode = self.opcode.value

        # check zero length data pushed with OP_0
        if data_len == 0 and opcode != OP_0:
            desc = "zero length data push is encoded with opcode %s instead of OP_0" % self.opcode.name
            raise ScriptError(ErrorCode.ErrMinimalData, desc=desc)

        # check one length data with value 1-16  pushed with OP_1-OP_16
        if data_len == 1 and 1 <= data[0] <= 16 and opcode != (OP_1 + data[0] - 1):
            desc = "data push of the value %d encoded with opcode %s instead of OP_%d" % (
                data[0], self.opcode.name, data[0])
            raise ScriptError(ErrorCode.ErrMinimalData, desc=desc)

        # check -1 pushed with OP_1NEGATE
        if data_len == 1 and data[0] == 0x81 and opcode != OP_1NEGATE:
            desc = "data push of the value -1 encoded with opcode %s instead of OP_1NEGATE" % (self.opcode.name)
            raise ScriptError(ErrorCode.ErrMinimalData, desc=desc)

        # check data_len below 75 pushed with direct push
        if data_len <= 75 and int(opcode) != data_len:
            desc = "data push of %d bytes encoded with opcode %s instead of OP_DATA_%d" % (
                data_len, self.opcode.name, data_len)
            raise ScriptError(ErrorCode.ErrMinimalData, desc=desc)

        # check data_len below 255 pushed with OP_PUSHDATA1
        if data_len <= 255 and opcode != OP_PUSHDATA1:
            desc = "data push of %d bytes encoded with opcode %s instead of OP_PUSHDATA1" % (
                data_len, self.opcode.name)
            raise ScriptError(ErrorCode.ErrMinimalData, desc=desc)

        # check data_len below 65535 pushed with OP_PUSHDATA2
        if data_len <= 65535 and opcode != OP_PUSHDATA2:
            desc = "data push of %d bytes encoded with opcode %s instead of OP_PUSHDATA2" % (
                data_len, self.opcode.name)
            raise ScriptError(ErrorCode.ErrMinimalData, desc=desc)

    # print returns a human-readable string representation of the opcode for use
    # in script disassembly.
    def print(self, one_line: bool) -> str:
        # The reference implementation one-line disassembly replaces opcodes
        # which represent values (e.g. OP_0 through OP_16 and OP_1NEGATE)
        # with the raw value.  However, when not doing a one-line dissassembly,
        # we prefer to show the actual opcode names.  Thus, only replace the
        # opcodes in question when the oneline flag is set.
        opcode_name = self.opcode.name

        if one_line:
            repl_name = OpcodeOnelineRepls.get(opcode_name, None)
            if repl_name:
                opcode_name = repl_name

            # Nothing more to do for non-data push opcodes.
            if self.opcode.length == 1:
                return opcode_name

            return format_bytes(self.data, holder="02x")

        # Nothing more to do for non-data push opcodes.
        if self.opcode.length == 1:
            return opcode_name

        ret_string = opcode_name
        if self.opcode.length == -1:
            ret_string += (" 0x%02x" % len(self.data))
        elif self.opcode.length == -2:
            ret_string += (" 0x%04x" % len(self.data))
        elif self.opcode.length == -4:
            ret_string += (" 0x%08x" % len(self.data))

        return "%s %s" % (ret_string, format_bytes(self.data, prefix="0x", holder="02x"))

    # bytes returns any data associated with the opcode encoded as it would be in
    # a script.  This is used for unparsing scripts from parsed opcodes.
    def bytes(self):
        script = bytearray()
        if self.opcode.length == 1:
            script.append(self.opcode.value)
            if len(self.data) != 0:
                desc = "internal consistency error - parsed opcode %s has data length %d when %d was expected".format(
                    self.opcode.name, len(self.data), 0)
                raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)
        elif self.opcode.length > 1:
            script.append(self.opcode.value)
            if len(self.data) != self.opcode.length - 1:
                desc = "internal consistency error - parsed opcode %s has data length %d when %d was expected".format(
                    self.opcode.name, len(self.data), self.opcode.length - 1)
                raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)
            script.extend(self.data)
        elif self.opcode.length < 0:
            script.append(self.opcode.value)
            l = len(self.data)
            if self.opcode.length == -1:
                try:
                    len_bytes = l.to_bytes(1, "little")
                except OverflowError:
                    desc = "internal consistency error - parsed opcode %s has data length %d, but overflow".format(
                        self.opcode.name, len(self.data))
                    raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)
                script.extend(len_bytes)
                script.extend(self.data)
            elif self.opcode.length == -2:
                try:
                    len_bytes = l.to_bytes(2, "little")
                except OverflowError:
                    desc = "internal consistency error - parsed opcode %s has data length %d, but overflow".format(
                        self.opcode.name, len(self.data))
                    raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)
                script.extend(len_bytes)
                script.extend(self.data)
            elif self.opcode.length == -4:
                try:
                    len_bytes = l.to_bytes(4, "little")
                except OverflowError:
                    desc = "internal consistency error - parsed opcode %s has data length %d, but overflow".format(
                        self.opcode.name, len(self.data))
                    raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)
                script.extend(len_bytes)
                script.extend(self.data)
            else:
                desc = "internal consistency error - parsed opcode %s has opcode length %s, not one of -1, -2, -4".format(
                    self.opcode.name, self.opcode.length)
                raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)

        else:
            desc = "opcode: %s,  length: %s is illegal".format(
                self.opcode.name, self.opcode.length)
            raise ScriptError(c=ErrorCode.ErrInternal, desc=desc)

        return script


# *******************************************
#  From script
# *******************************************

# sigHashMask defines the number of bits of the hash type which is used
# to identify which outputs are signed.
sigHashMask = 0x1f


#  removeOpcodeByData will return the script minus any opcodes that would push
# the passed data to the stack.
def remove_opcode_by_data(pops, data):
    ret_pops = []
    for pop in pops:
        if not canonical_push(pop) or data not in pop.data:
            ret_pops.append(pop)
    return ret_pops


# removeOpcode will remove any opcode matching ``opcode'' in the pops
def remove_opcode(pops, opcode):
    """

    :param []parsedOpcode pops:
    :param byte opcode:
    :return:
    """
    ret_pops = []
    for pop in pops:
        if pop.opcode.value != opcode:
            ret_pops.append(pop)
    return ret_pops


# canonicalPush returns true if the object is either not a push instruction
# or the push instruction contained wherein is matches the canonical form
# or using the smallest instruction to do the job. False otherwise.
def canonical_push(pop):
    opcode = pop.opcode.value
    data = pop.data
    data_len = len(pop.data)

    # opcode > OP_16 don't worry about canonical push
    if opcode > OP_16:
        return True

    # if you have one byte to push and it's value <= 16, use OP_2 - OP_16 to push
    # don't use OP_DATA_1 - OP_DATA_75
    if OP_0 < opcode < OP_PUSHDATA1 and data_len == 1 and data[0] <= 16:
        return False

    # if data_len < OP_PUSHDATA1, no need to use OP_PUSHDATA1, use OP_DATA1-OP_DATA_75
    if opcode == OP_PUSHDATA1 and data_len < OP_PUSHDATA1:
        return False

    # if push data len <= 0xffff(1 bytes max), no need to use OP_PUSHDATA2
    if opcode == OP_PUSHDATA2 and data_len <= 0xff:
        return False

    # if push data len <= 0xffff(2 bytes max), no need to use OP_PUSHDATA4
    if opcode == OP_PUSHDATA4 and data_len <= 0xffff:
        return False

    return True


# isWitnessPubKeyHash returns true if the passed script is a
# pay-to-witness-pubkey-hash, and false otherwise.
def is_witness_pub_key_hash(pops) -> bool:
    return len(pops) == 2 and pops[0].opcode.value == OP_0 and pops[1].opcode.value == OP_DATA_20


def unparse_script(pops):
    script = bytearray()
    for pop in pops:
        script.extend(pop.bytes())
    return script


def unparse_script_no_error(pops):
    script = bytearray()
    for pop in pops:
        try:
            script.extend(pop.bytes())
        except ScriptError as e:
            e.extra_data = script
            raise e
        except Exception:
            raise ScriptError(ErrorCode.ErrInternal, extra_data=script)

    return script


# calcWitnessSignatureHash computes the sighash digest of a transaction's
# segwit input using the new, optimized digest calculation algorithm defined
# in BIP0143: https:#github.com/bitcoin/bips/blob/master/bip-0143.mediawiki.
# This function makes use of pre-calculated sighash fragments stored within
# the passed HashCache to eliminate duplicate hashing computations when
# calculating the final digest, reducing the complexity from O(N^2) to O(N).
# Additionally, signatures now cover the input value of the referenced unspent
# output. This allows offline, or hardware wallets to compute the exact amount
# being spent, in addition to the final transaction fee. In the case the
# wallet if fed an invalid input amount, the real sighash will differ causing
# the produced signature to be invalid.
def calc_witness_signature_hash(sub_script, sig_hashes, hash_type, tx, idx, amt):
    # TODO check use of  hash_type type
    """

    :param []parsedOpcode sub_script:
    :param *TxSigHashes sig_hashes:
    :param SigHashType hash_type:
    :param *wire.MsgTx tx:
    :param int idx:
    :param int64 amt:
    :return:
    """

    # As a sanity check, ensure the passed input index for the transaction
    # is valid.
    if idx > len(tx.tx_ins) - 1:
        msg = "idx %d but %d txins" % (idx, len(tx.tx_ins))
        raise IdxTxInptsLenNotMatchError(msg)

    # We'll utilize this buffer throughout to incrementally calculate
    # the signature hash for this transaction.
    sig_hash = io.BytesIO()

    # First write out, then encode the transaction's version number.
    wire.write_element(sig_hash, "uint32", tx.version)

    # Next write out the possibly pre-calculated hashes for the sequence
    # numbers of all inputs, and the hashes of the previous outs for all
    # outputs.

    # If anyone can pay isn't active, then we can use the cached
    # hashPrevOuts, otherwise we just write zeroes for the prev outs.
    if hash_type & SigHashType.SigHashAnyOneCanPay == 0:
        wire.write_element(sig_hash, "chainhash.Hash", sig_hashes.hash_prev_outs)
    else:
        wire.write_element(sig_hash, "chainhash.Hash", chainhash.Hash())

    # If the sighash isn't anyone can pay, single, or none, the use the
    # cached hash sequences, otherwise write all zeroes for the
    # hashSequence.
    if hash_type & SigHashType.SigHashAnyOneCanPay == 0 and \
                            hash_type & sigHashMask != SigHashType.SigHashSingle and \
                            hash_type & sigHashMask != SigHashType.SigHashNone:
        wire.write_element(sig_hash, "chainhash.Hash", sig_hashes.hash_sequence)
    else:
        wire.write_element(sig_hash, "chainhash.Hash", chainhash.Hash())

    tx_in = tx.tx_ins[idx]

    # Next, write the outpoint being spent.
    wire.write_element(sig_hash, "chainhash.Hash", tx_in.previsous_out_point.hash)
    wire.write_element(sig_hash, "uint32", tx_in.previsous_out_point.index)

    if is_witness_pub_key_hash(sub_script):
        # The script code for a p2wkh is a length prefix varint for
        # the next 25 bytes, followed by a re-creation of the original
        # p2pkh pk script.
        sig_hash.write(bytes([0x19]))
        sig_hash.write(bytes([OP_DUP]))
        sig_hash.write(bytes([OP_HASH160]))
        sig_hash.write(bytes([OP_DATA_20]))
        sig_hash.write(sub_script[1].data)
        sig_hash.write(bytes([OP_EQUALVERIFY]))
        sig_hash.write(bytes([OP_CHECKSIG]))
    else:
        # For p2wsh outputs, and future outputs, the script code is
        # the original script, with all code separators removed,
        # serialized with a var int length prefix
        try:
            raw_script = unparse_script(sub_script)
        except ScriptError:
            raw_script = bytes()  # TOCHECK origin here use the script parsed not error before, here I use empty script
        wire.write_var_bytes(sig_hash, 0, raw_script)

    # Next, add the input amount, and sequence number of the input being
    # signed.
    wire.write_element(sig_hash, "uint64", amt)
    wire.write_element(sig_hash, "uint32", tx_in.sequence)

    # If the current signature mode isn't single, or none, then we can
    # re-use the pre-generated hashoutputs sighash fragment. Otherwise,
    # we'll serialize and add only the target output index to the signature
    # pre-image.
    if hash_type & SigHashType.SigHashSingle != SigHashType.SigHashSingle and \
                            hash_type & SigHashType.SigHashNone != SigHashType.SigHashNone:
        wire.write_element(sig_hash, "chainhash.Hash", sig_hashes.hash_outputs)
    elif hash_type & sigHashMask == SigHashType.SigHashSingle and \
                    idx < len(tx.tx_outs):
        b = io.BytesIO()
        wire.write_tx_out(b, 0, 0, tx.tx_outs[idx])
        sig_hash.write(chainhash.double_hash_b(b.getvalue()))
    else:
        wire.write_element(sig_hash, "chainhash.Hash", chainhash.Hash())

    # Finally, write out the transaction's locktime, and the sig hash
    # type.
    wire.write_element(sig_hash, "uint32", tx.lock_time)
    wire.write_element(sig_hash, "uint32", hash_type)

    return chainhash.double_hash_b(sig_hash.getvalue())


# shallowCopyTx creates a shallow copy of the transaction for use when
# calculating the signature hash.  It is used over the Copy method on the
# transaction itself since that is a deep copy and therefore does more work and
# allocates much more space than needed.
def shadow_copy_tx(tx):
    tx_copy = wire.MsgTx(
        version=tx.version,
        tx_ins=[],
        tx_outs=[],
        lock_time=tx.lock_time
    )

    for old_tx_in in tx.tx_ins:
        tx_copy.tx_ins.append(old_tx_in.copy())

    for old_tx_out in tx.tx_outs:
        tx_copy.tx_outs.append(old_tx_out.copy())
    return tx_copy


# calcSignatureHash will, given a script and hash type for the current script
# engine instance, calculate the signature hash to be used for signing and
# verification.
def calc_signature_hash(script, hash_type, tx, idx):  # TODO refactor the func name
    """

    :param []parsedOpcode script:
    :param SigHashType hash_type:
    :param *wire.MsgTx tx:
    :param int idx:
    :return:
    """
    # The SigHashSingle signature type signs only the corresponding input
    # and output (the output with the same index number as the input).
    #
    # Since transactions can have more inputs than outputs, this means it
    # is improper to use SigHashSingle on input indices that don't have a
    # corresponding output.
    #
    # A bug in the original Satoshi client implementation means specifying
    # an index that is out of range results in a signature hash of 1 (as a
    # uint256 little endian).  The original intent appeared to be to
    # indicate failure, but unfortunately, it was never checked and thus is
    # treated as the actual signature hash.  This buggy behavior is now
    # part of the consensus and a hard fork would be required to fix it.
    #
    # Due to this, care must be taken by software that creates transactions
    # which make use of SigHashSingle because it can lead to an extremely
    # dangerous situation where the invalid inputs will end up signing a
    # hash of 1.  This in turn presents an opportunity for attackers to
    # cleverly construct transactions which can steal those coins provided
    # they can reuse signatures.
    if hash_type & sigHashMask == SigHashType.SigHashSingle and \
                    idx < len(tx.tx_outs):
        hash = chainhash.Hash(bytes([0x01]) + bytes(chainhash.HashSize - 1))
        return hash

    # Remove all instances of OP_CODESEPARATOR from the script.
    script = remove_opcode(script, OP_CODESEPARATOR)

    # Make a shallow copy of the transaction, zeroing out the script for
    # all inputs that are not currently being processed.
    tx_copy = shadow_copy_tx(tx)
    for i in range(len(tx_copy.tx_ins)):
        if i == idx:
            # UnparseScript cannot fail here because removeOpcode
            # above only returns a valid script.
            sig_script = unparse_script_no_error(script)
            tx_copy.tx_ins[idx].signature_script = sig_script
        else:
            tx_copy.tx_ins[i].signature_script = bytes()

    v = hash_type & sigHashMask
    if v == SigHashType.SigHashNone:
        tx_copy.tx_outs = tx_copy.tx_outs[0:0]
        for i in range(len(tx_copy.tx_ins)):
            if i != idx:
                tx_copy.tx_ins[i].sequence = 0
    elif v == SigHashType.SigHashSingle:
        # Resize output array to up to and including requested index.
        tx_copy.tx_outs = tx_copy.tx_outs[:idx + 1]

        # All but current output get zeroed out.
        for i in range(idx):
            tx_copy.tx_outs[i].value = -1
            tx_copy.tx_outs[i].pk_script = bytes()

        # Sequence on all other inputs is 0, too.
        for i in range(len(tx_copy.tx_ins)):
            if i != idx:
                tx_copy.tx_ins[i].sequence = 0
    elif v in (SigHashType.SigHashOld, SigHashType.SigHashAll):
        pass

    if hash_type & SigHashType.SigHashAnyOneCanPay != 0:
        tx_copy.tx_ins = tx_copy.tx_ins[idx:idx + 1]

    # The final hash is the double sha256 of both the serialized modified
    # transaction and the hash type (encoded as a 4-byte little-endian
    # value) appended.
    wbuf = io.BytesIO()
    tx_copy.serialize_no_witness(wbuf)
    wire.write_element(wbuf, "uint32", hash_type)
    return chainhash.double_hash_b(wbuf.getvalue())


MaxOpsPerScript = 201  # Max number of non-push operations.
MaxPubKeysPerMultiSig = 20  # Multisig can't have more sigs than this.
MaxScriptElementSize = 520  # Max bytes pushable to the stack.

# *******************************************
#  End from
# *******************************************



# LockTimeThreshold is the number below which a lock time is
# interpreted to be a block number.  Since an average of one block
# is generated per 10 minutes, this allows blocks for about 9,512
# years.
LockTimeThreshold = 5e8  # Tue Nov 5 00:53:20 1985 UTC


# *******************************************
# Opcode implementation functions start here.
# *******************************************

# opcodeDisabled is a common handler for disabled opcodes.  It returns an
# appropriate error indicating the opcode is disabled.  While it would
# ordinarily make more sense to detect if the script contains any disabled
# opcodes before executing in an initial parse step, the consensus rules
# dictate the script doesn't fail until the program counter passes over a
# disabled opcode (even when they appear in a branch that is not executed).
def opcodeDisabled(pop, vm):
    desc = "attempt to execute disabled opcode %s" % pop.opcode.name
    raise ScriptError(c=ErrorCode.ErrDisabledOpcode, desc=desc)


# opcodeReserved is a common handler for all reserved opcodes.  It returns an
# appropriate error indicating the opcode is reserved.
def opcodeReserved(pop, vm):
    desc = "attempt to execute reserved opcode %s" % pop.opcode.name
    raise ScriptError(c=ErrorCode.ErrReservedOpcode, desc=desc)


# opcodeInvalid is a common handler for all invalid opcodes.  It returns an
# appropriate error indicating the opcode is invalid.
def opcodeInvalid(pop, vm):
    desc = "attempt to execute invalid opcode %s" % pop.opcode.name
    raise ScriptError(c=ErrorCode.ErrReservedOpcode, desc=desc)


# opcodeFalse pushes an empty array to the data stack to represent false.  Note
# that 0, when encoded as a number according to the numeric encoding consensus
# rules, is an empty array.
def opcodeFalse(pop, vm):
    vm.dstack.push_byte_array(bytes())
    return


# opcodePushData is a common handler for the vast majority of opcodes that push
# raw data (bytes) to the data stack.
def opcodePushData(pop, vm):
    vm.dstack.push_byte_array(pop.data)
    return


# opcode1Negate pushes -1, encoded as a number, to the data stack.
def opcode1Negate(pop, vm):
    vm.dstack.push_int(ScriptNum(-1))
    return


# opcodeN is a common handler for the small integer data push opcodes.  It
# pushes the numeric value the opcode represents (which will be from 1 to 16)
# onto the data stack.
def opcodeN(pop, vm):
    # The opcodes are all defined consecutively, so the numeric value is
    # the difference.
    vm.dstack.push_int(ScriptNum(pop.opcode.value - (OP_1 - 1)))
    return


# opcodeNop is a common handler for the NOP family of opcodes.  As the name
# implies it generally does nothing, however, it will return an error when
# the flag to discourage use of NOPs is set for select opcodes.
def opcodeNop(pop, vm):
    if pop.opcode.value in (OP_NOP1, OP_NOP4, OP_NOP5, OP_NOP6, OP_NOP7, OP_NOP8, OP_NOP9, OP_NOP10) and \
            vm.hash_flag(ScriptDiscourageUpgradableNops):
        desc = "OP_NOP%d reserved for soft-fork upgrades" % (pop.opcode.value - (OP_NOP1 - 1))
        raise ScriptError(ErrorCode.ErrDiscourageUpgradableNOPs, desc=desc)
    return


# opcodeIf treats the top item on the data stack as a boolean and removes it.
#
# An appropriate entry is added to the conditional stack depending on whether
# the boolean is true and whether this if is on an executing branch in order
# to allow proper execution of further opcodes depending on the conditional
# logic.  When the boolean is true, the first branch will be executed (unless
# this opcode is nested in a non-executed branch).
#
# <expression> if [statements] [else [statements]] endif
#
# Note that, unlike for all non-conditional opcodes, this is executed even when
# it is on a non-executing branch so proper nesting is maintained.
#
# Data stack transformation: [... bool] -> [...]
# Conditional stack transformation: [...] -> [... OpCondValue]
def opcodeIf(pop, vm):
    cond_val = OpCondFalse
    if vm.is_branch_executing():
        ok = vm.pop_if_pool()

        if ok:
            cond_val = OpCondTrue
    else:
        cond_val = OpCondSkip

    vm.cond_stack.append(cond_val)
    return


# opcodeNotIf treats the top item on the data stack as a boolean and removes
# it.
#
# An appropriate entry is added to the conditional stack depending on whether
# the boolean is true and whether this if is on an executing branch in order
# to allow proper execution of further opcodes depending on the conditional
# logic.  When the boolean is false, the first branch will be executed (unless
# this opcode is nested in a non-executed branch).
#
# <expression> notif [statements] [else [statements]] endif
#
# Note that, unlike for all non-conditional opcodes, this is executed even when
# it is on a non-executing branch so proper nesting is maintained.
#
# Data stack transformation: [... bool] -> [...]
# Conditional stack transformation: [...] -> [... OpCondValue]
def opcodeNotIf(pop, vm):
    cond_val = OpCondFalse
    if vm.is_branch_executing():
        ok = vm.pop_if_pool()

        if not ok:
            cond_val = OpCondTrue
    else:
        cond_val = OpCondSkip

    vm.cond_stack.append(cond_val)
    return


# opcodeElse inverts conditional execution for other half of if/else/endif.
#
# An error is returned if there has not already been a matching OP_IF.
#
# Conditional stack transformation: [... OpCondValue] -> [... !OpCondValue]
def opcodeElse(pop, vm):
    if len(vm.cond_stack) == 0:
        desc = "encountered opcode %s with no matching opcode to begin conditional execution" % pop.opcode.name
        raise ScriptError(ErrorCode.ErrUnbalancedConditional, desc=desc)

    if vm.cond_stack[-1] == OpCondTrue:
        vm.cond_stack[-1] = OpCondFalse
    elif vm.cond_stack[-1] == OpCondFalse:
        vm.cond_stack[-1] = OpCondTrue
    elif vm.cond_stack[-1] == OpCondSkip:
        # Value doesn't change in skip since it indicates this opcode
        # is nested in a non-executed branch.
        pass

    return


# opcodeEndif terminates a conditional block, removing the value from the
# conditional execution stack.
#
# An error is returned if there has not already been a matching OP_IF.
#
# Conditional stack transformation: [... OpCondValue] -> [...]
def opcodeEndif(pop, vm):
    if len(vm.cond_stack) == 0:
        desc = "encountered opcode %s with no matching opcode to begin conditional execution" % pop.opcode.name
        raise ScriptError(ErrorCode.ErrUnbalancedConditional, desc=desc)

    vm.cond_stack = vm.cond_stack[:-1]
    return


# abstractVerify examines the top item on the data stack as a boolean value and
# verifies it evaluates to true.  An error is returned either when there is no
# item on the stack or when that item evaluates to false.  In the latter case
# where the verification fails specifically due to the top item evaluating
# to false, the returned error will use the passed error code.
def abstract_verify(pop, vm, error_code):
    verified = vm.dstack.pop_bool()
    if not verified:
        desc = "%s failed" % pop.opcode.name
        raise ScriptError(c=error_code, desc=desc)
    return


# opcodeVerify examines the top item on the data stack as a boolean value and
# verifies it evaluates to true.  An error is returned if it does not.
def opcodeVerify(pop, vm):
    abstract_verify(pop, vm, ErrorCode.ErrVerify)
    return


# opcodeReturn returns an appropriate error since it is always an error to
# return early from a script.
def opcodeReturn(pop, vm):
    desc = "script returned early"
    raise ScriptError(ErrorCode.ErrEarlyReturn, desc=desc)


# verifyLockTime is a helper function used to validate locktimes.
def verify_lock_time(tx_lock_time, threshold, lock_time):
    # The lockTimes in both the script and transaction must be of the same
    # type.
    if not ((tx_lock_time < threshold and lock_time < threshold) or
                (tx_lock_time >= threshold and lock_time >= threshold)):
        desc = "mismatched locktime types -- tx locktime %d, stack locktime %d" % (tx_lock_time, lock_time)
        raise ScriptError(ErrorCode.ErrUnsatisfiedLockTime, desc=desc)

    if lock_time > tx_lock_time:
        desc = "locktime requirement not satisfied -- locktime is greater than the transaction locktime: %d > %d" % (
            lock_time, tx_lock_time)
        raise ScriptError(ErrorCode.ErrUnsatisfiedLockTime, desc=desc)

    return


# opcodeCheckLockTimeVerify compares the top item on the data stack to the
# LockTime field of the transaction containing the script signature
# validating if the transaction outputs are spendable yet.  If flag
# ScriptVerifyCheckLockTimeVerify is not set, the code continues as if OP_NOP2
# were executed.
def opcodeCheckLockTimeVerify(pop, vm):
    # If the ScriptVerifyCheckLockTimeVerify script flag is not set, treat
    # opcode as OP_NOP2 instead.
    if not vm.hash_flag(ScriptVerifyCheckLockTimeVerify):
        if vm.hash_flag(ScriptDiscourageUpgradableNops):
            desc = "OP_NOP2 reserved for soft-fork upgrades"
            raise ScriptError(ErrorCode.ErrDiscourageUpgradableNOPs, desc=desc)
        else:
            return

    # The current transaction locktime is a uint32 resulting in a maximum
    # locktime of 2^32-1 (the year 2106).  However, scriptNums are signed
    # and therefore a standard 4-byte scriptNum would only support up to a
    # maximum of 2^31-1 (the year 2038).  Thus, a 5-byte scriptNum is used
    # here since it will support up to 2^39-1 which allows dates beyond the
    # current locktime limit.
    #
    # PeekByteArray is used here instead of PeekInt because we do not want
    # to be limited to a 4-byte integer for reasons specified above.
    so = vm.dstack.peek_byte_array(idx=0)
    lock_time = make_script_num(so, vm.dstack.verify_minimal_data, script_num_len=5)

    # In the rare event that the argument needs to be < 0 due to some
    # arithmetic being done first, you can always use
    # 0 OP_MAX OP_CHECKLOCKTIMEVERIFY.
    if lock_time < 0:
        desc = "negative lock time: %d" % lock_time
        raise ScriptError(ErrorCode.ErrNegativeLockTime, desc=desc)

    # The lock time field of a transaction is either a block height at
    # which the transaction is finalized or a timestamp depending on if the
    # value is before the txscript.LockTimeThreshold.  When it is under the
    # threshold it is a block height.
    verify_lock_time(vm.tx.lock_time, LockTimeThreshold, lock_time)

    # TOCHECK why
    # The lock time feature can also be disabled, thereby bypassing
    # OP_CHECKLOCKTIMEVERIFY, if every transaction input has been finalized by
    # setting its sequence to the maximum value (wire.MaxTxInSequenceNum).  This
    # condition would result in the transaction being allowed into the blockchain
    # making the opcode ineffective.
    #
    # This condition is prevented by enforcing that the input being used by
    # the opcode is unlocked (its sequence number is less than the max
    # value).  This is sufficient to prove correctness without having to
    # check every input.
    #
    # NOTE: This implies that even if the transaction is not finalized due to
    # another input being unlocked, the opcode execution will still fail when the
    # input being used by the opcode is locked.
    if vm.tx.tx_ins[vm.tx_idx].sequence == wire.MaxTxInSequenceNum:
        raise ScriptError(ErrorCode.ErrUnsatisfiedLockTime, desc="transaction input is finalized")

    return


# TOCONSIDER Why
# opcodeCheckSequenceVerify compares the top item on the data stack to the
# LockTime field of the transaction containing the script signature
# validating if the transaction outputs are spendable yet.  If flag
# ScriptVerifyCheckSequenceVerify is not set, the code continues as if OP_NOP3
# were executed.
def opcodeCheckSequenceVerify(pop, vm):
    # If the ScriptVerifyCheckSequenceVerify script flag is not set, treat
    # opcode as OP_NOP3 instead.
    if not vm.hash_flag(ScriptVerifyCheckSequenceVerify):
        if vm.hash_flag(ScriptDiscourageUpgradableNops):
            desc = "OP_NOP3 reserved for soft-fork upgrades"
            raise ScriptError(ErrorCode.ErrDiscourageUpgradableNOPs, desc=desc)
        else:
            return

    # The current transaction sequence is a uint32 resulting in a maximum
    # sequence of 2^32-1.  However, scriptNums are signed and therefore a
    # standard 4-byte scriptNum would only support up to a maximum of
    # 2^31-1.  Thus, a 5-byte scriptNum is used here since it will support
    # up to 2^39-1 which allows sequences beyond the current sequence
    # limit.
    #
    # PeekByteArray is used here instead of PeekInt because we do not want
    # to be limited to a 4-byte integer for reasons specified above.
    so = vm.dstack.peek_byte_array(idx=0)
    stack_sequence = make_script_num(so, vm.dstack.verify_minimal_data, script_num_len=5)

    # In the rare event that the argument needs to be < 0 due to some
    # arithmetic being done first, you can always use
    # 0 OP_MAX OP_CHECKSEQUENCEVERIFY.
    if stack_sequence < 0:
        desc = "negative sequence: %d" % stack_sequence
        raise ScriptError(ErrorCode.ErrNegativeLockTime, desc=desc)

    sequence = stack_sequence

    # To provide for future soft-fork extensibility, if the
    # operand has the disabled lock-time flag set,
    # CHECKSEQUENCEVERIFY behaves as a NOP.
    if stack_sequence & wire.SequenceLockTimeDisabled != 0:
        return

    # Transaction version numbers not high enough to trigger CSV rules must
    # fail.
    if vm.tx.version < 2:
        desc = "invalid transaction version: %d" % vm.tx.version
        raise ScriptError(ErrorCode.ErrUnsatisfiedLockTime, desc=desc)

    # Sequence numbers with their most significant bit set are not
    # consensus constrained. Testing that the transaction's sequence
    # number does not have this bit set prevents using this property
    # to get around a CHECKSEQUENCEVERIFY check.
    tx_sequence = vm.tx.tx_ins[vm.tx_idx].sequence
    if tx_sequence & wire.SequenceLockTimeDisabled != 0:
        desc = "transaction sequence has sequence locktime disabled bit set: %s" % tx_sequence
        raise ScriptError(ErrorCode.ErrUnsatisfiedLockTime, desc=desc)

    # Mask off non-consensus bits before doing comparisons.
    lock_time_mask = wire.SequenceLockTimeIsSeconds | wire.SequenceLockTimeMask
    return verify_lock_time(tx_sequence & lock_time_mask, wire.SequenceLockTimeIsSeconds, sequence & lock_time_mask)


# opcodeToAltStack removes the top item from the main data stack and pushes it
# onto the alternate data stack.
#
# Main data stack transformation: [... x1 x2 x3] -> [... x1 x2]
# Alt data stack transformation:  [... y1 y2 y3] -> [... y1 y2 y3 x3]
def opcodeToAltStack(pop, vm):
    so = vm.dstack.pop_byte_array()
    vm.astack.push_byte_array(so)
    return


# opcodeFromAltStack removes the top item from the alternate data stack and
# pushes it onto the main data stack.
#
# Main data stack transformation: [... x1 x2 x3] -> [... x1 x2 x3 y3]
# Alt data stack transformation:  [... y1 y2 y3] -> [... y1 y2]
def opcodeFromAltStack(pop, vm):
    so = vm.astack.pop_byte_array()
    vm.dstack.push_byte_array(so)
    return


# opcode2Drop removes the top 2 items from the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1]
def opcode2Drop(pop, vm):
    vm.dstack.dropN(n=2)
    return


# opcode2Dup duplicates the top 2 items on the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1 x2 x3 x2 x3]
def opcode2Dup(pop, vm):
    vm.dstack.dupN(n=2)
    return


# opcode3Dup duplicates the top 3 items on the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1 x2 x3 x1 x2 x3]
def opcode3Dup(pop, vm):
    vm.dstack.dupN(n=3)
    return


# opcode2Over duplicates the 2 items before the top 2 items on the data stack.
#
# Stack transformation: [... x1 x2 x3 x4] -> [... x1 x2 x3 x4 x1 x2]
def opcode2Over(pop, vm):
    vm.dstack.overN(n=2)
    return


# opcode2Rot rotates the top 6 items on the data stack to the left twice.
#
# Stack transformation: [... x1 x2 x3 x4 x5 x6] -> [... x3 x4 x5 x6 x1 x2]
def opcode2Rot(pop, vm):
    vm.dstack.rotN(n=2)
    return


# opcode2Swap swaps the top 2 items on the data stack with the 2 that come
# before them.
#
# Stack transformation: [... x1 x2 x3 x4] -> [... x3 x4 x1 x2]
def opcode2Swap(pop, vm):
    vm.dstack.swapN(n=2)
    return


# opcodeIfDup duplicates the top item of the stack if it is not zero.
#
# Stack transformation (x1==0): [... x1] -> [... x1]
# Stack transformation (x1!=0): [... x1] -> [... x1 x1]
def opcodeIfDup(pop, vm):
    so = vm.dstack.peek_byte_array(idx=0)
    if as_bool(so):
        vm.dstack.push_byte_array(so)
    return


# opcodeDepth pushes the depth of the data stack prior to executing this
# opcode, encoded as a number, onto the data stack.
#
# Stack transformation: [...] -> [... <num of items on the stack>]
# Example with 2 items: [x1 x2] -> [x1 x2 2]
# Example with 3 items: [x1 x2 x3] -> [x1 x2 x3 3]
def opcodeDepth(pop, vm):
    vm.dstack.push_int(ScriptNum(vm.dstack.depth()))
    return


# opcodeDrop removes the top item from the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1 x2]
def opcodeDrop(pop, vm):
    vm.dstack.dropN(n=1)
    return


# opcodeDup duplicates the top item on the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1 x2 x3 x3]
def opcodeDup(pop, vm):
    vm.dstack.dupN(n=1)
    return


# opcodeNip removes the item before the top item on the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1 x3]
def opcodeNip(pop, vm):
    vm.dstack.nipN(idx=1)
    return


# opcodeOver duplicates the item before the top item on the data stack.
#
# Stack transformation: [... x1 x2 x3] -> [... x1 x2 x3 x2]
def opcodeOver(pop, vm):
    vm.dstack.overN(idx=1)
    return


# opcodePick treats the top item on the data stack as an integer and duplicates
# the item on the stack that number of items back to the top.
#
# Stack transformation: [xn ... x2 x1 x0 n] -> [xn ... x2 x1 x0 xn]
# Example with n=1: [x2 x1 x0 1] -> [x2 x1 x0 x1]
# Example with n=2: [x2 x1 x0 2] -> [x2 x1 x0 x2]
def opcodePick(pop, vm):
    val = vm.dstack.pop_int()
    vm.dstack.pickN(val)
    return


# opcodeRoll treats the top item on the data stack as an integer and moves
# the item on the stack that number of items back to the top.
#
# Stack transformation: [xn ... x2 x1 x0 n] -> [... x2 x1 x0 xn]
# Example with n=1: [x2 x1 x0 1] -> [x2 x0 x1]
# Example with n=2: [x2 x1 x0 2] -> [x1 x0 x2]
def opcodeRoll(pop, vm):
    val = vm.dstack.pop_int()
    vm.dstack.rollN(val)
    return


# opcodeRot rotates the top 3 items on the data stack to the left.
#
# Stack transformation: [... x1 x2 x3] -> [... x2 x3 x1]
def opcodeRot(pop, vm):
    vm.dstack.rotN(n=1)
    return


# opcodeSwap swaps the top two items on the stack.
#
# Stack transformation: [... x1 x2] -> [... x2 x1]
def opcodeSwap(pop, vm):
    vm.dstack.swapN(n=1)
    return


# opcodeTuck inserts a duplicate of the top item of the data stack before the
# second-to-top item.
#
# Stack transformation: [... x1 x2] -> [... x2 x1 x2]
def opcodeTuck(pop, vm):
    vm.dstack.tuck()
    return


# opcodeSize pushes the size of the top item of the data stack onto the data
# stack.
#
# Stack transformation: [... x1] -> [... x1 len(x1)]
def opcodeSize(pop, vm):
    so = vm.dstack.peek_byte_array(idx=0)
    vm.dstack.push_int(ScriptNum(len(so)))
    return


# opcodeEqual removes the top 2 items of the data stack, compares them as raw
# bytes, and pushes the result, encoded as a boolean, back to the stack.
#
# Stack transformation: [... x1 x2] -> [... bool]
def opcodeEqual(pop, vm):
    a = vm.dstack.pop_byte_array()
    b = vm.dstack.pop_byte_array()
    vm.dstack.push_bool(a == b)
    return


# opcodeEqualVerify is a combination of opcodeEqual and opcodeVerify.
# Specifically, it removes the top 2 items of the data stack, compares them,
# and pushes the result, encoded as a boolean, back to the stack.  Then, it
# examines the top item on the data stack as a boolean value and verifies it
# evaluates to true.  An error is returned if it does not.
#
# Stack transformation: [... x1 x2] -> [... bool] -> [...]
def opcodeEqualVerify(pop, vm):
    opcodeEqual(pop, vm)
    abstract_verify(pop, vm, ErrorCode.ErrEqualVerify)
    return


# opcode1Add treats the top item on the data stack as an integer and replaces
# it with its incremented value (plus 1).
#
# Stack transformation: [... x1 x2] -> [... x1 x2+1]
def opcode1Add(pop, vm):
    m = vm.dstack.pop_int()
    vm.dstack.push_int(m + 1)
    return


# opcode1Sub treats the top item on the data stack as an integer and replaces
# it with its decremented value (minus 1).
#
# Stack transformation: [... x1 x2] -> [... x1 x2-1]
def opcode1Sub(pop, vm):
    m = vm.dstack.pop_int()
    vm.dstack.push_int(m - 1)
    return


# opcodeNegate treats the top item on the data stack as an integer and replaces
# it with its negation.
#
# Stack transformation: [... x1 x2] -> [... x1 -x2]
def opcodeNegate(pop, vm):
    m = vm.dstack.pop_int()
    vm.dstack.push_int(-m)
    return


# opcodeAbs treats the top item on the data stack as an integer and replaces it
# it with its absolute value.
#
# Stack transformation: [... x1 x2] -> [... x1 abs(x2)]
def opcodeAbs(pop, vm):
    m = vm.dstack.pop_int()
    if m < 0:
        m = - m
    vm.dstack.push_int(m)
    return


# opcodeNot treats the top item on the data stack as an integer and replaces
# it with its "inverted" value (0 becomes 1, non-zero becomes 0).
#
# NOTE: While it would probably make more sense to treat the top item as a
# boolean, and push the opposite, which is really what the intention of this
# opcode is, it is extremely important that is not done because integers are
# interpreted differently than booleans and the consensus rules for this opcode
# dictate the item is interpreted as an integer.
#
# Stack transformation (x2==0): [... x1 0] -> [... x1 1]
# Stack transformation (x2!=0): [... x1 1] -> [... x1 0]
# Stack transformation (x2!=0): [... x1 17] -> [... x1 0]
def opcodeNot(pop, vm):
    m = vm.dstack.pop_int()
    if m == 0:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcode0NotEqual treats the top item on the data stack as an integer and
# replaces it with either a 0 if it is zero, or a 1 if it is not zero.
#
# Stack transformation (x2==0): [... x1 0] -> [... x1 0]
# Stack transformation (x2!=0): [... x1 1] -> [... x1 1]
# Stack transformation (x2!=0): [... x1 17] -> [... x1 1]
def opcode0NotEqual(pop, vm):
    m = vm.dstack.pop_int()
    if m != 0:
        m = ScriptNum(1)
    vm.dstack.push_int(m)
    return


# opcodeAdd treats the top two items on the data stack as integers and replaces
# them with their sum.
#
# Stack transformation: [... x1 x2] -> [... x1+x2]
def opcodeAdd(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    vm.dstack.push_int(a + b)
    return


# opcodeSub treats the top two items on the data stack as integers and replaces
# them with the result of subtracting the top entry from the second-to-top
# entry.
#
# Stack transformation: [... x1 x2] -> [... x1-x2]
def opcodeSub(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    vm.dstack.push_int(b - a)
    return


# opcodeBoolAnd treats the top two items on the data stack as integers.  When
# both of them are not zero, they are replaced with a 1, otherwise a 0.
#
# Stack transformation (x1==0, x2==0): [... 0 0] -> [... 0]
# Stack transformation (x1!=0, x2==0): [... 5 0] -> [... 0]
# Stack transformation (x1==0, x2!=0): [... 0 7] -> [... 0]
# Stack transformation (x1!=0, x2!=0): [... 4 8] -> [... 1]
def opcodeBoolAnd(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a != 0 and b != 0:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeBoolOr treats the top two items on the data stack as integers.  When
# either of them are not zero, they are replaced with a 1, otherwise a 0.
#
# Stack transformation (x1==0, x2==0): [... 0 0] -> [... 0]
# Stack transformation (x1!=0, x2==0): [... 5 0] -> [... 1]
# Stack transformation (x1==0, x2!=0): [... 0 7] -> [... 1]
# Stack transformation (x1!=0, x2!=0): [... 4 8] -> [... 1]
def opcodeBoolOr(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a != 0 or b != 0:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeNumEqual treats the top two items on the data stack as integers.  When
# they are equal, they are replaced with a 1, otherwise a 0.
#
# Stack transformation (x1==x2): [... 5 5] -> [... 1]
# Stack transformation (x1!=x2): [... 5 7] -> [... 0]
def opcodeNumEqual(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a == b:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeNumEqualVerify is a combination of opcodeNumEqual and opcodeVerify.
#
# Specifically, treats the top two items on the data stack as integers.  When
# they are equal, they are replaced with a 1, otherwise a 0.  Then, it examines
# the top item on the data stack as a boolean value and verifies it evaluates
# to true.  An error is returned if it does not.
#
# Stack transformation: [... x1 x2] -> [... bool] -> [...]
def opcodeNumEqualVerify(pop, vm):
    opcodeNumEqual(pop, vm)
    abstract_verify(pop, vm, ErrorCode.ErrNumEqualVerify)
    return


# opcodeNumNotEqual treats the top two items on the data stack as integers.
# When they are NOT equal, they are replaced with a 1, otherwise a 0.
#
# Stack transformation (x1==x2): [... 5 5] -> [... 0]
# Stack transformation (x1!=x2): [... 5 7] -> [... 1]
def opcodeNumNotEqual(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a != b:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeLessThan treats the top two items on the data stack as integers.  When
# the second-to-top item is less than the top item, they are replaced with a 1,
# otherwise a 0.
#
# Stack transformation: [... x1 x2] -> [... bool]
def opcodeLessThan(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a < b:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeGreaterThan treats the top two items on the data stack as integers.
# When the second-to-top item is greater than the top item, they are replaced
# with a 1, otherwise a 0.
#
# Stack transformation: [... x1 x2] -> [... bool]
def opcodeGreaterThan(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a > b:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeLessThanOrEqual treats the top two items on the data stack as integers.
# When the second-to-top item is less than or equal to the top item, they are
# replaced with a 1, otherwise a 0.
#
# Stack transformation: [... x1 x2] -> [... bool]
def opcodeLessThanOrEqual(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a <= b:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeGreaterThanOrEqual treats the top two items on the data stack as
# integers.  When the second-to-top item is greater than or equal to the top
# item, they are replaced with a 1, otherwise a 0.
#
# Stack transformation: [... x1 x2] -> [... bool]
def opcodeGreaterThanOrEqual(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if a >= b:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeMin treats the top two items on the data stack as integers and replaces
# them with the minimum of the two.
#
# Stack transformation: [... x1 x2] -> [... min(x1, x2)]
def opcodeMin(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if b < a:
        vm.dstack.push_int(ScriptNum(b))
    else:
        vm.dstack.push_int(ScriptNum(a))
    return


# opcodeMax treats the top two items on the data stack as integers and replaces
# them with the maximum of the two.
#
# Stack transformation: [... x1 x2] -> [... max(x1, x2)]
def opcodeMax(pop, vm):
    a = vm.dstack.pop_int()
    b = vm.dstack.pop_int()
    if b > a:
        vm.dstack.push_int(ScriptNum(b))
    else:
        vm.dstack.push_int(ScriptNum(a))
    return


# opcodeWithin treats the top 3 items on the data stack as integers.  When the
# value to test is within the specified range (left inclusive), they are
# replaced with a 1, otherwise a 0.
#
# The top item is the max value, the second-top-item is the minimum value, and
# the third-to-top item is the value to test.
#
# Stack transformation: [... x1 min max] -> [... bool]
def opcodeWithin(pop, vm):
    max_val = vm.dstack.pop_int()
    min_val = vm.dstack.pop_int()
    x = vm.dstack.pop_int()
    if min_val <= x < max_val:
        vm.dstack.push_int(ScriptNum(1))
    else:
        vm.dstack.push_int(ScriptNum(0))
    return


# opcodeRipemd160 treats the top item of the data stack as raw bytes and
# replaces it with ripemd160(data).
#
# Stack transformation: [... x1] -> [... ripemd160(x1)]
def opcodeRipemd160(pop, vm):
    buf = vm.dstack.pop_byte_array()
    vm.dstack.push_byte_array(btcec.ripemd160(buf))
    return


# opcodeSha1 treats the top item of the data stack as raw bytes and replaces it
# with sha1(data).
#
# Stack transformation: [... x1] -> [... sha1(x1)]
def opcodeSha1(pop, vm):
    buf = vm.dstack.pop_byte_array()
    vm.dstack.push_byte_array(btcec.sha1(buf))
    return


# opcodeSha256 treats the top item of the data stack as raw bytes and replaces
# it with sha256(data).
#
# Stack transformation: [... x1] -> [... sha256(x1)]
def opcodeSha256(pop, vm):
    buf = vm.dstack.pop_byte_array()
    vm.dstack.push_byte_array(btcec.sha256(buf))
    return


# opcodeHash160 treats the top item of the data stack as raw bytes and replaces
# it with ripemd160(sha256(data)).
#
# Stack transformation: [... x1] -> [... ripemd160(sha256(x1))]
def opcodeHash160(pop, vm):
    buf = vm.dstack.pop_byte_array()
    vm.dstack.push_byte_array(btcec.hash160(buf))
    return


# opcodeHash256 treats the top item of the data stack as raw bytes and replaces
# it with sha256(sha256(data)).
#
# Stack transformation: [... x1] -> [... sha256(sha256(x1))]
def opcodeHash256(pop, vm):
    buf = vm.dstack.pop_byte_array()
    vm.dstack.push_byte_array(chainhash.double_hash_b(buf))
    return


# opcodeCodeSeparator stores the current script offset as the most recently
# seen OP_CODESEPARATOR which is used during signature checking.
#
# This opcode does not change the contents of the data stack.
def opcodeCodeSeparator(pop, vm):
    vm.last_code_sep = vm.script_off
    return


# SigHashType represents hash type bits at the end of a signature.
class SigHashType(IntEnum):
    SigHashOld = 0x0
    SigHashAll = 0x1
    SigHashNone = 0x2
    SigHashSingle = 0x3
    SigHashAnyOneCanPay = 0x80

    # def __and__(self, other):
    #     return self.value & other
    #
    # def __or__(self, other):
    #     return self.value & other

# opcodeCheckSig treats the top 2 items on the stack as a public key and a
# signature and replaces them with a bool which indicates if the signature was
# successfully verified.
#
# The process of verifying a signature requires calculating a signature hash in
# the same way the transaction signer did.  It involves hashing portions of the
# transaction based on the hash type byte (which is the final byte of the
# signature) and the portion of the script starting from the most recent
# OP_CODESEPARATOR (or the beginning of the script if there are none) to the
# end of the script (with any other OP_CODESEPARATORs removed).  Once this
# "script hash" is calculated, the signature is checked using standard
# cryptographic methods against the provided public key.
#
# Stack transformation: [... signature pubkey] -> [... bool]
def opcodeCheckSig(pop, vm):
    pk_bytes = vm.dstack.pop_byte_array()
    full_sig_bytes = vm.dstack.pop_byte_array()

    # The signature actually needs needs to be longer than this, but at
    # least 1 byte is needed for the hash type below.  The full length is
    # checked depending on the script flags and upon parsing the signature.
    if len(full_sig_bytes) < 1:
        vm.dstack.push_bool(False)
        return

    # Trim off hashtype from the signature string and check if the
    # signature and pubkey conform to the strict encoding requirements
    # depending on the flags.
    #
    # NOTE: When the strict encoding flags are set, any errors in the
    # signature or public encoding here result in an immediate script error
    # (and thus no result bool is pushed to the data stack).  This differs
    # from the logic below where any errors in parsing the signature is
    # treated as the signature failure resulting in false being pushed to
    # the data stack.  This is required because the more general script
    # validation consensus rules do not have the new strict encoding
    # requirements enabled by the flags.
    hash_type = SigHashType(full_sig_bytes[-1])
    sig_bytes = full_sig_bytes[:-1]

    vm.check_hash_type_encoding(hash_type)
    vm.check_signature_encoding(sig_bytes)
    vm.check_pub_key_encoding(pk_bytes)

    # Get script starting from the most recent OP_CODESEPARATOR.
    sub_script = vm.sub_script()

    # Generate the signature hash based on the signature hash type.
    if vm.is_witness_version_active(version=0):
        if vm.hash_cache:
            sig_hashes = vm.hash_cache
        else:
            sig_hashes = TxSigHashes.from_msg_tx(vm.tx)

        hash = calc_witness_signature_hash(sub_script, sig_hashes, hash_type,
                                           vm.tx, vm.tx_idx, vm.input_amout)
    else:
        # Remove the signature since there is no way for a signature
        # to sign itself.
        sub_script = remove_opcode_by_data(sub_script, full_sig_bytes)
        hash = calc_signature_hash(sub_script, hash_type, vm.tx, vm.tx_idx)

    try:
        pub_key = btcec.parse_pub_key(pk_bytes, btcec.s256())
    except Exception:
        vm.dstack.push_bool(False)
        return

    try:
        if vm.has_flag(ScriptVerifyStrictEncoding) or vm.has_flag(ScriptVerifyDERSignatures):
            signature = btcec.parse_der_signature(sig_bytes, btcec.s256())
        else:
            signature = btcec.parse_signature(sig_bytes, btcec.s256())
    except Exception as e:
        # print(e)
        vm.dstack.push_bool(False)
        return

    if vm.sig_cache:
        sig_hash = chainhash.Hash(hash)
        valid = vm.sig_cache.exists(sig_hash, signature, pub_key)
        if not valid and signature.verify(hash, pub_key):
            vm.sig_cache.add(sig_hash, signature, pub_key)
            valid = True
    else:
        valid = signature.verify(hash, pub_key)

    if not valid and vm.has_flag(ScriptVerifyNullFail) and len(sig_bytes) > 0:
        desc = "signature not empty on failed checksig"
        raise ScriptError(ErrorCode.ErrNullFail, desc=desc)

    vm.dstack.push_bool(valid)

    return


# opcodeCheckSigVerify is a combination of opcodeCheckSig and opcodeVerify.
# The opcodeCheckSig function is invoked followed by opcodeVerify.  See the
# documentation for each of those opcodes for more details.
#
# Stack transformation: signature pubkey] -> [... bool] -> [...]
def opcodeCheckSigVerify(pop, vm):
    opcodeCheckSig(pop, vm)
    abstract_verify(pop, vm, ErrorCode.ErrCheckSigVerify)
    return


class ParsedSigInfo:
    def __init__(self, signature=None, parsed_signature=None, parsed=None):
        """

        :param []byte signature:
        :param *btcec.Signature parsed_signature:
        :param bool parsed:
        """
        self.signature = signature or bytes()
        self.parsed_signature = parsed_signature or None  # TOCHECK the type, should be btcec.Signature
        self.parsed = parsed or False


# opcodeCheckMultiSig treats the top item on the stack as an integer number of
# public keys, followed by that many entries as raw data representing the public
# keys, followed by the integer number of signatures, followed by that many
# entries as raw data representing the signatures.
#
# Due to a bug in the original Satoshi client implementation, an additional
# dummy argument is also required by the consensus rules, although it is not
# used.  The dummy value SHOULD be an OP_0, although that is not required by
# the consensus rules.  When the ScriptStrictMultiSig flag is set, it must be
# OP_0.
#
# All of the aforementioned stack items are replaced with a bool which
# indicates if the requisite number of signatures were successfully verified.
#
# See the opcodeCheckSigVerify documentation for more details about the process
# for verifying each signature.
#
# Stack transformation:
# [... dummy [sig ...] numsigs [pubkey ...] numpubkeys] -> [... bool]
def opcodeCheckMultiSig(pop, vm):
    # Get pub keys
    num_keys = vm.dstack.pop_int()
    num_pub_keys = num_keys.int32()

    if num_pub_keys < 0:
        msg = "number of pubkeys %d is negative" % num_pub_keys
        raise ScriptError(ErrorCode.ErrInvalidPubKeyCount, msg)

    if num_pub_keys > MaxPubKeysPerMultiSig:
        msg = "too many pubkeys: %d > %d" % (num_pub_keys, MaxPubKeysPerMultiSig)
        raise ScriptError(ErrorCode.ErrInvalidPubKeyCount, msg)

    vm.num_ops += num_pub_keys
    if vm.num_ops > MaxOpsPerScript:
        msg = "exceeded max operation limit of %d" % MaxOpsPerScript
        raise ScriptError(ErrorCode.ErrTooManyOperations, msg)

    pub_keys = []
    for i in range(num_pub_keys):
        pub_key = vm.dstack.pop_byte_array()
        pub_keys.append(pub_key)

    # Get Signatures
    num_sigs = vm.dstack.pop_int()
    num_signatures = num_sigs.int32()

    if num_signatures < 0:
        msg = "number of signatures %d is negative" % num_signatures
        raise ScriptError(ErrorCode.ErrInvalidSignatureCount, msg)

    if num_signatures > num_pub_keys:
        msg = "more signatures than pubkeys: %d > %d" % (num_signatures, num_pub_keys)
        raise ScriptError(ErrorCode.ErrInvalidSignatureCount, msg)

    signatures = []
    for i in range(num_signatures):
        signature = vm.dstack.pop_byte_array()
        sig_info = ParsedSigInfo(signature=signature)
        signatures.append(sig_info)

        # A bug in the original Satoshi client implementation means one more
    # stack value than should be used must be popped.  Unfortunately, this
    # buggy behavior is now part of the consensus and a hard fork would be
    # required to fix it.
    dummy = vm.dstack.pop_byte_array()

    # Since the dummy argument is otherwise not checked, it could be any
    # value which unfortunately provides a source of malleability.  Thus,
    # there is a script flag to force an error when the value is NOT 0.
    if vm.has_flag(ScriptStrictMultiSig) and len(dummy) != 0:
        msg = "multisig dummy argument has length %d instead of 0" % len(dummy)
        raise ScriptError(ErrorCode.ErrSigNullDummy, msg)

    # Get script starting from the most recent OP_CODESEPARATOR.
    script = vm.sub_script()

    # Remove the signature in pre version 0 segwit scripts since there is
    # no way for a signature to sign itself.
    if not vm.is_witness_version_active(version=0):
        for sig_info in signatures:
            script = remove_opcode_by_data(script, sig_info)

    success = True
    num_pub_keys += 1
    pub_key_idx = -1
    signature_idx = 0
    while num_signatures > 0:
        # When there are more signatures than public keys remaining,
        # there is no way to succeed since too many signatures are
        # invalid, so exit early.
        pub_key_idx += 1
        num_pub_keys -= 1
        if num_signatures > num_pub_keys:
            success = False
            break

        sig_info = signatures[signature_idx]
        pub_key = pub_keys[pub_key_idx]

        # The order of the signature and public key evaluation is
        # important here since it can be distinguished by an
        # OP_CHECKMULTISIG NOT when the strict encoding flag is set.
        raw_sig = sig_info.signature
        if len(raw_sig) == 0:
            # Skip to the next pubkey if signature is empty.
            continue

        # Split the signature into hash type and signature components.
        hash_type = SigHashType(raw_sig[-1])
        signature = raw_sig[:-1]

        # Only parse and check the signature encoding once.
        if not sig_info.parsed:
            vm.check_hash_type_encoding(hash_type)
            vm.check_signatire_encoding(signature)

            try:
                if vm.has_flag(ScriptVerifyStrictEncoding) or vm.has_flag(ScriptVerifyDERSignatures):
                    parsed_sig = btcec.parse_der_signature(signature, btcec.s256())
                else:
                    parsed_sig = btcec.parse_signature(signature, btcec.s256())
            except:
                sig_info.parsed = True
                continue

            sig_info.parsed = True
            sig_info.parsed_signature = parsed_sig
        else:
            # Skip to the next pubkey if the signature is invalid.
            if not sig_info.parsed_signature:
                continue

            # Use the already parsed signature.
            parsed_sig = sig_info.parsed_signature

        vm.check_pub_key_encoding(pub_key)
        # parse pub key
        try:
            parsed_pub_key = btcec.parse_pub_key(pub_key, btcec.s256())
        except:
            continue

        # Generate the signature hash based on the signature hash type.
        if vm.is_witness_version_active(version=0):
            if vm.hash_cache:
                sig_hashes = vm.hash_cache
            else:
                sig_hashes = TxSigHashes.from_msg_tx(vm.tx)

            hash = calc_witness_signature_hash(script, sig_hashes, hash_type,
                                               vm.tx, vm.tx_idx, vm.input_amout)
        else:
            # Remove the signature since there is no way for a signature
            # to sign itself.
            hash = calc_signature_hash(script, hash_type, vm.tx, vm.tx_idx)

        if vm.sig_cache:
            sig_hash = chainhash.Hash(hash)
            valid = vm.sig_cache.exists(sig_hash, parsed_sig, parsed_pub_key)
            if not valid and parsed_sig.verify(hash, parsed_pub_key):
                vm.sig_cache.add(sig_hash, parsed_sig, pub_key)
                valid = True
        else:
            valid = parsed_sig.verify(hash, parsed_pub_key)

        if valid:
            # PubKey verified, move on to the next signature.
            signature_idx += 1
            num_signatures -= 1

    if not success and vm.hash_flag(ScriptVerifyNullFail):
        for sig in signatures:
            if len(sig.signatire) > 0:
                msg = "not all signatures empty on failed checkmultisig"
                raise ScriptError(ErrorCode.ErrNullFail, msg)

    vm.dstack.push_bool(success)
    return


# opcodeCheckMultiSigVerify is a combination of opcodeCheckMultiSig and
# opcodeVerify.  The opcodeCheckMultiSig is invoked followed by opcodeVerify.
# See the documentation for each of those opcodes for more details.
#
# Stack transformation:
# [... dummy [sig ...] numsigs [pubkey ...] numpubkeys] -> [... bool] -> [...]
def opcodeCheckMultiSigVerify(pop, vm):
    opcodeCheckMultiSig(pop, vm)
    abstract_verify(pop, vm, ErrorCode.ErrCheckMultiSigVerify)
    return


opcode_array = [
    # Data push opcodes.
    OpCode(OP_FALSE, "OP_0", 1, opcodeFalse),
    OpCode(OP_DATA_1, "OP_DATA_1", 2, opcodePushData),
    OpCode(OP_DATA_2, "OP_DATA_2", 3, opcodePushData),
    OpCode(OP_DATA_3, "OP_DATA_3", 4, opcodePushData),
    OpCode(OP_DATA_4, "OP_DATA_4", 5, opcodePushData),
    OpCode(OP_DATA_5, "OP_DATA_5", 6, opcodePushData),
    OpCode(OP_DATA_6, "OP_DATA_6", 7, opcodePushData),
    OpCode(OP_DATA_7, "OP_DATA_7", 8, opcodePushData),
    OpCode(OP_DATA_8, "OP_DATA_8", 9, opcodePushData),
    OpCode(OP_DATA_9, "OP_DATA_9", 10, opcodePushData),
    OpCode(OP_DATA_10, "OP_DATA_10", 11, opcodePushData),
    OpCode(OP_DATA_11, "OP_DATA_11", 12, opcodePushData),
    OpCode(OP_DATA_12, "OP_DATA_12", 13, opcodePushData),
    OpCode(OP_DATA_13, "OP_DATA_13", 14, opcodePushData),
    OpCode(OP_DATA_14, "OP_DATA_14", 15, opcodePushData),
    OpCode(OP_DATA_15, "OP_DATA_15", 16, opcodePushData),
    OpCode(OP_DATA_16, "OP_DATA_16", 17, opcodePushData),
    OpCode(OP_DATA_17, "OP_DATA_17", 18, opcodePushData),
    OpCode(OP_DATA_18, "OP_DATA_18", 19, opcodePushData),
    OpCode(OP_DATA_19, "OP_DATA_19", 20, opcodePushData),
    OpCode(OP_DATA_20, "OP_DATA_20", 21, opcodePushData),
    OpCode(OP_DATA_21, "OP_DATA_21", 22, opcodePushData),
    OpCode(OP_DATA_22, "OP_DATA_22", 23, opcodePushData),
    OpCode(OP_DATA_23, "OP_DATA_23", 24, opcodePushData),
    OpCode(OP_DATA_24, "OP_DATA_24", 25, opcodePushData),
    OpCode(OP_DATA_25, "OP_DATA_25", 26, opcodePushData),
    OpCode(OP_DATA_26, "OP_DATA_26", 27, opcodePushData),
    OpCode(OP_DATA_27, "OP_DATA_27", 28, opcodePushData),
    OpCode(OP_DATA_28, "OP_DATA_28", 29, opcodePushData),
    OpCode(OP_DATA_29, "OP_DATA_29", 30, opcodePushData),
    OpCode(OP_DATA_30, "OP_DATA_30", 31, opcodePushData),
    OpCode(OP_DATA_31, "OP_DATA_31", 32, opcodePushData),
    OpCode(OP_DATA_32, "OP_DATA_32", 33, opcodePushData),
    OpCode(OP_DATA_33, "OP_DATA_33", 34, opcodePushData),
    OpCode(OP_DATA_34, "OP_DATA_34", 35, opcodePushData),
    OpCode(OP_DATA_35, "OP_DATA_35", 36, opcodePushData),
    OpCode(OP_DATA_36, "OP_DATA_36", 37, opcodePushData),
    OpCode(OP_DATA_37, "OP_DATA_37", 38, opcodePushData),
    OpCode(OP_DATA_38, "OP_DATA_38", 39, opcodePushData),
    OpCode(OP_DATA_39, "OP_DATA_39", 40, opcodePushData),
    OpCode(OP_DATA_40, "OP_DATA_40", 41, opcodePushData),
    OpCode(OP_DATA_41, "OP_DATA_41", 42, opcodePushData),
    OpCode(OP_DATA_42, "OP_DATA_42", 43, opcodePushData),
    OpCode(OP_DATA_43, "OP_DATA_43", 44, opcodePushData),
    OpCode(OP_DATA_44, "OP_DATA_44", 45, opcodePushData),
    OpCode(OP_DATA_45, "OP_DATA_45", 46, opcodePushData),
    OpCode(OP_DATA_46, "OP_DATA_46", 47, opcodePushData),
    OpCode(OP_DATA_47, "OP_DATA_47", 48, opcodePushData),
    OpCode(OP_DATA_48, "OP_DATA_48", 49, opcodePushData),
    OpCode(OP_DATA_49, "OP_DATA_49", 50, opcodePushData),
    OpCode(OP_DATA_50, "OP_DATA_50", 51, opcodePushData),
    OpCode(OP_DATA_51, "OP_DATA_51", 52, opcodePushData),
    OpCode(OP_DATA_52, "OP_DATA_52", 53, opcodePushData),
    OpCode(OP_DATA_53, "OP_DATA_53", 54, opcodePushData),
    OpCode(OP_DATA_54, "OP_DATA_54", 55, opcodePushData),
    OpCode(OP_DATA_55, "OP_DATA_55", 56, opcodePushData),
    OpCode(OP_DATA_56, "OP_DATA_56", 57, opcodePushData),
    OpCode(OP_DATA_57, "OP_DATA_57", 58, opcodePushData),
    OpCode(OP_DATA_58, "OP_DATA_58", 59, opcodePushData),
    OpCode(OP_DATA_59, "OP_DATA_59", 60, opcodePushData),
    OpCode(OP_DATA_60, "OP_DATA_60", 61, opcodePushData),
    OpCode(OP_DATA_61, "OP_DATA_61", 62, opcodePushData),
    OpCode(OP_DATA_62, "OP_DATA_62", 63, opcodePushData),
    OpCode(OP_DATA_63, "OP_DATA_63", 64, opcodePushData),
    OpCode(OP_DATA_64, "OP_DATA_64", 65, opcodePushData),
    OpCode(OP_DATA_65, "OP_DATA_65", 66, opcodePushData),
    OpCode(OP_DATA_66, "OP_DATA_66", 67, opcodePushData),
    OpCode(OP_DATA_67, "OP_DATA_67", 68, opcodePushData),
    OpCode(OP_DATA_68, "OP_DATA_68", 69, opcodePushData),
    OpCode(OP_DATA_69, "OP_DATA_69", 70, opcodePushData),
    OpCode(OP_DATA_70, "OP_DATA_70", 71, opcodePushData),
    OpCode(OP_DATA_71, "OP_DATA_71", 72, opcodePushData),
    OpCode(OP_DATA_72, "OP_DATA_72", 73, opcodePushData),
    OpCode(OP_DATA_73, "OP_DATA_73", 74, opcodePushData),
    OpCode(OP_DATA_74, "OP_DATA_74", 75, opcodePushData),
    OpCode(OP_DATA_75, "OP_DATA_75", 76, opcodePushData),
    OpCode(OP_PUSHDATA1, "OP_PUSHDATA1", -1, opcodePushData),
    OpCode(OP_PUSHDATA2, "OP_PUSHDATA2", -2, opcodePushData),
    OpCode(OP_PUSHDATA4, "OP_PUSHDATA4", -4, opcodePushData),
    OpCode(OP_1NEGATE, "OP_1NEGATE", 1, opcode1Negate),
    OpCode(OP_RESERVED, "OP_RESERVED", 1, opcodeReserved),
    OpCode(OP_TRUE, "OP_1", 1, opcodeN),
    OpCode(OP_2, "OP_2", 1, opcodeN),
    OpCode(OP_3, "OP_3", 1, opcodeN),
    OpCode(OP_4, "OP_4", 1, opcodeN),
    OpCode(OP_5, "OP_5", 1, opcodeN),
    OpCode(OP_6, "OP_6", 1, opcodeN),
    OpCode(OP_7, "OP_7", 1, opcodeN),
    OpCode(OP_8, "OP_8", 1, opcodeN),
    OpCode(OP_9, "OP_9", 1, opcodeN),
    OpCode(OP_10, "OP_10", 1, opcodeN),
    OpCode(OP_11, "OP_11", 1, opcodeN),
    OpCode(OP_12, "OP_12", 1, opcodeN),
    OpCode(OP_13, "OP_13", 1, opcodeN),
    OpCode(OP_14, "OP_14", 1, opcodeN),
    OpCode(OP_15, "OP_15", 1, opcodeN),
    OpCode(OP_16, "OP_16", 1, opcodeN),

    # Control opcodes.
    OpCode(OP_NOP, "OP_NOP", 1, opcodeNop),
    OpCode(OP_VER, "OP_VER", 1, opcodeReserved),
    OpCode(OP_IF, "OP_IF", 1, opcodeIf),
    OpCode(OP_NOTIF, "OP_NOTIF", 1, opcodeNotIf),
    OpCode(OP_VERIF, "OP_VERIF", 1, opcodeReserved),
    OpCode(OP_VERNOTIF, "OP_VERNOTIF", 1, opcodeReserved),
    OpCode(OP_ELSE, "OP_ELSE", 1, opcodeElse),
    OpCode(OP_ENDIF, "OP_ENDIF", 1, opcodeEndif),
    OpCode(OP_VERIFY, "OP_VERIFY", 1, opcodeVerify),
    OpCode(OP_RETURN, "OP_RETURN", 1, opcodeReturn),
    # # As same of OP_NOP2 and OP_NOP3
    # OpCode(OP_CHECKLOCKTIMEVERIFY, "OP_CHECKLOCKTIMEVERIFY", 1, opcodeCheckLockTimeVerify),
    # OpCode(OP_CHECKSEQUENCEVERIFY, "OP_CHECKSEQUENCEVERIFY", 1, opcodeCheckSequenceVerify),

    # Stack opcodes.
    OpCode(OP_TOALTSTACK, "OP_TOALTSTACK", 1, opcodeToAltStack),
    OpCode(OP_FROMALTSTACK, "OP_FROMALTSTACK", 1, opcodeFromAltStack),
    OpCode(OP_2DROP, "OP_2DROP", 1, opcode2Drop),
    OpCode(OP_2DUP, "OP_2DUP", 1, opcode2Dup),
    OpCode(OP_3DUP, "OP_3DUP", 1, opcode3Dup),
    OpCode(OP_2OVER, "OP_2OVER", 1, opcode2Over),
    OpCode(OP_2ROT, "OP_2ROT", 1, opcode2Rot),
    OpCode(OP_2SWAP, "OP_2SWAP", 1, opcode2Swap),
    OpCode(OP_IFDUP, "OP_IFDUP", 1, opcodeIfDup),
    OpCode(OP_DEPTH, "OP_DEPTH", 1, opcodeDepth),
    OpCode(OP_DROP, "OP_DROP", 1, opcodeDrop),
    OpCode(OP_DUP, "OP_DUP", 1, opcodeDup),
    OpCode(OP_NIP, "OP_NIP", 1, opcodeNip),
    OpCode(OP_OVER, "OP_OVER", 1, opcodeOver),
    OpCode(OP_PICK, "OP_PICK", 1, opcodePick),
    OpCode(OP_ROLL, "OP_ROLL", 1, opcodeRoll),
    OpCode(OP_ROT, "OP_ROT", 1, opcodeRot),
    OpCode(OP_SWAP, "OP_SWAP", 1, opcodeSwap),
    OpCode(OP_TUCK, "OP_TUCK", 1, opcodeTuck),

    # Splice opcodes.
    OpCode(OP_CAT, "OP_CAT", 1, opcodeDisabled),
    OpCode(OP_SUBSTR, "OP_SUBSTR", 1, opcodeDisabled),
    OpCode(OP_LEFT, "OP_LEFT", 1, opcodeDisabled),
    OpCode(OP_RIGHT, "OP_RIGHT", 1, opcodeDisabled),
    OpCode(OP_SIZE, "OP_SIZE", 1, opcodeSize),

    # Bitwise logic opcodes.
    OpCode(OP_INVERT, "OP_INVERT", 1, opcodeDisabled),
    OpCode(OP_AND, "OP_AND", 1, opcodeDisabled),
    OpCode(OP_OR, "OP_OR", 1, opcodeDisabled),
    OpCode(OP_XOR, "OP_XOR", 1, opcodeDisabled),
    OpCode(OP_EQUAL, "OP_EQUAL", 1, opcodeEqual),
    OpCode(OP_EQUALVERIFY, "OP_EQUALVERIFY", 1, opcodeEqualVerify),
    OpCode(OP_RESERVED1, "OP_RESERVED1", 1, opcodeReserved),
    OpCode(OP_RESERVED2, "OP_RESERVED2", 1, opcodeReserved),

    # Numeric related opcodes.
    OpCode(OP_1ADD, "OP_1ADD", 1, opcode1Add),
    OpCode(OP_1SUB, "OP_1SUB", 1, opcode1Sub),
    OpCode(OP_2MUL, "OP_2MUL", 1, opcodeDisabled),
    OpCode(OP_2DIV, "OP_2DIV", 1, opcodeDisabled),
    OpCode(OP_NEGATE, "OP_NEGATE", 1, opcodeNegate),
    OpCode(OP_ABS, "OP_ABS", 1, opcodeAbs),
    OpCode(OP_NOT, "OP_NOT", 1, opcodeNot),
    OpCode(OP_0NOTEQUAL, "OP_0NOTEQUAL", 1, opcode0NotEqual),
    OpCode(OP_ADD, "OP_ADD", 1, opcodeAdd),
    OpCode(OP_SUB, "OP_SUB", 1, opcodeSub),
    OpCode(OP_MUL, "OP_MUL", 1, opcodeDisabled),
    OpCode(OP_DIV, "OP_DIV", 1, opcodeDisabled),
    OpCode(OP_MOD, "OP_MOD", 1, opcodeDisabled),
    OpCode(OP_LSHIFT, "OP_LSHIFT", 1, opcodeDisabled),
    OpCode(OP_RSHIFT, "OP_RSHIFT", 1, opcodeDisabled),
    OpCode(OP_BOOLAND, "OP_BOOLAND", 1, opcodeBoolAnd),
    OpCode(OP_BOOLOR, "OP_BOOLOR", 1, opcodeBoolOr),
    OpCode(OP_NUMEQUAL, "OP_NUMEQUAL", 1, opcodeNumEqual),
    OpCode(OP_NUMEQUALVERIFY, "OP_NUMEQUALVERIFY", 1, opcodeNumEqualVerify),
    OpCode(OP_NUMNOTEQUAL, "OP_NUMNOTEQUAL", 1, opcodeNumNotEqual),
    OpCode(OP_LESSTHAN, "OP_LESSTHAN", 1, opcodeLessThan),
    OpCode(OP_GREATERTHAN, "OP_GREATERTHAN", 1, opcodeGreaterThan),
    OpCode(OP_LESSTHANOREQUAL, "OP_LESSTHANOREQUAL", 1, opcodeLessThanOrEqual),
    OpCode(OP_GREATERTHANOREQUAL, "OP_GREATERTHANOREQUAL", 1, opcodeGreaterThanOrEqual),
    OpCode(OP_MIN, "OP_MIN", 1, opcodeMin),
    OpCode(OP_MAX, "OP_MAX", 1, opcodeMax),
    OpCode(OP_WITHIN, "OP_WITHIN", 1, opcodeWithin),

    # Crypto opcodes.
    OpCode(OP_RIPEMD160, "OP_RIPEMD160", 1, opcodeRipemd160),
    OpCode(OP_SHA1, "OP_SHA1", 1, opcodeSha1),
    OpCode(OP_SHA256, "OP_SHA256", 1, opcodeSha256),
    OpCode(OP_HASH160, "OP_HASH160", 1, opcodeHash160),
    OpCode(OP_HASH256, "OP_HASH256", 1, opcodeHash256),
    OpCode(OP_CODESEPARATOR, "OP_CODESEPARATOR", 1, opcodeCodeSeparator),
    OpCode(OP_CHECKSIG, "OP_CHECKSIG", 1, opcodeCheckSig),
    OpCode(OP_CHECKSIGVERIFY, "OP_CHECKSIGVERIFY", 1, opcodeCheckSigVerify),
    OpCode(OP_CHECKMULTISIG, "OP_CHECKMULTISIG", 1, opcodeCheckMultiSig),
    OpCode(OP_CHECKMULTISIGVERIFY, "OP_CHECKMULTISIGVERIFY", 1, opcodeCheckMultiSigVerify),

    # Reserved opcodes.
    OpCode(OP_NOP1, "OP_NOP1", 1, opcodeNop),
    OpCode(OP_CHECKLOCKTIMEVERIFY, "OP_CHECKLOCKTIMEVERIFY", 1, opcodeCheckLockTimeVerify),
    OpCode(OP_CHECKSEQUENCEVERIFY, "OP_CHECKSEQUENCEVERIFY", 1, opcodeCheckSequenceVerify),
    OpCode(OP_NOP4, "OP_NOP4", 1, opcodeNop),
    OpCode(OP_NOP5, "OP_NOP5", 1, opcodeNop),
    OpCode(OP_NOP6, "OP_NOP6", 1, opcodeNop),
    OpCode(OP_NOP7, "OP_NOP7", 1, opcodeNop),
    OpCode(OP_NOP8, "OP_NOP8", 1, opcodeNop),
    OpCode(OP_NOP9, "OP_NOP9", 1, opcodeNop),
    OpCode(OP_NOP10, "OP_NOP10", 1, opcodeNop),

    # Undefined opcodes.
    OpCode(OP_UNKNOWN186, "OP_UNKNOWN186", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN187, "OP_UNKNOWN187", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN188, "OP_UNKNOWN188", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN189, "OP_UNKNOWN189", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN190, "OP_UNKNOWN190", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN191, "OP_UNKNOWN191", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN192, "OP_UNKNOWN192", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN193, "OP_UNKNOWN193", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN194, "OP_UNKNOWN194", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN195, "OP_UNKNOWN195", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN196, "OP_UNKNOWN196", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN197, "OP_UNKNOWN197", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN198, "OP_UNKNOWN198", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN199, "OP_UNKNOWN199", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN200, "OP_UNKNOWN200", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN201, "OP_UNKNOWN201", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN202, "OP_UNKNOWN202", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN203, "OP_UNKNOWN203", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN204, "OP_UNKNOWN204", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN205, "OP_UNKNOWN205", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN206, "OP_UNKNOWN206", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN207, "OP_UNKNOWN207", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN208, "OP_UNKNOWN208", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN209, "OP_UNKNOWN209", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN210, "OP_UNKNOWN210", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN211, "OP_UNKNOWN211", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN212, "OP_UNKNOWN212", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN213, "OP_UNKNOWN213", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN214, "OP_UNKNOWN214", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN215, "OP_UNKNOWN215", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN216, "OP_UNKNOWN216", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN217, "OP_UNKNOWN217", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN218, "OP_UNKNOWN218", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN219, "OP_UNKNOWN219", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN220, "OP_UNKNOWN220", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN221, "OP_UNKNOWN221", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN222, "OP_UNKNOWN222", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN223, "OP_UNKNOWN223", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN224, "OP_UNKNOWN224", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN225, "OP_UNKNOWN225", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN226, "OP_UNKNOWN226", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN227, "OP_UNKNOWN227", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN228, "OP_UNKNOWN228", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN229, "OP_UNKNOWN229", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN230, "OP_UNKNOWN230", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN231, "OP_UNKNOWN231", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN232, "OP_UNKNOWN232", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN233, "OP_UNKNOWN233", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN234, "OP_UNKNOWN234", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN235, "OP_UNKNOWN235", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN236, "OP_UNKNOWN236", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN237, "OP_UNKNOWN237", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN238, "OP_UNKNOWN238", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN239, "OP_UNKNOWN239", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN240, "OP_UNKNOWN240", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN241, "OP_UNKNOWN241", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN242, "OP_UNKNOWN242", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN243, "OP_UNKNOWN243", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN244, "OP_UNKNOWN244", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN245, "OP_UNKNOWN245", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN246, "OP_UNKNOWN246", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN247, "OP_UNKNOWN247", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN248, "OP_UNKNOWN248", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN249, "OP_UNKNOWN249", 1, opcodeInvalid),

    # Bitcoin Core internal use opcode.  Defined here for completeness.
    OpCode(OP_SMALLINTEGER, "OP_SMALLINTEGER", 1, opcodeInvalid),
    OpCode(OP_PUBKEYS, "OP_PUBKEYS", 1, opcodeInvalid),
    OpCode(OP_UNKNOWN252, "OP_UNKNOWN252", 1, opcodeInvalid),
    OpCode(OP_PUBKEYHASH, "OP_PUBKEYHASH", 1, opcodeInvalid),
    OpCode(OP_PUBKEY, "OP_PUBKEY", 1, opcodeInvalid),

    OpCode(OP_INVALIDOPCODE, "OP_INVALIDOPCODE", 1, opcodeInvalid),

]

OpcodeByName = {op.name: op.value for op in opcode_array}
OpcodeByName["OP_FALSE"] = OP_FALSE
OpcodeByName["OP_TRUE"] = OP_TRUE
OpcodeByName["OP_NOP2"] = OP_CHECKLOCKTIMEVERIFY
OpcodeByName["OP_NOP3"] = OP_CHECKSEQUENCEVERIFY
