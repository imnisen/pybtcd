# Bucket represents a collection of key/value pairs.
class Bucket:
    # Bucket retrieves a nested bucket with the given key.  Returns nil if
    # the bucket does not exist.
    def bucket(self, key: bytes) -> 'Bucket':
        pass

    # CreateBucket creates and returns a new nested bucket with the given
    # key.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBucketExists if the bucket already exists
    #   - ErrBucketNameRequired if the key is empty
    #   - ErrIncompatibleValue if the key is otherwise invalid for the
    #     particular implementation
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    def create_bucket(self, key: bytes) -> 'Bucket':
        pass

    # CreateBucketIfNotExists creates and returns a new nested bucket with
    # the given key if it does not already exist.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBucketNameRequired if the key is empty
    #   - ErrIncompatibleValue if the key is otherwise invalid for the
    #     particular implementation
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    def create_bucket_if_not_exsit(self, key: bytes) -> 'Bucket':
        pass

    # DeleteBucket removes a nested bucket with the given key.  This also
    # includes removing all nested buckets and keys under the bucket being
    # deleted.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBucketNotFound if the specified bucket does not exist
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    def delete_bucket(self, key: bytes):
        pass

    # ForEach invokes the passed function with every key/value pair in the
    # bucket.  This does not include nested buckets or the key/value pairs
    # within those nested buckets.
    #
    # WARNING: It is not safe to mutate data while iterating with this
    # method.  Doing so may cause the underlying cursor to be invalidated
    # and return unexpected keys and/or values.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrTxClosed if the transaction has already been closed
    #
    # NOTE: The slices returned by this function are only valid during a
    # transaction.  Attempting to access them after a transaction has ended
    # results in undefined behavior.  Additionally, the slices must NOT
    # be modified by the caller.  These constraints prevent additional data
    # copies and allows support for memory-mapped database implementations.
    def for_each(self):  # TODO
        pass

    # ForEachBucket invokes the passed function with the key of every
    # nested bucket in the current bucket.  This does not include any
    # nested buckets within those nested buckets.
    #
    # WARNING: It is not safe to mutate data while iterating with this
    # method.  Doing so may cause the underlying cursor to be invalidated
    # and return unexpected keys and/or values.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrTxClosed if the transaction has already been closed
    #
    # NOTE: The keys returned by this function are only valid during a
    # transaction.  Attempting to access them after a transaction has ended
    # results in undefined behavior.  This constraint prevents additional
    # data copies and allows support for memory-mapped database
    # implementations.
    def for_each_bucket(self):  # TODO
        pass

    # Cursor returns a new cursor, allowing for iteration over the bucket's
    # key/value pairs and nested buckets in forward or backward order.
    #
    # You must seek to a position using the First, Last, or Seek functions
    # before calling the Next, Prev, Key, or Value functions.  Failure to
    # do so will result in the same return values as an exhausted cursor,
    # which is false for the Prev and Next functions and nil for Key and
    # Value functions.
    def cursor(self):
        pass

    # Writable returns whether or not the bucket is writable.
    def writable(self):
        pass

    # Put saves the specified key/value pair to the bucket.  Keys that do
    # not already exist are added and keys that already exist are
    # overwritten.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrKeyRequired if the key is empty
    #   - ErrIncompatibleValue if the key is the same as an existing bucket
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # NOTE: The slices passed to this function must NOT be modified by the
    # caller.  This constraint prevents the requirement for additional data
    # copies and allows support for memory-mapped database implementations.
    def put(self, key: bytes, value: bytes):
        pass

    # Get returns the value for the given key.  Returns nil if the key does
    # not exist in this bucket.  An empty slice is returned for keys that
    # exist but have no value assigned.
    #
    # NOTE: The value returned by this function is only valid during a
    # transaction.  Attempting to access it after a transaction has ended
    # results in undefined behavior.  Additionally, the value must NOT
    # be modified by the caller.  These constraints prevent additional data
    # copies and allows support for memory-mapped database implementations.
    def get(self, key: bytes) -> bytes:
        pass

    # Delete removes the specified key from the bucket.  Deleting a key
    # that does not exist does not return an error.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrKeyRequired if the key is empty
    #   - ErrIncompatibleValue if the key is the same as an existing bucket
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    def delete(self, key: bytes):
        pass


