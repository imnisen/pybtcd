from database.error import *

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
