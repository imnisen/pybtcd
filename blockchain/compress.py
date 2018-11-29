import txscript
import btcec
from .error import *


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
    i, j = 0, offset
    while i < j:
        target[i], target[j] = target[j], target[i]
        i += 1
        j -= 1
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


# -----------------------------------------------------------------------------
# In order to reduce the size of stored scripts, a domain specific compression
# algorithm is used which recognizes standard scripts and stores them using
# less bytes than the original script.  The compression algorithm used here was
# obtained from Bitcoin Core, so all credits for the algorithm go to it.
#
# The general serialized format is:
#
#   <script size or type><script data>
#
#   Field                 Type     Size
#   script size or type   VLQ      variable
#   script data           []byte   variable
#
# The specific serialized format for each recognized standard script is:
#
# - Pay-to-pubkey-hash: (21 bytes) - <0><20-byte pubkey hash>
# - Pay-to-script-hash: (21 bytes) - <1><20-byte script hash>
# - Pay-to-pubkey**:    (33 bytes) - <2, 3, 4, or 5><32-byte pubkey X value>
#   2, 3 = compressed pubkey with bit 0 specifying the y coordinate to use
#   4, 5 = uncompressed pubkey with bit 0 specifying the y coordinate to use
#   ** Only valid public keys starting with 0x02, 0x03, and 0x04 are supported.
#
# Any scripts which are not recognized as one of the aforementioned standard
# scripts are encoded using the general serialized format and encode the script
# size as the sum of the actual size of the script and the number of special
# cases.
# -----------------------------------------------------------------------------

# The following constants specify the special constants used to identify a
# special script type in the domain-specific compressed script encoding.
#
# NOTE: This section specifically does not use iota since these values are
# serialized and must be stable for long-term storage.

# cstPayToPubKeyHash identifies a compressed pay-to-pubkey-hash script.
cstPayToPubKeyHash = 0

# cstPayToScriptHash identifies a compressed pay-to-script-hash script.
cstPayToScriptHash = 1

# cstPayToPubKeyComp2 identifies a compressed pay-to-pubkey script to
# a compressed pubkey.  Bit 0 specifies which y-coordinate to use
# to reconstruct the full uncompressed pubkey.
cstPayToPubKeyComp2 = 2

# cstPayToPubKeyComp3 identifies a compressed pay-to-pubkey script to
# a compressed pubkey.  Bit 0 specifies which y-coordinate to use
# to reconstruct the full uncompressed pubkey.
cstPayToPubKeyComp3 = 3

# cstPayToPubKeyUncomp4 identifies a compressed pay-to-pubkey script to
# an uncompressed pubkey.  Bit 0 specifies which y-coordinate to use
# to reconstruct the full uncompressed pubkey.
cstPayToPubKeyUncomp4 = 4

# cstPayToPubKeyUncomp5 identifies a compressed pay-to-pubkey script to
# an uncompressed pubkey.  Bit 0 specifies which y-coordinate to use
# to reconstruct the full uncompressed pubkey.
cstPayToPubKeyUncomp5 = 5

# numSpecialScripts is the number of special scripts recognized by the
# domain-specific script compression algorithm.
numSpecialScripts = 6


# isPubKeyHash returns whether or not the passed public key script is a
# standard pay-to-pubkey-hash script along with the pubkey hash it is paying to
# if it is.
def is_pub_key_hash(script: bytes) -> (bool, bytes or None):
    if len(script) == 25 and \
                    script[0] == txscript.OP_DUP and \
                    script[1] == txscript.OP_HASH160 and \
                    script[2] == txscript.OP_DATA_20 and \
                    script[23] == txscript.OP_EQUALVERIFY and \
                    script[24] == txscript.OP_CHECKSIG:
        return True, script[3:23]
    else:
        return False, None


# isScriptHash returns whether or not the passed public key script is a
# standard pay-to-script-hash script along with the script hash it is paying to
# if it is.
def is_script_hash(script: bytes) -> (bool, bytes):
    if len(script) == 23 and \
                    script[0] == txscript.OP_HASH160 and \
                    script[1] == txscript.OP_DATA_20 and \
                    script[22] == txscript.OP_EQUAL:
        return True, script[2:22]
    else:
        return False, None


