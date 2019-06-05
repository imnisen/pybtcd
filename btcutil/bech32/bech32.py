bech32_charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


class Bech32EncodeError(Exception):
    pass


class Bech32DecodeError(Exception):
    pass


# TOCHECK 这里要求每一个byte值的大小在32以内，但实际上data有这个限制吗？
# 注意到，segwit address生成的时候，每5个bit组成一组，所以大小是在32以内的
# 所以bech32编码不适用在一般的bytes加密吗？
# toChars converts the byte slice 'data' to a string where each byte in 'data'
# encodes the index of a character in 'charset'.
def to_chars(data: bytes) -> str:
    result = ""
    for b in data:
        if b >= len(bech32_charset):
            raise Bech32EncodeError("invalid data byte: %s" % b)
        result += bech32_charset[b]
    return result


# toBytes converts each character in the string 'chars' to the value of the
# index of the correspoding character in 'charset'.
def to_bytes(chars: str) -> bytes:
    b = bytes()
    for c in chars:
        index = index_str(bech32_charset, c)
        if index < 0:
            raise Bech32DecodeError("invalid character not part of charset: %s" % c)
        b += bytes([index])
    return b


# TODO
def convert_bits():
    pass


# Encode encodes a byte slice into a bech32 string with the
# human-readable part hrb. Note that the bytes must each encode 5 bits
# (base32).
def encode(hrp: str, data: bytes) -> str:
    # Calculate the checksum of the data and append it at the end.
    checksum = bech32_checksum(hrp, data)
    combined = data + checksum

    # The resulting bech32 string is the concatenation of the hrp, the
    # separator 1, data and checksum. Everything after the separator is
    # represented using the specified charset.
    data_chars = to_chars(combined)

    return hrp + "1" + data_chars


# Decode decodes a bech32 encoded string, returning the human-readable
# part and the data part excluding the checksum.
def decode(bech: str) -> (str, bytes):
    # The maximum allowed length for a bech32 string is 90. It must also
    # be at least 8 characters, since it needs a non-empty HRP, a
    # separator, and a 6 character checksum.
    if len(bech) < 8 or len(bech) > 90:
        raise Bech32DecodeError("invalid bech32 string length %d" % len(bech))

    # Only	ASCII characters between 33 and 126 are allowed.
    for c in bech:
        if ord(c) < 33 or ord(c) > 126:
            raise Bech32DecodeError("invalid character in string: %s" % c)

    # The characters must be either all lowercase or all uppercase.
    upper_bech = bech.upper()
    lower_bech = bech.lower()
    if bech != upper_bech and bech != lower_bech:
        raise Bech32DecodeError("string not all lowercase or all uppercase")

    # We'll work with the lowercase string from now on.
    bech = lower_bech

    # The string is invalid if the last '1' is non-existent, it is the
    # first character of the string (no human-readable part) or one of the
    # last 6 characters of the string (since checksum cannot contain '1'),
    # or if the string is more than 90 characters in total.
    one = last_index_str(bech, '1')
    if one < 1 or one + 7 > len(bech):
        raise Bech32DecodeError("invalid index of 1")

    # The human-readable part is everything before the last '1'.
    hrp = bech[:one]
    data = bech[one + 1]

    # Each character corresponds to the byte with value of the index in
    # 'charset'.
    decoded = to_bytes(data)

    # Here is for detail error info
    if not bech32_verify_checksum(hrp, decoded):
        more_info = ""
        checksum = bech[-6:]
        try:
            expected = to_chars(bech32_checksum(hrp, decoded[:-6]))
            more_info = "Expected: %s, got %s" % (expected, checksum)
        except:
            pass
        raise Bech32DecodeError("checksum failed." + more_info)

    # We exclude the last 6 bytes, which is the checksum.
    return hrp, decoded[:-6]


# LastIndexByte returns the index of the last instance of c in s, or -1 if c is not present in s.
def last_index_str(s, c):
    try:
        return s[::-1].index(c)
    except ValueError:
        return -1


def index_str(s, c):
    try:
        return s[::-1].index(c)
    except ValueError:
        return -1


############################################################################
# These method is copy from BIP 173
# For more details on the checksum calculation, please refer to BIP 173.
def bech32_checksum(hrp: str, data: bytes) -> bytes:
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = (chk >> 25)
        chk = (chk & 0x1ffffff) << 5 ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def bech32_hrp_expand(s):
    return [ord(x) >> 5 for x in s] + [0] + [ord(x) & 31 for x in s]


def bech32_verify_checksum(hrp, data):
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1

############################################################################
