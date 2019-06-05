bech32_charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


# TOCHECK 这里要求每一个byte值的大小在32以内，但实际上data有这个限制吗？
# 注意到，segwit address生成的时候，每5个bit组成一组，所以大小是在32以内的
# 所以bech32编码不适用在一般的bytes加密吗？
# toChars converts the byte slice 'data' to a string where each byte in 'data'
# encodes the index of a character in 'charset'.
def to_chars(data: bytes) -> str:
    result = ""
    for b in data:
        if b >= len(bech32_charset):
            raise Exception("invalid data byte: %s" % b)
        result += bech32_charset[b]
    return result


def to_bytes(chars: str) -> bytes:
    pass


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
