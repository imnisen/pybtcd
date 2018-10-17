from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.ecdsa import Signature


class Sig(Signature):
    def __init__(self, r, s):
        super(Sig, self).__init__(r=r, s=s)

    def __eq__(self, other):
        return self.r == other.r and self.s == other.s


class PublicKey(VerifyingKey):
    def __init__(self, _error__please_use_generate=None):
        super(PublicKey, self).__init__(_error__please_use_generate=_error__please_use_generate)

    def __eq__(self, other):
        return self.to_string() == other.to_string()


class PrivateKey(SigningKey):
    def __init__(self, _error__please_use_generate=None):
        super(PrivateKey, self).__init__(_error__please_use_generate=_error__please_use_generate)

    def __eq__(self, other):
        return self.to_string() == other.to_string()
