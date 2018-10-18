from .utils import *
from ecdsa import VerifyingKey, SECP256k1
from ecdsa.util import number_to_string
from ecdsa.ellipticcurve import Point
from ecdsa.ecdsa import point_is_valid
from .error import *

PubkeyCompressed = 0x2  # y_bit + x coord
PubkeyUncompressed = 0x4  # x coord + y coord
PubkeyHybrid = 0x6  # y_bit + x coord + y coord

PubKeyBytesLenCompressed = 33
PubKeyBytesLenUncompressed = 65
PubKeyBytesLenHybrid = 65


class PublicKey(VerifyingKey):
    def __init__(self, _error__please_use_generate=None):
        super(PublicKey, self).__init__(_error__please_use_generate=_error__please_use_generate)

    def __eq__(self, other):
        return self.to_string() == other.to_string()

    def serialize_uncompressed(self):
        # TOCHECK TODO
        return bytes([PubkeyUncompressed]) + \
               int_to_bytes(super(PublicKey, self).pubkey.point.x()).rjust(32, b'\x00') + \
               int_to_bytes(self.pubkey.point.y()).rjust(32, b'\x00')

    # ecdsa method
    def serialize_uncompressed2(self):
        # TOCHECK TODO
        return bytes([PubkeyUncompressed]) + self.to_string()

    def serialize_compressed(self):
        y = self.pubkey.point.y()
        if y & 1:  # odd
            prefix = PubkeyCompressed | 0x1
        else:
            prefix = PubkeyCompressed
        return bytes([prefix]) + int_to_bytes(super(PublicKey, self).pubkey.point.x()).rjust(32, b'\x00')

    # ecdsa method
    def serialize_compressed2(self):
        y = self.pubkey.point.y()

        if y & 1:  # odd
            prefix = PubkeyCompressed | 0x1
        else:
            prefix = PubkeyCompressed

        order = self.pubkey.oder

        return bytes([prefix]) + number_to_string(y, order)

    def serialize_hybrid(self):
        y = self.pubkey.point.y()
        if y & 1:  # odd
            prefix = PubkeyCompressed | 0x1
        else:
            prefix = PubkeyCompressed
        return bytes([prefix]) + \
               int_to_bytes(super(PublicKey, self).pubkey.point.x()).rjust(32, b'\x00') + \
               int_to_bytes(self.pubkey.point.y()).rjust(32, b'\x00')

    # ecdsa method
    def serialize_hybrid2(self):
        y = self.pubkey.point.y()
        if y & 1:  # odd
            prefix = PubkeyCompressed | 0x1
        else:
            prefix = PubkeyCompressed
        return bytes([prefix]) + self.to_string()


def decompress_point(curve, x, ybit: bool):
    p = curve.curve.p()
    b = curve.curve.b()
    y = pow(((pow_mod(x, 3, p) + b) % p), (p + 1) // 4, p)

    if ybit != ((y % 2) != 0):
        y = -y % p

    if ybit != ((y % 2) != 0):
        msg = "ybit doesn't match oddness"
        raise PubKeyYbitOddnessErr(msg)
    return y


# ParsePubKey parses a public key for a koblitz curve from a bytestring into a
# ecdsa.Publickey, verifying that it is valid. It supports compressed,
# uncompressed and hybrid signature formats.
def parse_pub_key(pub_key_str, curve):
    """

    :param bytes pub_key_str:
    :param curve:
    :return:
    """
    # pub_key_str = pub_key_str.encode()

    pub_key_len = len(pub_key_str)
    if pub_key_len == 0:
        msg = "pubkey string is empty"
        raise PubKeyLenErr(msg)

    prefix = pub_key_str[0]
    ybit = ((prefix & 0x1) == 0x1)
    prefix &= ~0x1

    if pub_key_len == PubKeyBytesLenUncompressed:
        if prefix not in (PubkeyUncompressed, PubkeyHybrid):
            msg = "invalid magic in pubkey str %s" % pub_key_str[0]
            raise PubKeyInValidMagicErr(msg)

        x = bytes_to_int(pub_key_str[1:33])
        y = bytes_to_int(pub_key_str[33:])

        if prefix == PubkeyHybrid and ybit != (y & 1):
            msg = "ybit doesn't match oddness"
            raise PubKeyYbitOddnessErr(msg)

    elif pub_key_len == PubKeyBytesLenCompressed:
        if prefix != PubkeyCompressed:
            msg = "invalid magic in compressed pubkey string: %s" % pub_key_str[0]
            raise PubKeyInValidMagicErr(msg)
        x = bytes_to_int(pub_key_str[1:33])
        y = decompress_point(curve, x, ybit)
    else:
        msg = "invalid pub key length %d" % pub_key_len
        raise PubKeyLenErr(msg)

    # some checker
    point_is_valid(curve.generator, x, y)

    point = Point(curve.curve, x, y, curve.order)
    return PublicKey.from_public_point(point, curve)  # TOCHECK hashfunc the default is sha1


def s256():
    return SECP256k1
