from ecdsa.ecdsa import Signature as BaseSignature
from .error import *
from .utils import *

import binascii


def binary_to_number(string):
    return int(binascii.hexlify(string), 16)


class Signature(BaseSignature):
    def __init__(self, r, s):
        super(Signature, self).__init__(r=r, s=s)

    def __eq__(self, other):
        return self.r == other.r and self.s == other.s

    def verify(self, hash, pub_key):
        number = binary_to_number(hash)
        return pub_key.pubkey.verifies(number, self)


def _parse_sig(sig_str, curve, der):
    """
    Refer to:
        https://en.bitcoin.it/w/images/en/7/70/Bitcoin_OpCheckSig_InDetail.png

    :param []byte sig_str:
    :param elliptic.Curve curve:
    :param bool der:
    :return:
    """
    # Originally this code used encoding/asn1 in order to parse the
    # signature, but a number of problems were found with this approach.
    # Despite the fact that signatures are stored as DER, the difference
    # between go's idea of a bignum (and that they have sign) doesn't agree
    # with the openssl one (where they do not). The above is true as of
    # Go 1.1. In the end it was simpler to rewrite the code to explicitly
    # understand the format which is this:
    # 0x30 <length of whole message> <0x02> <length of R> <R> 0x2
    # <length of S> <S>.

    # minimal message is when both numbers are 1 bytes. adding up to:
    # 0x30 + len + 0x02 + 0x01 + <byte> + 0x2 + 0x01 + <byte>
    if len(sig_str) < 8:
        raise SigMalformedTooShortErr

    # first byte 0x30
    index = 0
    if sig_str[index] != 0x30:
        raise SigMalformedNoHeaderMagicErr

    index += 1
    sig_len = sig_str[index]

    index += 1
    if sig_len + 2 > len(sig_str):
        raise SigMalformedBadLenErr

    # trim the slice we're working on so we only look at what matters.
    sig_str = sig_str[:sig_len + 2]

    # next byte 0x02
    if sig_str[index] != 0x02:
        raise SigMalformedNoFirstMarkerErr

    index += 1

    # next byte is r length
    r_len = int(sig_str[index])
    # must be positive, must be able to fit in another 0x2, <len> <s>
    # hence the -3. We assume that the length must be at least one byte.
    index += 1
    if r_len <= 0 or r_len > len(sig_str) - index - 3:
        raise SigMalformedBogusRLenErr

    # Next is R itself
    r_bytes = sig_str[index: index + r_len]
    if der:
        try:
            canonical_padding(r_bytes)
        except ErrNegativeValue:
            raise SigRNegativeErr
        except ErrExcessivelyPaddedValue:
            raise SigRExcessivelyPaddedValueErr

    r = bytes_to_int(r_bytes)
    index += r_len

    # Next is 0x02
    if sig_str[index] != 0x02:
        raise SigMalformedNoSecondMarkerErr
    index += 1

    # Next is length of S
    s_len = int(sig_str[index])
    index += 1

    if s_len <= 0 or s_len > len(sig_str) - index:
        raise SigMalformedBogusSLenErr

    # Next is S itself
    s_bytes = sig_str[index: index + s_len]
    if der:
        try:
            canonical_padding(r_bytes)
        except ErrNegativeValue:
            raise SigSNegativeErr
        except ErrExcessivelyPaddedValue:
            raise SigSExcessivelyPaddedValueErr
    s = bytes_to_int(s_bytes)
    index += s_len

    # sanity check length parsing
    if index != len(sig_str):
        raise SigMalformedBadFinalLenErr

    # Verify also checks this, but we can be more sure that we parsed
    # correctly if we verify here too.
    # FWIW the ecdsa spec states that R and S must be | 1, N - 1 |
    # but crypto/ecdsa only checks for Sign != 0. Mirror that.

    if r <= 0:
        raise SigRNotPositiveErr
    if s <= 0:
        raise SigSNotPositiveErr

    if r >= curve.order:
        raise SigRTooBigErr

    if s >= curve.order:
        raise SigSTooBigErr
    signature = Signature(r=r, s=s)
    return signature


# ParseSignature parses a signature in BER format for the curve type `curve'
# into a Signature type, performing some basic sanity checks.  If parsing
# according to the more strict DER format is needed, use ParseDERSignature.
def parse_signature(sig_str, curve):
    return _parse_sig(sig_str, curve, der=False)


# ParseDERSignature parses a signature in DER format for the curve type
# `curve` into a Signature type.  If parsing according to the less strict
# BER format is needed, use ParseSignature.
def parse_der_signature(sig_str, curve):
    return _parse_sig(sig_str, curve, der=True)


# canonicalPadding checks whether a big-endian encoded integer could
# possibly be misinterpreted as a negative number (even though OpenSSL
# treats all numbers as unsigned), or if there is any unnecessary
# leading zero padding.
def canonical_padding(b: bytes):
    if b[0] & 0x80 == 0x80:
        raise ErrNegativeValue
    elif len(b) > 1 and b[0] == 0x00 and b[1] & 0x80 != 0x80:
        raise ErrExcessivelyPaddedValue
    else:
        pass
    return
