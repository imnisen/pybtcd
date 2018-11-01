from database.error import *
import crcmod

def byte_compare(b1, b2: bytes) -> int:
    if b1 > b2:
        return 1
    elif b1 == b2:
        return 0
    else:
        return -1


# convertErr converts the passed leveldb error into a database error with an
# equivalent error code  and the passed description.  It also sets the passed
# error as the underlying error.
def convert_err(msg, ldb_err):
    # Use the driver-specific error code by default.  The code below will
    # update this with the converted error if it's recognized.
    code = ErrorCode.ErrDriverSpecific

    # TODO

    return DBError(code, msg, ldb_err)


# Predefined polynomials in Golang.
# const (
#         // IEEE is by far and away the most common CRC-32 polynomial.
#         // Used by ethernet (IEEE 802.3), v.42, fddi, gzip, zip, png, ...
#         IEEE = 0xedb88320
#
#         // Castagnoli's polynomial, used in iSCSI.
#         // Has better error detection characteristics than IEEE.
#         // https://dx.doi.org/10.1109/26.231911
#         Castagnoli = 0x82f63b78
#
#         // Koopman's polynomial.
#         // Also has better error detection characteristics than IEEE.
#         // https://dx.doi.org/10.1109/DSN.2002.1028931
#         Koopman = 0xeb31d82e
# )

Castagnoli = 0x82f63b78

# I don't know how the poly is defined in crcmod,
# Just write this test func to do transfer from golang polynomials to crcmod polynomials
def magic_transfer(p):
    """Transfer to strange poly in crcmod """
    return int('{:032b}1'.format(p)[::-1], 2)

crc32_Castagnoli = crcmod.mkCrcFun(magic_transfer(Castagnoli), initCrc=0, xorOut=0xFFFFFFFF)
