class PubKeyLenErr(Exception):
    def __init__(self, msg=""):
        self.msg = msg


class PubKeyInValidMagicErr(Exception):
    def __init__(self, msg=""):
        self.msg = msg


class PubKeyYbitOddnessErr(Exception):
    def __init__(self, msg=""):
        self.msg = msg



class ErrNegativeValue(Exception):
    pass


class ErrExcessivelyPaddedValue(Exception):
    pass


# ****************
# Signature related error
# ****************

class SigMalformedTooShortErr(Exception):
    pass


class SigMalformedNoHeaderMagicErr(Exception):
    pass


class SigMalformedBadLenErr(Exception):
    pass


class SigMalformedNoFirstMarkerErr(Exception):
    pass


class SigMalformedBogusRLenErr(Exception):
    pass


class SigMalformedNoSecondMarkerErr(Exception):
    pass


class SigMalformedBogusSLenErr(Exception):
    pass


class SigMalformedBadFinalLenErr(Exception):
    pass


class SigRNotPositiveErr(Exception):
    pass


class SigSNotPositiveErr(Exception):
    pass


class SigRTooBigErr(Exception):
    pass


class SigSTooBigErr(Exception):
    pass


class SigRNegativeErr(Exception):
    pass

class SigSNegativeErr(Exception):
    pass


class SigRExcessivelyPaddedValueErr(Exception):
    pass

class SigSExcessivelyPaddedValueErr(Exception):
    pass