# isPubKey returns whether or not the passed public key script is a standard
# pay-to-pubkey script that pays to a valid compressed or uncompressed public
# key along with the serialized pubkey it is paying to if it is.
#
# NOTE: This function ensures the public key is actually valid since the
# compression algorithm requires valid pubkeys.  It does not support hybrid
# pubkeys.  This means that even if the script has the correct form for a
# pay-to-pubkey script, this function will only return true when it is paying
# to a valid compressed or uncompressed pubkey.
def is_pub_key(script: bytes) -> (bool, bytes or None):
    # Pay-to-compressed-pubkey script.
    if len(script) == 35 and \
                    script[0] == txscript.OP_DATA_33 and \
                    script[34] == txscript.OP_CHECKSIG and \
            (script[1] == 0x02 or script[1] == 0x03):
        # Ensure the public key is valid.
        serialized_pub_key = script[1:34]
        btcec.parse_pub_key(serialized_pub_key, btcec.s256())
        return True, serialized_pub_key

    # Pay-to-uncompressed-pubkey script.
    if len(script) == 67 and \
                    script[0] == txscript.OP_DATA_65 and \
                    script[66] == txscript.OP_CHECKSIG and \
                    script[1] == 0x04:
        # Ensure the public key is valid.
        serialized_pub_key = script[1:66]
        btcec.parse_pub_key(serialized_pub_key, btcec.s256())
        return True, serialized_pub_key

    return False, None


# compressedScriptSize returns the number of bytes the passed script would take
# when encoded with the domain specific compression algorithm described above.
def compressed_script_size(pk_script: bytes):
    valid, _ = is_pub_key_hash(pk_script)
    if valid:
        return 21

    valid, _ = is_script_hash(pk_script)
    if valid:
        return 21

    valid, _ = is_pub_key(pk_script)
    if valid:
        return 33

    # When none of the above special cases apply, encode the script as is
    # preceded by the sum of its size and the number of special cases
    # encoded as a variable length quantity.
    return serialize_size_vlq(len(pk_script) + numSpecialScripts) + len(pk_script)


# decodeCompressedScriptSize treats the passed serialized bytes as a compressed
# script, possibly followed by other data, and returns the number of bytes it
# occupies taking into account the special encoding of the script size by the
# domain specific compression algorithm described above.
def decode_compressed_script_size(serialized: bytes) -> int:
    script_size, bytes_read = deserialize_vlq(serialized)
    if bytes_read == 0:
        return 0

    if script_size == cstPayToPubKeyHash:
        return 21
    elif script_size == cstPayToScriptHash:
        return 21
    elif script_size in (cstPayToPubKeyComp2, cstPayToPubKeyComp3, cstPayToPubKeyUncomp4, cstPayToPubKeyUncomp5):
        return 33

    script_size -= numSpecialScripts
    script_size += bytes_read
    return script_size


# putCompressedScript compresses the passed script according to the domain
# specific compression algorithm described above directly into the passed
# target byte slice.  The target byte slice must be at least large enough to
# handle the number of bytes returned by the compressedScriptSize function or
# it will panic.
def put_compressed_script(target: bytearray, pk_script: bytes) -> int:
    # Pay-to-pubkey-hash script.
    valid, hash = is_pub_key_hash(pk_script)
    if valid:
        target[0] = cstPayToPubKeyHash
        target[1:21] = hash
        return 21

    # Pay-to-script-hash script.
    valid, hash = is_script_hash(pk_script)
    if valid:
        target[0] = cstPayToScriptHash
        target[1:21] = hash
        return 21

    # Pay-to-pubkey (compressed or uncompressed) script.
    valid, serialized_pub_key = is_pub_key(pk_script)
    if valid:
        pub_key_format = serialized_pub_key[0]
        if pub_key_format in (0x02, 0x03):
            target[0] = pub_key_format
            target[1:33] = serialized_pub_key[1:33]
            return 33
        elif pub_key_format == 0x04:
            # Encode the oddness of the serialized pubkey into the
            # compressed script type.
            target[0] = pub_key_format | (serialized_pub_key[64] & 0x01)
            target[1:33] = serialized_pub_key[1:33]
            return 33

    # When none of the above special cases apply, encode the unmodified
    # script preceded by the sum of its size and the number of special
    # cases encoded as a variable length quantity.
    encode_size = len(pk_script) + numSpecialScripts
    vlq_size_len = put_vlq(target, encode_size)
    target[vlq_size_len:] = pk_script
    return vlq_size_len + len(pk_script)


