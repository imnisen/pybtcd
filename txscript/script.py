from enum import Enum


# SigHashType represents hash type bits at the end of a signature.
class SigHashType(Enum):
    SigHashOld = 0x0
    SigHashAll = 0x1
    SigHashNone = 0x2
    SigHashSingle = 0x3
    SigHashAnyOneCanPay = 0x80
