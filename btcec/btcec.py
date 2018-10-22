from ecdsa import SigningKey, VerifyingKey, SECP256k1



class PrivateKey(SigningKey):
    def __init__(self, _error__please_use_generate=None):
        super(PrivateKey, self).__init__(_error__please_use_generate=_error__please_use_generate)

    def __eq__(self, other):
        return self.to_string() == other.to_string()
