class PubKeyLenErr(Exception):
    def __init__(self, msg=""):
        self.msg = msg


class PubKeyInValidMagicErr(Exception):
    def __init__(self, msg=""):
        self.msg = msg

class PubKeyYbitOddnessErr(Exception):
    def __init__(self, msg=""):
        self.msg = msg
