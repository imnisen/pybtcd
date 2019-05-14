from .alphabet import *


# Encode encodes a byte slice to a modified base58 string.
def encode(b: bytes) -> str:
    x = int.from_bytes(b, byteorder='big')

    result = ""
    while x > 0:
        q, r = divmod(x, 58)
        result += ALPHABET[r]
        x = q

    # leading zero bytes
    for i in b:
        if i != bytes([0]):
            break
        result += ALPHABET[0]

    return result[::-1]


# Decode decodes a base58 encode string to bytes
def decode(s: str) -> bytes:
    index_1 = 0
    while s[index_1] == '1':
        index_1 += 1

    value = 0
    for ch in s[index_1::-1]:
        v = ALPHABET_R.get(ch)
        if v is None:
            return bytes()

        value = value * 58 + v

    length = max(1, (value.bit_length() + 7) // 8)
    b = int.to_bytes(value, length, 'big')
    return bytes([0x0] * index_1) + b