# Cursor represents a cursor over key/value pairs and nested buckets of a
# bucket.
#
# Note that open cursors are not tracked on bucket changes and any
# modifications to the bucket, with the exception of Cursor.Delete, invalidates
# the cursor.  After invalidation, the cursor must be repositioned, or the keys
# and values returned may be unpredictable.
class Cursor:
    # Bucket returns the bucket the cursor was created for.
    def bucket(self) -> Bucket:
        pass

    # Delete removes the current key/value pair the cursor is at without
    # invalidating the cursor.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrIncompatibleValue if attempted when the cursor points to a
    #     nested bucket
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    def delete(self):
        pass

    # First positions the cursor at the first key/value pair and returns
    # whether or not the pair exists.
    def first(self) -> bool:
        pass

    # Last positions the cursor at the last key/value pair and returns
    # whether or not the pair exists.
    def last(self) -> bool:
        pass

    # Next moves the cursor one key/value pair forward and returns whether
    # or not the pair exists.
    def next(self) -> bool:
        pass

    # Prev moves the cursor one key/value pair backward and returns whether
    # or not the pair exists.
    def prev(self) -> bool:
        pass

    # Seek positions the cursor at the first key/value pair that is greater
    # than or equal to the passed seek key.  Returns whether or not the
    # pair exists.
    def seek(self, seek: bytes) -> bool:
        pass

    # Key returns the current key the cursor is pointing to.
    def key(self) -> bytes:
        pass

    # Value returns the current value the cursor is pointing to.  This will
    # be nil for nested buckets.
    def value(self) -> bytes:
        pass


# BlockRegion specifies a particular region of a block identified by the
# specified hash, given an offset and length.    
class BlockRegion:
    def __init__(self, hash, offset, len):
        """

        :param *chainhash.Hash hash:
        :param uint32 offset:
        :param uint32 len:
        """
        self.hash = hash
        self.offset = offset
        self.len = len


# Tx represents a database transaction.  It can either by read-only or
# read-write.  The transaction provides a metadata bucket against which all
# read and writes occur.
#
# As would be expected with a transaction, no changes will be saved to the
# database until it has been committed.  The transaction will only provide a
# view of the database at the time it was created.  Transactions should not be
# long running operations.
class Tx:
    #  Metadata returns the top-most bucket for all metadata storage.
    def meta_data(self) -> Bucket:
        pass

    # StoreBlock stores the provided block into the database.  There are no
    # checks to ensure the block connects to a previous block, contains
    # double spends, or any additional functionality such as transaction
    # indexing.  It simply stores the block in the database.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockExists when the block hash already exists
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # Other errors are possible depending on the implementation.
    def store_block(self, block):
        pass

    # HasBlock returns whether or not a block with the given hash exists
    # in the database.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrTxClosed if the transaction has already been closed
    #
    # Other errors are possible depending on the implementation.
    def has_block(self, hash):
        pass

    # HasBlocks returns whether or not the blocks with the provided hashes
    # exist in the database.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrTxClosed if the transaction has already been closed
    #
    # Other errors are possible depending on the implementation.
    def has_blocks(self, hashes):
        pass

    # FetchBlockHeader returns the raw serialized bytes for the block
    # header identified by the given hash.  The raw bytes are in the format
    # returned by Serialize on a wire.BlockHeader.
    #
    # It is highly recommended to use this function (or FetchBlockHeaders)
    # to obtain block headers over the FetchBlockRegion(s) functions since
    # it provides the backend drivers the freedom to perform very specific
    # optimizations which can result in significant speed advantages when
    # working with headers.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockNotFound if the requested block hash does not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.
    def fetch_block_header(self, hash):
        pass

    # FetchBlockHeaders returns the raw serialized bytes for the block
    # headers identified by the given hashes.  The raw bytes are in the
    # format returned by Serialize on a wire.BlockHeader.
    #
    # It is highly recommended to use this function (or FetchBlockHeader)
    # to obtain block headers over the FetchBlockRegion(s) functions since
    # it provides the backend drivers the freedom to perform very specific
    # optimizations which can result in significant speed advantages when
    # working with headers.
    #
    # Furthermore, depending on the specific implementation, this function
    # can be more efficient for bulk loading multiple block headers than
    # loading them one-by-one with FetchBlockHeader.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockNotFound if any of the request block hashes do not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.
    def fetch_block_headers(self, hash):
        pass

    # FetchBlock returns the raw serialized bytes for the block identified
    # by the given hash.  The raw bytes are in the format returned by
    # Serialize on a wire.MsgBlock.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockNotFound if the requested block hash does not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.
    def fetch_block(self, hash):
        pass

    # FetchBlocks returns the raw serialized bytes for the blocks
    # identified by the given hashes.  The raw bytes are in the format
    # returned by Serialize on a wire.MsgBlock.
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockNotFound if the any of the requested block hashes do not
    #     exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.
    def fetch_blocks(self, hashes):
        pass

    # FetchBlockRegion returns the raw serialized bytes for the given
    # block region.
    #
    # For example, it is possible to directly extract Bitcoin transactions
    # and/or scripts from a block with this function.  Depending on the
    # backend implementation, this can provide significant savings by
    # avoiding the need to load entire blocks.
    #
    # The raw bytes are in the format returned by Serialize on a
    # wire.MsgBlock and the Offset field in the provided BlockRegion is
    # zero-based and relative to the start of the block (byte 0).
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockNotFound if the requested block hash does not exist
    #   - ErrBlockRegionInvalid if the region exceeds the bounds of the
    #     associated block
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.
    def fetch_block_region(self, region):
        pass

    # FetchBlockRegions returns the raw serialized bytes for the given
    # block regions.
    #
    # For example, it is possible to directly extract Bitcoin transactions
    # and/or scripts from various blocks with this function.  Depending on
    # the backend implementation, this can provide significant savings by
    # avoiding the need to load entire blocks.
    #
    # The raw bytes are in the format returned by Serialize on a
    # wire.MsgBlock and the Offset fields in the provided BlockRegions are
    # zero-based and relative to the start of the block (byte 0).
    #
    # The interface contract guarantees at least the following errors will
    # be returned (other implementation-specific errors are possible):
    #   - ErrBlockNotFound if any of the requested block hashed do not
    #     exist
    #   - ErrBlockRegionInvalid if one or more region exceed the bounds of
    #     the associated block
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.

    def fetch_block_regions(self, regions):
        pass

    # ******************************************************************
    # Methods related to both atomic metadata storage and block storage.
    # ******************************************************************

    # Commit commits all changes that have been made to the metadata or
    # block storage.  Depending on the backend implementation this could be
    # to a cache that is periodically synced to persistent storage or
    # directly to persistent storage.  In any case, all transactions which
    # are started after the commit finishes will include all changes made
    # by this transaction.  Calling this function on a managed transaction
    # will result in a panic.
    def commit(self):
        pass

    # Rollback undoes all changes that have been made to the metadata or
    # block storage.  Calling this function on a managed transaction will
    # result in a panic.
    def rollback(self):
        pass


