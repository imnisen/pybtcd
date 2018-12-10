import chainhash


# Note: Big int in python is same as int.

# HashToBig converts a chainhash.Hash into a big.Int that can be used to
# perform math comparisons.
def hash_to_big(hash: chainhash.Hash) -> int:
    # A Hash is in little-endian, but the big package wants the bytes in
    # big-endian, so reverse them.
    pass


def calc_work(bits: int):
    pass


# CompactToBig converts a compact representation of a whole number N to an
# unsigned 32-bit number.  The representation is similar to IEEE754 floating
# point numbers.
#
# Like IEEE754 floating point, there are three basic components: the sign,
# the exponent, and the mantissa.  They are broken out as follows:
#
#    * the most significant 8 bits represent the unsigned base 256 exponent
#     * bit 23 (the 24th bit) represents the sign bit
#    * the least significant 23 bits represent the mantissa
#
#    -------------------------------------------------
#    |   Exponent     |    Sign    |    Mantissa     |
#    -------------------------------------------------
#    | 8 bits [31-24] | 1 bit [23] | 23 bits [22-00] |
#    -------------------------------------------------
#
# The formula to calculate N is:
#     N = (-1^sign) * mantissa * 256^(exponent-3)
#
# This compact form is only used in bitcoin to encode unsigned 256-bit numbers
# which represent difficulty targets, thus there really is not a need for a
# sign bit, but it is implemented here to stay consistent with bitcoind.
def compact_to_big(compact: int) -> int:
    #  Extract the mantissa, sign bit, and exponent.
    mantissa = compact & 0x007fffff
    is_negative = (compact & 0x00800000 != 0)
    exponent = compact >> 24

    # Since the base for the exponent is 256, the exponent can be treated
    # as the number of bytes to represent the full 256-bit number.  So,
    # treat the exponent as the number of bytes and shift the mantissa
    # right or left accordingly.  This is equivalent to:
    # N = mantissa * 256^(exponent-3)  ->  N = mantissa * 2 ^ (8(exponent-3)) ->  mantissa << 8(exponent-3)
    if exponent <= 3:
        bn = mantissa >> 8 * (3 - exponent)
    else:
        bn = mantissa << 8 * (exponent - 3)

    # Make it negative if the sign bit is set.
    if is_negative:
        bn = -bn
    return bn


def calc_bytes_len(n: int) -> int:
    return max(1, (n.bit_length() + 7) // 8)


def little_endian_first_bytes_as_int(n):
    length = calc_bytes_len(n)
    return n.to_bytes(length, 'little')[0]


# BigToCompact converts a whole number N to a compact representation using
# an unsigned 32-bit number.  The compact representation only provides 23 bits
# of precision, so values larger than (2^23 - 1) only encode the most
# significant digits of the number.  See CompactToBig for details.
def big_to_compact(n: int) -> int:
    if n == 0:
        return 0

    # bytes_len = calc_bytes_len(n)
    # exponent = bytes_len
    #
    # if exponent <= 3:
    #     print('mantissa1:', little_endian_first_bytes_as_int(n))
    #
    #     mantissa = little_endian_first_bytes_as_int(n) << (8 * (3 - exponent))
    #     print('mantissa2:', mantissa)
    # else:
    #     mantissa = little_endian_first_bytes_as_int(n >> (8 * (exponent - 3)))
    #     print('-mantissa:', mantissa)
    #
    # # When the mantissa already has the sign bit set, the number is too
    # # large to fit into the available 23-bits, so divide the number by 256
    # # and increment the exponent accordingly.
    # if mantissa & 0x00800000 != 0:
    #     mantissa >>= 8
    #     exponent += 1
    #
    # print('exponent:', exponent)
    # print('mantissa:', mantissa)
    #
    # # Pack the exponent, sign bit, and mantissa into an unsigned 32-bit
    # # int and return it.
    # compact = exponent << 24 | mantissa
    # if n < 0:
    #     compact |= 0x00800000
    # return compact