# decompressScript returns the original script obtained by decompressing the
# passed compressed script according to the domain specific compression
# algorithm described above.
#
# NOTE: The script parameter must already have been proven to be long enough
# to contain the number of bytes returned by decodeCompressedScriptSize or it
# will panic.  This is acceptable since it is only an internal function.
def decompress_script(compressed_pk_script: bytes) -> bytes:
    # In practice this function will not be called with a zero-length or
    # nil script since the nil script encoding includes the length, however
    # the code below assumes the length exists, so just return nil now if
    # the function ever ends up being called with a nil script in the
    # future.
    if len(compressed_pk_script) == 0:
        return bytes()

    # Decode the script size and examine it for the special cases.
    encoded_script_size, bytes_read = deserialize_vlq(compressed_pk_script)

    # Pay-to-pubkey-hash script.  The resulting script is:
    # <OP_DUP><OP_HASH160><20 byte hash><OP_EQUALVERIFY><OP_CHECKSIG>
    if encoded_script_size == cstPayToPubKeyHash:
        pk_script = bytearray(25)
        pk_script[0] = txscript.OP_DUP
        pk_script[1] = txscript.OP_HASH160
        pk_script[2] = txscript.OP_DATA_20
        pk_script[3:23] = compressed_pk_script[bytes_read: bytes_read + 20]
        pk_script[23] = txscript.OP_EQUALVERIFY
        pk_script[24] = txscript.OP_CHECKSIG
        return bytes(pk_script)

    # Pay-to-script-hash script.  The resulting script is:
    # <OP_HASH160><20 byte script hash><OP_EQUAL>
    elif encoded_script_size == cstPayToScriptHash:
        pk_script = bytearray(23)
        pk_script[0] = txscript.OP_HASH160
        pk_script[1] = txscript.OP_DATA_20
        pk_script[2:22] = compressed_pk_script[bytes_read: bytes_read + 20]
        pk_script[22] = txscript.OP_EQUAL
        return bytes(pk_script)
    # Pay-to-compressed-pubkey script.  The resulting script is:
    # <OP_DATA_33><33 byte compressed pubkey><OP_CHECKSIG>
    elif encoded_script_size in (cstPayToPubKeyComp2, cstPayToPubKeyComp3):
        pk_script = bytearray(35)
        pk_script[0] = txscript.OP_DATA_33
        pk_script[1] = encoded_script_size
        pk_script[2:34] = compressed_pk_script[bytes_read: bytes_read + 32]
        pk_script[34] = txscript.OP_CHECKSIG
        return bytes(pk_script)

    # Pay-to-uncompressed-pubkey script.  The resulting script is:
    # <OP_DATA_65><65 byte uncompressed pubkey><OP_CHECKSIG>
    elif encoded_script_size in (cstPayToPubKeyUncomp4, cstPayToPubKeyUncomp5):
        # Change the leading byte to the appropriate compressed pubkey
        # identifier (0x02 or 0x03) so it can be decoded as a
        # compressed pubkey.  This really should never fail since the
        # encoding ensures it is valid before compressing to this type.
        compressed_key = bytearray(33)
        compressed_key[0] = encoded_script_size - 2
        compressed_key[1:] = compressed_pk_script[1:]
        try:
            key = btcec.parse_pub_key(bytes(compressed_key), btcec.s256())
        except Exception:
            return bytes()

        pk_script = bytearray(67)
        pk_script[0] = txscript.OP_DATA_65

        b = key.serialize_uncompressed()
        pk_script[1:1 + len(b)] = b
        pk_script[66] = txscript.OP_CHECKSIG
        return bytes(pk_script)

    # When none of the special cases apply, the script was encoded using
    # the general format, so reduce the script size by the number of
    # special cases and return the unmodified script.
    script_size = encoded_script_size - numSpecialScripts

    if script_size == 0:
        return bytes()

    pk_script = bytearray(script_size)
    pk_script[0:] = compressed_pk_script[bytes_read: bytes_read + script_size]
    return bytes(pk_script)


# -----------------------------------------------------------------------------
# In order to reduce the size of stored amounts, a domain specific compression
# algorithm is used which relies on there typically being a lot of zeroes at
# end of the amounts.  The compression algorithm used here was obtained from
# Bitcoin Core, so all credits for the algorithm go to it.
#
# While this is simply exchanging one uint64 for another, the resulting value
# for typical amounts has a much smaller magnitude which results in fewer bytes
# when encoded as variable length quantity.  For example, consider the amount
# of 0.1 BTC which is 10000000 satoshi.  Encoding 10000000 as a VLQ would take
# 4 bytes while encoding the compressed value of 8 as a VLQ only takes 1 byte.
#
# Essentially the compression is achieved by splitting the value into an
# exponent in the range [0-9] and a digit in the range [1-9], when possible,
# and encoding them in a way that can be decoded.  More specifically, the
# encoding is as follows:
# - 0 is 0
# - Find the exponent, e, as the largest power of 10 that evenly divides the
#   value up to a maximum of 9
# - When e < 9, the final digit can't be 0 so store it as d and remove it by
#   dividing the value by 10 (call the result n).  The encoded value is thus:
#   1 + 10*(9*n + d-1) + e
# - When e==9, the only thing known is the amount is not 0.  The encoded value
#   is thus:
#   1 + 10*(n-1) + e   ==   10 + 10*(n-1)
#
# Example encodings:
# (The numbers in parenthesis are the number of bytes when serialized as a VLQ)
#            0 (1) -> 0        (1)           *  0.00000000 BTC
#         1000 (2) -> 4        (1)           *  0.00001000 BTC
#        10000 (2) -> 5        (1)           *  0.00010000 BTC
#     12345678 (4) -> 111111101(4)           *  0.12345678 BTC
#     50000000 (4) -> 47       (1)           *  0.50000000 BTC
#    100000000 (4) -> 9        (1)           *  1.00000000 BTC
#    500000000 (5) -> 49       (1)           *  5.00000000 BTC
#   1000000000 (5) -> 10       (1)           * 10.00000000 BTC
# -----------------------------------------------------------------------------

