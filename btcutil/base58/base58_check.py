import btcec
from .base58 import encode, decode


# ErrChecksum indicates that the checksum of a check-encoded string does not verify against
# the checksum.
class ErrChecksum(Exception):
    # "checksum error"
    pass


# ErrInvalidFormat indicates that the check-encoded string has an invalid format.
class ErrInvalidFormat(Exception):
    # "invalid format: version and/or checksum bytes missing"
    pass


# for one byte, order is not important
IGNORE_ORDER = 'little'


# checksum: first four bytes of sha256^2
def checksum(b: bytes) -> bytes:
    return btcec.sha256(btcec.sha256(b))[:4]


# CheckEncode prepends a version byte and appends a four byte checksum.
def check_encode(b: bytes, version: int) -> str:
    """

    :param b:
    :param version: version is one byte
    :return:
    """
    # version_byte = version.to_bytes(1, IGNORE_ORDER)
    version_byte = bytes([version])
    checksum_bytes = checksum(version_byte + b)
    return encode(version_byte + b + checksum_bytes)


# CheckDecode decodes a string that was encoded with CheckEncode and verifies the checksum.
def check_decode(s: str) -> (bytes, int):
    decoded = decode(s)
    if len(decoded) < 5:
        raise ErrInvalidFormat

    # version = int.from_bytes(decoded[0], IGNORE_ORDER)
    version = decoded[0]
    cksum = decoded[-4:]
    if checksum(decoded[:-4]) != cksum:
        raise ErrChecksum

    payload = decoded[1:-4]
    return payload, version