# DB provides a generic interface that is used to store bitcoin blocks and
# related metadata.  This interface is intended to be agnostic to the actual
# mechanism used for backend data storage.  The RegisterDriver function can be
# used to add a new backend data storage method.
#
# This interface is divided into two distinct categories of functionality.
#
# The first category is atomic metadata storage with bucket support.  This is
# accomplished through the use of database transactions.
#
# The second category is generic block storage.  This functionality is
# intentionally separate because the mechanism used for block storage may or
# may not be the same mechanism used for metadata storage.  For example, it is
# often more efficient to store the block data as flat files while the metadata
# is kept in a database.  However, this interface aims to be generic enough to
# support blocks in the database too, if needed by a particular backend.
class DB:
    # Type returns the database driver type the current database instance
    # was created with.
    def type(self):
        pass

    # Begin starts a transaction which is either read-only or read-write
    # depending on the specified flag.  Multiple read-only transactions
    # can be started simultaneously while only a single read-write
    # transaction can be started at a time.  The call will block when
    # starting a read-write transaction when one is already open.
    #
    # NOTE: The transaction must be closed by calling Rollback or Commit on
    # it when it is no longer needed.  Failure to do so can result in
    # unclaimed memory and/or inablity to close the database due to locks
    # depending on the specific database implementation.
    def begin(self):
        pass

    # View invokes the passed function in the context of a managed
    # read-only transaction.  Any errors returned from the user-supplied
    # function are returned from this function.
    #
    # Calling Rollback or Commit on the transaction passed to the
    # user-supplied function will result in a panic.
    def view(self, fn):  # TODO
        pass

    # Update invokes the passed function in the context of a managed
    # read-write transaction.  Any errors returned from the user-supplied
    # function will cause the transaction to be rolled back and are
    # returned from this function.  Otherwise, the transaction is committed
    # when the user-supplied function returns a nil error.
    #
    # Calling Rollback or Commit on the transaction passed to the
    # user-supplied function will result in a panic.
    def update(self, fn):
        pass

    # Close cleanly shuts down the database and syncs all data.  It will
    # block until all database transactions have been finalized (rolled
    # back or committed).
    def close(self):
        pass
