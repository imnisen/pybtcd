# -----------------------------------------------------------------------------
# A variable length quantity (VLQ) is an encoding that uses an arbitrary number
# of binary octets to represent an arbitrarily large integer.  The scheme
# employs a most significant byte (MSB) base-128 encoding where the high bit in
# each byte indicates whether or not the byte is the final one.  In addition,
# to ensure there are no redundant encodings, an offset is subtracted every
# time a group of 7 bits is shifted out.  Therefore each integer can be
# represented in exactly one way, and each representation stands for exactly
# one integer.
#
# Another nice property of this encoding is that it provides a compact
# representation of values that are typically used to indicate sizes.  For
# example, the values 0 - 127 are represented with a single byte, 128 - 16511
# with two bytes, and 16512 - 2113663 with three bytes.
#
# While the encoding allows arbitrarily large integers, it is artificially
# limited in this code to an unsigned 64-bit integer for efficiency purposes.
#
# Example encodings:
#           0 -> [0x00]
#         127 -> [0x7f]                 * Max 1-byte value
#         128 -> [0x80 0x00]
#         129 -> [0x80 0x01]
#         255 -> [0x80 0x7f]
#         256 -> [0x81 0x00]
#       16511 -> [0xff 0x7f]            * Max 2-byte value
#       16512 -> [0x80 0x80 0x00]
#       32895 -> [0x80 0xff 0x7f]
#     2113663 -> [0xff 0xff 0x7f]       * Max 3-byte value
#   270549119 -> [0xff 0xff 0xff 0x7f]  * Max 4-byte value
#      2^64-1 -> [0x80 0xfe 0xfe 0xfe 0xfe 0xfe 0xfe 0xfe 0xfe 0x7f]
#
# References:
#   https:#en.wikipedia.org/wiki/Variable-length_quantity
#   http:#www.codecodex.com/wiki/Variable-Length_Integers
# -----------------------------------------------------------------------------

# serializeSizeVLQ returns the number of bytes it would take to serialize the
# passed number as a variable-length quantity according to the format described
# above.

# serializeSizeVLQ returns the number of bytes it would take to serialize the
# passed number as a variable-length quantity according to the format described
# above.
def serialize_size_vlq(n: int) -> int:
    size = 1
    while n > 0x7f:
        size += 1
        n = (n >> 7) - 1
    return size


# putVLQ serializes the provided number to a variable-length quantity according
# to the format described above and returns the number of bytes of the encoded
# value.  The result is placed directly into the passed byte slice which must
# be at least large enough to handle the number of bytes returned by the
# serializeSizeVLQ function or it will panic.
def put_vlq(target: bytearray, n: int) -> int:
    """Notice, here change the passed target , so target should be bytearray, not bytes"""
    offset = 0
    while True:
        # The high bit is set when another byte follows.
        high_bit_mask = 0x80
        if offset == 0:
            high_bit_mask = 0x00

        target[offset] = n & 0x7f | high_bit_mask
        if n <= 0x7f:
            break
        n = (n >> 7) - 1

        offset += 1

    # Reverse the bytes so it is MSB-encoded.
    target.reverse()
    return offset + 1


# deserializeVLQ deserializes the provided variable-length quantity according
# to the format described above.  It also returns the number of bytes
# deserialized.
def deserialize_vlq(serialized: bytes) -> (int, int):
    n = 0
    size = 0
    for val in serialized:
        size += 1
        n = (n << 7) | (val & 0x7f)
        if val & 0x80 != 0x80:
            break
        n += 1
    return n, size
