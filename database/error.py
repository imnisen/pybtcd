from enum import Enum


# ErrorCode identifies a kind of error.
class ErrorCode(Enum):
    # **************************************
    # Errors related to driver registration.
    # **************************************

    # ErrDbTypeRegistered indicates two different database drivers
    # attempt to register with the name database type.
    ErrDbTypeRegistered = 0

    # *************************************
    # Errors related to database functions.
    # *************************************

    # ErrDbUnknownType indicates there is no driver registered for
    # the specified database type.
    ErrDbUnknownType = 1

    # ErrDbDoesNotExist indicates open is called for a database that
    # does not exist.
    ErrDbDoesNotExist = 2

    # ErrDbExists indicates create is called for a database that
    # already exists.
    ErrDbExists = 3

    # ErrDbNotOpen indicates a database instance is accessed before
    # it is opened or after it is closed.
    ErrDbNotOpen = 4

    # ErrDbAlreadyOpen indicates open was called on a database that
    # is already open.
    ErrDbAlreadyOpen = 5

    # ErrInvalid indicates the specified database is not valid.
    ErrInvalid = 6

    # ErrCorruption indicates a checksum failure occurred which invariably
    # means the database is corrupt.
    ErrCorruption = 7

    # ****************************************
    # Errors related to database transactions.
    # ****************************************

    # ErrTxClosed indicates an attempt was made to commit or rollback a
    # transaction that has already had one of those operations performed.
    ErrTxClosed = 8

    # ErrTxNotWritable indicates an operation that requires write access to
    # the database was attempted against a read-only transaction.
    ErrTxNotWritable = 9

    # **************************************
    # Errors related to metadata operations.
    # **************************************

    # ErrBucketNotFound indicates an attempt to access a bucket that has
    # not been created yet.
    ErrBucketNotFound = 10

    # ErrBucketExists indicates an attempt to create a bucket that already
    # exists.
    ErrBucketExists = 11

    # ErrBucketNameRequired indicates an attempt to create a bucket with a
    # blank name.
    ErrBucketNameRequired = 12

    # ErrKeyRequired indicates at attempt to insert a zero-length key.
    ErrKeyRequired = 13

    # ErrKeyTooLarge indicates an attmempt to insert a key that is larger
    # than the max allowed key size.  The max key size depends on the
    # specific backend driver being used.  As a general rule, key sizes
    # should be relatively, so this should rarely be an issue.
    ErrKeyTooLarge = 14

    # ErrValueTooLarge indicates an attmpt to insert a value that is larger
    # than max allowed value size.  The max key size depends on the
    # specific backend driver being used.
    ErrValueTooLarge = 15

    # ErrIncompatibleValue indicates the value in question is invalid for
    # the specific requested operation.  For example, trying create or
    # delete a bucket with an existing non-bucket key, attempting to create
    # or delete a non-bucket key with an existing bucket key, or trying to
    # delete a value via a cursor when it points to a nested bucket.
    ErrIncompatibleValue = 16

    # ***************************************
    # Errors related to block I/O operations.
    # ***************************************

    # ErrBlockNotFound indicates a block with the provided hash does not
    # exist in the database.
    ErrBlockNotFound = 17

    # ErrBlockExists indicates a block with the provided hash already
    # exists in the database.
    ErrBlockExists = 18

    # ErrBlockRegionInvalid indicates a region that exceeds the bounds of
    # the specified block was requested.  When the hash provided by the
    # region does not correspond to an existing block, the error will be
    # ErrBlockNotFound instead.
    ErrBlockRegionInvalid = 19

    # ***********************************
    # Support for driver-specific errors.
    # ***********************************

    # ErrDriverSpecific indicates the Err field is a driver-specific error.
    # This provides a mechanism for drivers to plug-in their own custom
    # errors for any situations which aren't already covered by the error
    # codes provided by this package.
    ErrDriverSpecific = 20

    # numErrorCodes is the maximum error code number used in tests.
    numErrorCodes = 21

    def __str__(self):
        return errorCodeStrings[self]


errorCodeStrings = {

    ErrorCode.ErrDbTypeRegistered: "ErrDbTypeRegistered",
    ErrorCode.ErrDbUnknownType: "ErrDbUnknownType",
    ErrorCode.ErrDbDoesNotExist: "ErrDbDoesNotExist",
    ErrorCode.ErrDbExists: "ErrDbExists",
    ErrorCode.ErrDbNotOpen: "ErrDbNotOpen",
    ErrorCode.ErrDbAlreadyOpen: "ErrDbAlreadyOpen",
    ErrorCode.ErrInvalid: "ErrInvalid",
    ErrorCode.ErrCorruption: "ErrCorruption",
    ErrorCode.ErrTxClosed: "ErrTxClosed",
    ErrorCode.ErrTxNotWritable: "ErrTxNotWritable",
    ErrorCode.ErrBucketNotFound: "ErrBucketNotFound",
    ErrorCode.ErrBucketExists: "ErrBucketExists",
    ErrorCode.ErrBucketNameRequired: "ErrBucketNameRequired",
    ErrorCode.ErrKeyRequired: "ErrKeyRequired",
    ErrorCode.ErrKeyTooLarge: "ErrKeyTooLarge",
    ErrorCode.ErrValueTooLarge: "ErrValueTooLarge",
    ErrorCode.ErrIncompatibleValue: "ErrIncompatibleValue",
    ErrorCode.ErrBlockNotFound: "ErrBlockNotFound",
    ErrorCode.ErrBlockExists: "ErrBlockExists",
    ErrorCode.ErrBlockRegionInvalid: "ErrBlockRegionInvalid",
    ErrorCode.ErrDriverSpecific: "ErrDriverSpecific",
}


class DBError(Exception):
    def __init__(self, c, desc=None, err=None):
        """

        :param ErrorCode c:
        :param str desc:
        """

        self.c = c
        self.desc = desc or ""
        self.err = err

    def __eq__(self, other):
        return self.c == other.c and self.desc == other.desc

    def __repr__(self):
        return "ScriptError(ErrorCode={}, desc={})".format(str(self.c), self.desc or "\"\"")

    def __str__(self):
        return "ScriptError(ErrorCode={}, desc={})".format(str(self.c), self.desc or "\"\"")

    def __hash__(self):
        return hash(str(self.c) + str(self.desc))