# compressTxOutAmount compresses the passed amount according to the domain
# specific compression algorithm described above.
def compress_tx_out_amount(amount: int) -> int:
    # No need to do any work if it's zero.
    if amount == 0:
        return 0

    # Find the largest power of 10 (max of 9) that evenly divides the
    # value.
    exponent = 0
    while amount % 10 == 0 and exponent < 9:
        amount //= 10
        exponent += 1

    # The compressed result for exponents less than 9 is:
    # 1 + 10*(9*n + d-1) + e
    if exponent < 9:
        last_digit = amount % 10
        amount //= 10
        return 1 + 10 * (9 * amount + last_digit - 1) + exponent

    # The compressed result for an exponent of 9 is:
    # 1 + 10*(n-1) + e   ==   10 + 10*(n-1)
    return 10 + 10 * (amount - 1)


# decompressTxOutAmount returns the original amount the passed compressed
# amount represents according to the domain specific compression algorithm
# described above.
def decompress_tx_out_amount(amount: int) -> int:
    # No need to do any work if it's zero.
    if amount == 0:
        return 0

    # The decompressed amount is either of the following two equations:
    # x = 1 + 10*(9*n + d - 1) + e
    # x = 1 + 10*(n - 1)       + 9
    amount -= 1

    # The decompressed amount is now one of the following two equations:
    # x = 10*(9*n + d - 1) + e
    # x = 10*(n - 1)       + 9
    exponent = amount % 10
    amount //= 10

    # The decompressed amount is now one of the following two equations:
    # x = 9*n + d - 1  | where e < 9
    # x = n - 1        | where e = 9
    n = 0
    if exponent < 9:
        last_digit = amount % 9 + 1
        amount //= 9
        n = amount * 10 + last_digit  # TOCHECK why?
    else:
        n = amount + 1

    # Apply the exponent
    while exponent > 0:
        n *= 10
        exponent -= 1

    return n


# -----------------------------------------------------------------------------
# Compressed transaction outputs consist of an amount and a public key script
# both compressed using the domain specific compression algorithms previously
# described.
#
# The serialized format is:
#
#   <compressed amount><compressed script>
#
#   Field                 Type     Size
#     compressed amount   VLQ      variable
#     compressed script   []byte   variable
# -----------------------------------------------------------------------------

# compressedTxOutSize returns the number of bytes the passed transaction output
# fields would take when encoded with the format described above.
def compress_tx_out_size(amount: int, pk_script: bytes) -> int:
    return serialize_size_vlq(compress_tx_out_amount(amount)) + compressed_script_size(pk_script)


# putCompressedTxOut compresses the passed amount and script according to their
# domain specific compression algorithms and encodes them directly into the
# passed target byte slice with the format described above.  The target byte
# slice must be at least large enough to handle the number of bytes returned by
# the compressedTxOutSize function or it will panic.
def put_compressed_tx_out(target: bytearray, amount: int, pk_script: bytes) -> int:
    offset = put_vlq(target, compress_tx_out_amount(amount))

    # do some trick as slice don't pass as pointer
    amount_offset = offset
    target_slice = target[amount_offset:]

    offset += put_compressed_script(target_slice, pk_script)  # TODO check [:] pass
    target[amount_offset:] = target_slice
    return offset


# decodeCompressedTxOut decodes the passed compressed txout, possibly followed
# by other data, into its uncompressed amount and script and returns them along
# with the number of bytes they occupied prior to decompression
def decode_compressed_tx_out(serialized: bytes) -> (int, bytes, int):
    # Deserialize the compressed amount and ensure there are bytes
    # remaining for the compressed script.
    compressed_amount, bytes_read = deserialize_vlq(serialized)
    if bytes_read >= len(serialized):
        msg = "unexpected end of data after compressed amount"
        raise DeserializeError(msg=msg)

    # Decode the compressed script size and ensure there are enough bytes
    # left in the slice for it.
    script_size = decode_compressed_script_size(serialized[bytes_read:])
    if len(serialized[bytes_read:]) < script_size:
        msg = "unexpected end of data after script size"
        raise DeserializeError(msg=msg)

    # Decompress and return the amount and script.
    amount = decompress_tx_out_amount(compressed_amount)
    script = decompress_script(serialized[bytes_read: bytes_read + script_size])
    return amount, script, bytes_read + script_size
