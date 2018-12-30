import chainhash
import database
from database.error import *
import pyutil
import btcutil
import database.treap as treap
import logging
import copy
from .utils import *
from enum import IntEnum
from .block_io import *
from .reconcile import *
import plyvel
from .db_cache import *
from .ldb_treap_iter import *
from .leveldb_iterator import *

_logger = logging.Logger(__name__)

# ****************
# Some constant
# ****************
# error code.
errDbNotOpenStr = "database is not open"

# errTxClosedStr is the text to use for the database.ErrTxClosed error
# code.
errTxClosedStr = "database tx is closed"

# ****************
# Some global variables
# ****************

# metadataDbName is the name used for the metadata database.
metadataDbName = "metadata"

# bucketIndexPrefix is the prefix used for all entries in the bucket
# index.
bucketIndexPrefix = b"bidx"

# curBucketIDKeyName is the name of the key used to keep track of the
# current bucket ID counter.
curBucketIDKeyName = b"bidx-cbid"

# metadataBucketID is the ID of the top-level metadata bucket.
# It is the value 0 encoded as an unsigned big-endian uint32.
metadataBucketID = bytes(4)

# blockIdxBucketID is the ID of the internal block metadata bucket.
# It is the value 1 encoded as an unsigned big-endian uint32.
blockIdxBucketID = bytes([0x00, 0x00, 0x00, 0x01])

# blockIdxBucketName is the bucket used internally to track block
# metadata.
blockIdxBucketName = b"ffldb-blockidx"

# writeLocKeyName is the key used to store the current write file
# location.
writeLocKeyName = b"ffldb-writeloc"


# ****************
# Helper function
# ****************






def copy_slice(b):
    return copy.deepcopy(b)


# ****************
# Class defines
# ****************


# bulkFetchData is allows a block location to be specified along with the
# index it was requested from.  This in turn allows the bulk data loading
# functions to sort the data accesses based on the location to improve
# performance while keeping track of which result the data is for.
class BulkFetchData:
    def __init__(self, block_location, reply_index):
        self.block_location = block_location
        self.reply_index = reply_index


# bucketIndexKey returns the actual key to use for storing and retrieving a
# child bucket in the bucket index.  This is required because additional
# information is needed to distinguish nested buckets with the same name.
def bucket_index_key(parent_id: bytes(4), key: bytes) -> bytes:
    # The serialized bucket index key format is:
    #   <bucketindexprefix><parentbucketid><bucketname>
    return bucketIndexPrefix + parent_id + key


# bucketizedKey returns the actual key to use for storing and retrieving a key
# for the provided bucket ID.  This is required because bucketizing is handled
# through the use of a unique prefix per bucket.
def bucketized_key(bucket_id: bytes(4), key: bytes) -> bytes:
    # The serialized block index key format is:
    #   <bucketid><key>
    return bucket_id + key


# bucket is an internal type used to represent a collection of key/value pairs
# and implements the database.Bucket interface.
class Bucket(database.Bucket):
    def __init__(self, tx: 'Transaction', id: bytes(4)):
        self.tx = tx
        self.id = id

    # Bucket retrieves a nested bucket with the given key.  Returns nil if
    # the bucket does not exist.
    #
    # This function is part of the database.Bucket interface implementation.
    def bucket(self, key: bytes) -> database.Bucket or None:

        # Ensure transaction state is valid.
        try:
            self.tx.check_closed()
        except Exception as e:
            _logger.warning("A ignored exception happens" % e)
            return None  # if there is error, return None

        # Attempt to fetch the ID for the child bucket.  The bucket does not
        # exist if the bucket index entry does not exist.
        child_id = self.tx.fetch_key(bucket_index_key(self.id, key))
        if child_id is None:
            return None

        child_bucket = Bucket(tx=self.tx, id=child_id)
        return child_bucket

    # CreateBucket creates and returns a new nested bucket with the given key.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBucketExists if the bucket already exists
    #   - ErrBucketNameRequired if the key is empty
    #   - ErrIncompatibleValue if the key is otherwise invalid for the particular
    #     implementation
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Bucket interface implementation.
    def create_bucket(self, key: bytes) -> database.Bucket:
        # Ensure transaction state is valid.
        self.tx.check_closed()

        # Ensure the transaction is writable.
        if not self.tx.writable:
            msg = "create bucket requires a writable database transaction"
            raise DBError(ErrorCode.ErrTxNotWritable, msg)

        # Ensure a key was provided.
        if len(key) == 0:
            msg = "create bucket requires a key"
            raise DBError(ErrorCode.ErrBucketNameRequired, msg)

        # Ensure bucket does not already exist.
        bidx_key = bucket_index_key(self.id, key)
        if self.tx.has_key(bidx_key):
            msg = "bucket already exists"
            raise DBError(ErrorCode.ErrBucketExists, msg)

        # Find the appropriate next bucket ID to use for the new bucket.  In
        # the case of the special internal block index, keep the fixed ID.
        if self.id == metadataBucketID and key == blockIdxBucketName:
            child_id = blockIdxBucketID
        else:
            child_id = self.tx.next_bucket_id()

        # Add the new bucket to the bucket index.
        try:
            self.tx.put_key(bidx_key, child_id)
        except Exception as e:
            msg = "failed to create bucket with key %s" % key
            raise convert_err(msg, e)

        return Bucket(tx=self.tx, id=child_id)

    # CreateBucketIfNotExists creates and returns a new nested bucket with the
    # given key if it does not already exist.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBucketNameRequired if the key is empty
    #   - ErrIncompatibleValue if the key is otherwise invalid for the particular
    #     implementation
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Bucket interface implementation.
    def create_bucket_if_not_exists(self, key: bytes) -> database.Bucket:
        # Ensure transaction state is valid.
        self.tx.check_closed()

        # Ensure the transaction is writable.
        if not self.tx.writable:
            msg = "create bucket requires a writable database transaction"
            raise DBError(ErrorCode.ErrTxNotWritable, msg)

        # Return existing bucket if it already exists, otherwise create it.
        bucket = self.bucket(key)
        if bucket is not None:
            return bucket

        return self.create_bucket(key)

    # DeleteBucket removes a nested bucket with the given key.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBucketNotFound if the specified bucket does not exist
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Bucket interface implementation.
    def delete_bucket(self, key: bytes):
        # Ensure transaction state is valid.
        self.tx.check_closed()

        # Ensure the transaction is writable.
        if not self.tx.writable:
            msg = "delete bucket requires a writable database transaction"
            raise DBError(ErrorCode.ErrTxNotWritable, msg)

        # Attempt to fetch the ID for the child bucket.  The bucket does not
        # exist if the bucket index entry does not exist.  In the case of the
        # special internal block index, keep the fixed ID.
        bidx_key = bucket_index_key(self.id, key)
        child_id = self.tx.fetch_key(bidx_key)
        if child_id is None:
            msg = "bucket %s does not exist" % key
            raise DBError(ErrorCode.ErrBucketNotFound, msg)

        # Remove all nested buckets and their keys.
        child_ids = [child_id]
        while len(child_ids) > 0:
            child_id = child_ids[-1]
            child_ids = child_ids[:-1]

            # Delete all keys in the nested bucket.
            key_cursor = new_cursor(self, child_id, CursorType.ctKeys)
            ok = key_cursor.first()
            while ok:
                self.tx.delete_key(key_cursor.raw_key(), notify_iterators=False)
                ok = key_cursor.next()

            cursor_finalizer(key_cursor)

            # Iterate through all nested buckets.
            bucket_cursor = new_cursor(self, child_id, CursorType.ctBuckets)
            ok = bucket_cursor.first()
            while ok:
                # Push the id of the nested bucket onto the stack for
                # the next iteration.
                child_id = bucket_cursor.raw_value()
                child_ids.append(child_id)

                # Remove the nested bucket from the bucket index.
                self.tx.delete_key(bucket_cursor.raw_key(), notify_iterators=False)

                ok = bucket_cursor.next()
            cursor_finalizer(bucket_cursor)

        # Remove the nested bucket from the bucket index.  Any buckets nested
        # under it were already removed above.
        self.tx.delete_key(bidx_key, notify_iterators=True)
        return

    # Cursor returns a new cursor, allowing for iteration over the bucket's
    # key/value pairs and nested buckets in forward or backward order.
    #
    # You must seek to a position using the First, Last, or Seek functions before
    # calling the Next, Prev, Key, or Value functions.  Failure to do so will
    # result in the same return values as an exhausted cursor, which is false for
    # the Prev and Next functions and nil for Key and Value functions.
    #
    # This function is part of the database.Bucket interface implementation.
    def cursor(self) -> database.Cursor:

        # Ensure transaction state is valid.
        try:
            self.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return Cursor(bucket=self)

        # Create the cursor and setup a runtime finalizer to ensure the
        # iterators are released when the cursor is garbage collected.
        c = new_cursor(self, self.id, CursorType.ctFull)

        # TOADD TODO add a destructive method to cursor class?
        return c

    # ForEach invokes the passed function with every key/value pair in the bucket.
    # This does not include nested buckets or the key/value pairs within those
    # nested buckets.
    #
    # WARNING: It is not safe to mutate data while iterating with this method.
    # Doing so may cause the underlying cursor to be invalidated and return
    # unexpected keys and/or values.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrTxClosed if the transaction has already been closed
    #
    # NOTE: The values returned by this function are only valid during a
    # transaction.  Attempting to access them after a transaction has ended will
    # likely result in an access violation.
    #
    # This function is part of the database.Bucket interface implementation.
    def for_each2(self):
        """This use yield to make a generator"""
        self.tx.check_closed()

        c = new_cursor(self, self.id, CursorType.ctKeys)

        ok = c.first()
        try:
            while ok:
                yield c.key(), c.value()
                ok = c.next()

        finally:
            cursor_finalizer(c)  # TOCONSIDER better way
        return

    # ForEachBucket invokes the passed function with the key of every nested bucket
    # in the current bucket.  This does not include any nested buckets within those
    # nested buckets.
    #
    # WARNING: It is not safe to mutate data while iterating with this method.
    # Doing so may cause the underlying cursor to be invalidated and return
    # unexpected keys.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrTxClosed if the transaction has already been closed
    #
    # NOTE: The values returned by this function are only valid during a
    # transaction.  Attempting to access them after a transaction has ended will
    # likely result in an access violation.
    #
    # This function is part of the database.Bucket interface implementation.
    def for_each_bucket2(self):
        """This use yield to make a generator"""
        self.tx.check_closed()

        c = new_cursor(self, self.id, CursorType.ctKeys)

        ok = c.first()
        try:
            while ok:
                yield c.key()
                ok = c.next()

        finally:
            cursor_finalizer(c)  # TOCONSIDER better way
        return

    # Writable returns whether or not the bucket is writable.
    #
    # This function is part of the database.Bucket interface implementation.
    def writable(self):
        return self.tx.writable

    # Put saves the specified key/value pair to the bucket.  Keys that do not
    # already exist are added and keys that already exist are overwritten.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrKeyRequired if the key is empty
    #   - ErrIncompatibleValue if the key is the same as an existing bucket
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Bucket interface implementation.
    def put(self, key: bytes, value: bytes):
        self.tx.check_closed()

        if not self.tx.writable:
            msg = "setting a key requires a writable database transaction"
            raise DBError(ErrorCode.ErrTxNotWritable, msg)

        if len(key) == 0:
            msg = "put requires a key"
            raise DBError(ErrorCode.ErrKeyRequired, msg)

        return self.tx.put_key(bucketized_key(self.id, key), value)

    # Get returns the value for the given key.  Returns nil if the key does not
    # exist in this bucket.  An empty slice is returned for keys that exist but
    # have no value assigned.
    #
    # NOTE: The value returned by this function is only valid during a transaction.
    # Attempting to access it after a transaction has ended results in undefined
    # behavior.  Additionally, the value must NOT be modified by the caller.
    #
    # This function is part of the database.Bucket interface implementation.
    def get(self, key: bytes) -> bytes or None:
        try:
            self.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return None

        if len(key) == 0:
            return None

        return self.tx.fetch_key(bucketized_key(self.id, key))

    # Delete removes the specified key from the bucket.  Deleting a key that does
    # not exist does not return an error.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrKeyRequired if the key is empty
    #   - ErrIncompatibleValue if the key is the same as an existing bucket
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Bucket interface implementation.
    def delete(self, key: bytes):
        self.tx.check_closed()

        if not self.tx.writable:
            msg = "setting a key requires a writable database transaction"
            raise DBError(ErrorCode.ErrTxNotWritable, msg)

        if len(key) == 0:
            return None

        return self.tx.delete_key(bucketized_key(self.id, key), notify_iterators=True)


# pendingBlock houses a block that will be written to disk when the database
# transaction is committed.
class PendingBlock:
    def __init__(self, block_hash, block_bytes):
        """

        :param chainhash.Hash block_hash:
        :param bytes block_bytes:
        """
        self.block_hash = block_hash
        self.block_bytes = block_bytes


# transaction represents a database transaction.  It can either be read-only or
# read-write and implements the database.Tx interface.  The transaction
# provides a root bucket against which all read and writes occur.
class Transaction(database.Tx):
    def __init__(self, managed=None, closed=None, writable=None, db=None, snapshot=None, meta_bucket=None,
                 block_idx_bucket=None, pending_blocks=None, pending_block_data=None,
                 pending_keys=None, pending_remove=None,
                 active_iter_lock=None, active_iters=None, ):
        """

        :param bool managed:
        :param bool closed:
        :param bool writable:
        :param DB db:
        :param *dbCacheSnapshot snapshot:
        :param *bucket meta_bucket:
        :param *bucket block_idx_bucket:
        :param map[chainhash.Hash]int pending_blocks:
        :param [PendingBlock] pending_block_data:
        :param *treap.Mutable pending_keys:
        :param *treap.Mutable pending_remove:
        :param RWLock active_iter_lock:
        :param []*treap.Iterator active_iters:
        """
        # Is the transaction managed?
        self.managed = managed or False

        # Is the transaction closed?
        self.closed = closed or False

        # Is the transaction writable?
        self.writable = writable or False

        # DB instance the tx was created from.
        self.db = db

        # Underlying snapshot for txns.
        self.snapshot = snapshot

        # The root metadata bucket.
        self.meta_bucket = meta_bucket

        # The block index bucket.
        self.block_idx_bucket = block_idx_bucket

        # Blocks that need to be stored on commit.  The pendingBlocks map is
        # kept to allow quick lookups of pending data by block hash.
        self.pending_blocks = pending_blocks or {}
        self.pending_block_data = pending_block_data or []

        # Keys that need to be stored or deleted on commit.
        self.pending_keys = pending_keys
        self.pending_remove = pending_remove

        # Active iterators that need to be notified when the pending keys have
        # been updated so the cursors can properly handle updates to the
        # transaction state.
        self.active_iter_lock = active_iter_lock or pyutil.RWLock()
        self.active_iters = active_iters or []

    # removeActiveIter removes the passed iterator from the list of active
    # iterators against the pending keys treap.
    def remove_active_iter(self, the_iter: treap.Iterator):
        self.active_iter_lock.writer_acquire()
        self.active_iters.remove(the_iter)
        self.active_iter_lock.writer_release()

    # addActiveIter adds the passed iterator to the list of active iterators for
    # the pending keys treap.
    def add_active_iter(self, the_iter: treap.Iterator):
        self.active_iter_lock.writer_acquire()
        self.active_iters.append(the_iter)
        self.active_iter_lock.writer_release()

    # notifyActiveIters notifies all of the active iterators for the pending keys
    # treap that it has been updated.
    def notify_active_iters(self):
        self.active_iter_lock.reader_acquire()
        for the_iter in self.active_iters:
            the_iter.force_reseek()
        self.active_iter_lock.reader_release()

    # checkClosed returns an error if the the database or transaction is closed.
    def check_closed(self):
        # The transaction is no longer valid if it has been closed.
        if self.closed:
            raise DBError(ErrorCode.ErrTxClosed, errTxClosedStr)
        return

    # hasKey returns whether or not the provided key exists in the database while
    # taking into account the current transaction state.
    def has_key(self, key: bytes) -> bool:
        # When the transaction is writable, check the pending transaction
        # state first.
        if self.writable:
            if self.pending_remove.has(key):
                return False

            if self.pending_keys.has(key):
                return True

        # Consult the database cache and underlying database.
        return self.snapshot.has(key)

    # putKey adds the provided key to the list of keys to be updated in the
    # database when the transaction is committed.
    #
    # NOTE: This function must only be called on a writable transaction.  Since it
    # is an internal helper function, it does not check.
    def put_key(self, key: bytes, value: bytes):
        # Prevent the key from being deleted if it was previously scheduled
        # to be deleted on transaction commit.
        self.pending_remove.delete(key)

        # Add the key/value pair to the list to be written on transaction
        # commit.
        self.pending_keys.put(key, value)
        self.notify_active_iters()
        return

        # fetchKey attempts to fetch the provided key from the database cache (and

    # hence underlying database) while taking into account the current transaction
    # state.  Returns nil if the key does not exist.
    def fetch_key(self, key: bytes) -> bytes:
        # When the transaction is writable, check the pending transaction
        # state first.
        if self.writable:
            if self.pending_remove.has(key):
                return None

            value = self.pending_keys.get(key)
            if value is not None:
                return value

        return self.snapshot.get(key)

    # deleteKey adds the provided key to the list of keys to be deleted from the
    # database when the transaction is committed.  The notify iterators flag is
    # useful to delay notifying iterators about the changes during bulk deletes.
    #
    # NOTE: This function must only be called on a writable transaction.  Since it
    # is an internal helper function, it does not check.
    def delete_key(self, key: bytes, notify_iterators: bool):
        # Remove the key from the list of pendings keys to be written on
        # transaction commit if needed.
        self.pending_keys.delete(key)

        # Add the key to the list to be deleted on transaction    commit.
        self.pending_remove.put(key, None)

        # Notify the active iterators about the change if the flag is set.
        if notify_iterators:
            self.notify_active_iters()

        return

    # nextBucketID returns the next bucket ID to use for creating a new bucket.
    #
    # NOTE: This function must only be called on a writable transaction.  Since it
    # is an internal helper function, it does not check.
    def next_bucket_id(self):
        # Load the currently highest used bucket ID.
        cur_bucket_id_bytes = self.fetch_key(curBucketIDKeyName)
        cur_bucket_id_int = pyutil.bytes_to_uint32(cur_bucket_id_bytes)

        # Increment and update the current bucket ID and return it.
        next_bucket_id_bytes = pyutil.uint32_to_bytes(cur_bucket_id_int + 1)

        self.put_key(curBucketIDKeyName, next_bucket_id_bytes)

        return next_bucket_id_bytes

    # Metadata returns the top-most bucket for all metadata storage.
    #
    # This function is part of the database.Tx interface implementation.
    def metadata(self):
        return self.meta_bucket

    # hasBlock returns whether or not a block with the given hash exists.
    def _has_block(self, hash: chainhash.Hash):

        # Return true if the block is pending to be written on commit since
        # it exists from the viewpoint of this transaction.
        if hash in self.pending_blocks:
            return True

        return self.has_key(bucketized_key(blockIdxBucketID, hash.to_bytes()))

    # StoreBlock stores the provided block into the database.  There are no checks
    # to ensure the block connects to a previous block, contains double spends, or
    # any additional functionality such as transaction indexing.  It simply stores
    # the block in the database.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockExists when the block hash already exists
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Tx interface implementation.
    def store_block(self, block: btcutil.Block):
        # Ensure transaction state is valid.
        self.check_closed()

        # Ensure the transaction is writable.
        if not self.writable:
            msg = "store block requires a writable database transaction"
            raise DBError(ErrorCode.ErrTxNotWritable, msg)

        block_hash = block.hash()
        if self._has_block(block_hash):
            msg = "block %s already exists" % block_hash
            raise DBError(ErrorCode.ErrBlockExists, msg)

        try:
            block_bytes = block.bytes()
        except Exception as e:
            msg = "failed to get serialized bytes for block %s" % block_hash
            raise DBError(ErrorCode.ErrDriverSpecific, msg, err=e)

        # Add the block to be stored to the list of pending blocks to store
        # when the transaction is committed.  Also, add it to pending blocks
        # map so it is easy to determine the block is pending based on the
        # block hash.
        self.pending_blocks[block_hash] = len(self.pending_block_data)
        self.pending_block_data.append(PendingBlock(
            block_hash=block_hash,
            block_bytes=block_bytes
        ))
        _logger.info("Added block %s to pending blocks" % block_hash)
        return

    # HasBlock returns whether or not a block with the given hash exists in the
    # database.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Tx interface implementation.
    def has_block(self, hash: chainhash.Hash) -> bool:

        # Ensure transaction state is valid.
        self.check_closed()

        return self._has_block(hash)

    # HasBlocks returns whether or not the blocks with the provided hashes
    # exist in the database.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Tx interface implementation.
    def has_blocks(self, hashes: [chainhash.Hash]) -> [bool]:

        # Ensure transaction state is valid.
        self.check_closed()

        results = []
        for hash in hashes:
            try:
                has = self.has_block(hash)
            except Exception as e:
                _logger.debug(e)
                has = False
            results.append(has)
        return results

    # fetchBlockRow fetches the metadata stored in the block index for the provided
    # hash.  It will return ErrBlockNotFound if there is no entry.
    def fetch_block_row(self, hash: chainhash.Hash):
        block_row = self.block_idx_bucket.get(hash.to_bytes())
        if block_row is None:
            msg = "block %s does not exist" % hash
            raise DBError(ErrorCode.ErrBlockNotFound, msg)
        return block_row

    # FetchBlockHeader returns the raw serialized bytes for the block header
    # identified by the given hash.  The raw bytes are in the format returned by
    # Serialize on a wire.BlockHeader.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockNotFound if the requested block hash does not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a
    # database transaction.  Attempting to access it after a transaction
    # has ended results in undefined behavior.  This constraint prevents
    # additional data copies and allows support for memory-mapped database
    # implementations.
    #
    # This function is part of the database.Tx interface implementation.
    def fetch_block_header(self, hash: chainhash.Hash):
        return self.fetch_block_region(database.BlockRegion(
            hash=hash,
            offset=0,
            len=wire.MaxBlockHeaderPayload
        ))

    # FetchBlockHeaders returns the raw serialized bytes for the block headers
    # identified by the given hashes.  The raw bytes are in the format returned by
    # Serialize on a wire.BlockHeader.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockNotFound if the any of the requested block hashes do not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # NOTE: The data returned by this function is only valid during a database
    # transaction.  Attempting to access it after a transaction has ended results
    # in undefined behavior.  This constraint prevents additional data copies and
    # allows support for memory-mapped database implementations.
    #
    # This function is part of the database.Tx interface implementation.
    def fetch_block_headers(self, hashes: [chainhash.Hash]):
        regions = []
        for hash in hashes:
            regions.append(database.BlockRegion(
                hash=hash,
                offset=0,
                len=wire.MaxBlockHeaderPayload
            ))
        return self.fetch_block_regions(regions)

    # FetchBlock returns the raw serialized bytes for the block identified by the
    # given hash.  The raw bytes are in the format returned by Serialize on a
    # wire.MsgBlock.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockNotFound if the requested block hash does not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # In addition, returns ErrDriverSpecific if any failures occur when reading the
    # block files.
    #
    # NOTE: The data returned by this function is only valid during a database
    # transaction.  Attempting to access it after a transaction has ended results
    # in undefined behavior.  This constraint prevents additional data copies and
    # allows support for memory-mapped database implementations.
    #
    # This function is part of the database.Tx interface implementation.
    def fetch_block(self, hash: chainhash.Hash):
        # Ensure transaction state is valid.
        self.check_closed()

        # When the block is pending to be written on commit return the bytes
        # from there.
        if hash in self.pending_blocks:
            idx = self.pending_blocks[hash]
            return self.pending_block_data[idx].bytes

        block_row = self.fetch_block_row(hash)
        location = BlockLocation()
        location.deserialize(block_row)

        # Read the block from the appropriate location.  The function also
        # performs a checksum over the data to detect data corruption.
        block_bytes = self.db.store.read_block(hash, location)
        return block_bytes

    # FetchBlocks returns the raw serialized bytes for the blocks identified by the
    # given hashes.  The raw bytes are in the format returned by Serialize on a
    # wire.MsgBlock.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockNotFound if any of the requested block hashed do not exist
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # In addition, returns ErrDriverSpecific if any failures occur when reading the
    # block files.
    #
    # NOTE: The data returned by this function is only valid during a database
    # transaction.  Attempting to access it after a transaction has ended results
    # in undefined behavior.  This constraint prevents additional data copies and
    # allows support for memory-mapped database implementations.
    #
    # This function is part of the database.Tx interface implementation.
    def fetch_blocks(self, hashes):
        # Ensure transaction state is valid.
        self.check_closed()

        # NOTE: This could check for the existence of all blocks before loading
        # any of them which would be faster in the failure case, however
        # callers will not typically be calling this function with invalid
        # values, so optimize for the common case.
        blocks = []
        for hash in hashes:
            blocks.append(self.fetch_block(hash))
        return blocks

    # fetchPendingRegion attempts to fetch the provided region from any block which
    # are pending to be written on commit.  It will return nil for the byte slice
    # when the region references a block which is not pending.  When the region
    # does reference a pending block, it is bounds checked and returns
    # ErrBlockRegionInvalid if invalid.
    def fetch_pending_region(self, region: database.BlockRegion):
        # Nothing to do if the block is not pending to be written on commit.
        if region.hash not in self.pending_blocks:
            return None

        # Ensure the region is within the bounds of the block.
        idx = self.pending_blocks[region.hash]
        block_bytes = self.pending_block_data[idx].bytes
        block_len = len(block_bytes)
        end_offset = region.offset + region.len
        if end_offset < region.offset or end_offset > block_len:
            msg = "block %s region offset %d, length %d exceeds block length of %d" % (
                region.hash, region.offset, region.len, block_len)
            raise DBError(ErrorCode.ErrBlockRegionInvalid, msg)

        # Return the bytes from the pending block.
        return block_bytes[region.offset:end_offset]

    # FetchBlockRegion returns the raw serialized bytes for the given block region.
    #
    # For example, it is possible to directly extract Bitcoin transactions and/or
    # scripts from a block with this function.  Depending on the backend
    # implementation, this can provide significant savings by avoiding the need to
    # load entire blocks.
    #
    # The raw bytes are in the format returned by Serialize on a wire.MsgBlock and
    # the Offset field in the provided BlockRegion is zero-based and relative to
    # the start of the block (byte 0).
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockNotFound if the requested block hash does not exist
    #   - ErrBlockRegionInvalid if the region exceeds the bounds of the associated
    #     block
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # In addition, returns ErrDriverSpecific if any failures occur when reading the
    # block files.
    #
    # NOTE: The data returned by this function is only valid during a database
    # transaction.  Attempting to access it after a transaction has ended results
    # in undefined behavior.  This constraint prevents additional data copies and
    # allows support for memory-mapped database implementations.
    #
    # This function is part of the database.Tx interface implementation.
    def fetch_block_region(self, region: database.BlockRegion):
        # Ensure transaction state is valid.
        self.check_closed()

        # When the block is pending to be written on commit return the bytes
        # from there.
        if self.pending_blocks:
            region_bytes = self.fetch_pending_region(region)
            if region_bytes:
                return region_bytes

        # Lookup the location of the block in the files from the block index.
        block_row = self.fetch_block_row(region.hash)
        location = BlockLocation()
        location.deserialize(block_row)

        # Ensure the region is within the bounds of the block.
        end_offset = region.offset + region.len
        if end_offset < region.offset or end_offset > location.block_len:
            msg = "block %s region offset %d, length %d exceeds block length of %d" % (
                region.hash, region.offset, region.len, location.block_len)
            raise DBError(ErrorCode.ErrBlockRegionInvalid, msg)

        # Read the region from the appropriate disk block file.
        region_bytes = self.db.store.read_block_region(location, region.offset, region.len)
        return region_bytes

    # FetchBlockRegions returns the raw serialized bytes for the given block
    # regions.
    #
    # For example, it is possible to directly extract Bitcoin transactions and/or
    # scripts from various blocks with this function.  Depending on the backend
    # implementation, this can provide significant savings by avoiding the need to
    # load entire blocks.
    #
    # The raw bytes are in the format returned by Serialize on a wire.MsgBlock and
    # the Offset fields in the provided BlockRegions are zero-based and relative to
    # the start of the block (byte 0).
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrBlockNotFound if any of the request block hashes do not exist
    #   - ErrBlockRegionInvalid if one or more region exceed the bounds of the
    #     associated block
    #   - ErrTxClosed if the transaction has already been closed
    #   - ErrCorruption if the database has somehow become corrupted
    #
    # In addition, returns ErrDriverSpecific if any failures occur when reading the
    # block files.
    #
    # NOTE: The data returned by this function is only valid during a database
    # transaction.  Attempting to access it after a transaction has ended results
    # in undefined behavior.  This constraint prevents additional data copies and
    # allows support for memory-mapped database implementations.
    #
    # This function is part of the database.Tx interface implementation.
    def fetch_block_regions(self, regions):
        # Ensure transaction state is valid.
        self.check_closed()

        # NOTE: This could check for the existence of all blocks before
        # deserializing the locations and building up the fetch list which
        # would be faster in the failure case, however callers will not
        # typically be calling this function with invalid values, so optimize
        # for the common case.

        # NOTE: A potential optimization here would be to combine adjacent
        # regions to reduce the number of reads.

        # In order to improve efficiency of loading the bulk data, first grab
        # the block location for all of the requested block hashes and sort
        # the reads by filenum:offset so that all reads are grouped by file
        # and linear within each file.  This can result in quite a significant
        # performance increase depending on how spread out the requested hashes
        # are by reducing the number of file open/closes and random accesses
        # needed.  The fetchList is intentionally allocated with a cap because
        # some of the regions might be fetched from the pending blocks and
        # hence there is no need to fetch those from disk.
        block_regions = []

        for region in regions:
            # When the block is pending to be written on commit return the bytes
            # from there.
            if self.pending_blocks:
                region_bytes = self.fetch_pending_region(region)
                if region_bytes:
                    block_regions.append(region_bytes)
                    continue

            # Lookup the location of the block in the files from the block index.
            block_row = self.fetch_block_row(region.hash)
            location = BlockLocation()
            location.deserialize(block_row)

            # Ensure the region is within the bounds of the block.
            end_offset = region.offset + region.len
            if end_offset < region.offset or end_offset > location.block_len:
                msg = "block %s region offset %d, length %d exceeds block length of %d" % (
                    region.hash, region.offset, region.len, location.block_len)
                raise DBError(ErrorCode.ErrBlockRegionInvalid, msg)

            # fetch_list.append(bulk_)
            # Read the region from the appropriate disk block file.
            region_bytes = self.db.store.read_block_region(location, region.offset, region.len)
            block_regions.append(region_bytes)

        return block_regions

    # close marks the transaction closed then releases any pending data, the
    # underlying snapshot, the transaction read lock, and the write lock when the
    # transaction is writable.
    def close(self):
        self.closed = True

        # Clear pending blocks that would have been written on commit.
        self.pending_blocks = None
        self.pending_block_data = None

        # Clear pending keys that would have been written or deleted on commit.
        self.pending_keys = None
        self.pending_remove = None

        # Release the snapshot.
        if self.snapshot:
            self.snapshot.release()
            self.snapshot = None

        self.db.close_lock.reader_release()

        # Release the writer lock for writable transactions to unblock any
        # other write transaction which are possibly waiting.
        if self.writable:
            self.db.write_lock.release()

        return

    # writePendingAndCommit writes pending block data to the flat block files,
    # updates the metadata with their locations as well as the new current write
    # location, and commits the metadata to the memory database cache.  It also
    # properly handles rollback in the case of failures.
    #
    # This function MUST only be called when there is pending data to be written.
    def write_pending_and_commit(self):
        # Save the current block store write position for potential rollback.
        # These variables are only updated here in this function and there can
        # only be one write transaction active at a time, so it's safe to store
        # them for potential rollback.
        wc = self.db.store.write_cursor
        wc.r_lock()
        old_blk_file_num = wc.cur_file_num
        old_blk_offset = wc.cur_offset
        wc.r_unlock()

        def rollback():
            # Rollback any modifications made to the block files if needed.
            self.db.store.handle_rollback(old_blk_file_num, old_blk_offset)

        # Loop through all of the pending blocks to store and write them.
        for block_data in self.pending_block_data:
            _logger.info("Storing block %s" % block_data.block_hash)
            try:
                location = self.db.store.write_block(block_data.block_bytes)
            except Exception as e:
                rollback()
                raise e

            # Add a record in the block index for the block.  The record
            # includes the location information needed to locate the block
            # on the filesystem as well as the block header since they are
            # so commonly needed.
            try:
                block_row = location.serialize()
                self.block_idx_bucket.put(block_data.block_hash.to_bytes(), block_row)
            except Exception as e:
                rollback()
                raise e

        # Update the metadata for the current write file and offset.
        write_row = serialize_write_row(wc.cur_file_num, wc.cur_offset)
        try:
            self.meta_bucket.put(writeLocKeyName, write_row)
        except Exception as e:
            rollback()
            return convert_err("failed to store write cursor", e)

        # Atomically update the database cache.  The cache automatically
        # handles flushing to the underlying persistent storage database.
        return self.db.cache.commit_tx(self)

    # Commit commits all changes that have been made to the root metadata bucket
    # and all of its sub-buckets to the database cache which is periodically synced
    # to persistent storage.  In addition, it commits all new blocks directly to
    # persistent storage bypassing the db cache.  Blocks can be rather large, so
    # this help increase the amount of cache available for the metadata updates and
    # is safe since blocks are immutable.
    #
    # This function is part of the database.Tx interface implementation.
    def commit(self):
        # Prevent commits on managed transactions.
        if self.managed:
            self.close()
            msg = "managed transaction rollback not allowed"
            raise Exception(msg)  # TOCHECK the way of panic

        # Ensure transaction state is valid.
        self.check_closed()

        try:
            if not self.writable:
                msg = "Commit requires a writable database transaction"
                raise DBError(ErrorCode.ErrTxNotWritable, msg)

            return self.write_pending_and_commit()
        finally:
            # Regardless of whether the commit succeeds, the transaction is closed
            # on return.
            self.close()

    # Rollback undoes all changes that have been made to the root bucket and all of
    # its sub-buckets.
    #
    # This function is part of the database.Tx interface implementation.
    def rollback(self):
        # Prevent rollbacks on managed transactions.
        if self.managed:
            self.close()
            msg = "managed transaction rollback not allowed"
            raise Exception(msg)  # TOCHECK the way of panic

        # Ensure transaction state is valid.
        self.check_closed()

        self.close()
        return


# cursor is an internal type used to represent a cursor over key/value pairs
# and nested buckets of a bucket and implements the database.Cursor interface.
class Cursor(database.Cursor):
    def __init__(self, bucket, db_iter=None, pending_iter=None, current_iter=None):
        """

        :param bucket bucket:
        :param iterator.Iterator db_iter:
        :param iterator.Iterator pending_iter:
        :param iterator.Iterator current_iter:
        """
        self.bucket = bucket
        self.db_iter = db_iter
        self.pending_iter = pending_iter
        self.current_iter = current_iter

    # Bucket returns the bucket the cursor was created for.
    #
    # This function is part of the database.Cursor interface implementation.
    def get_bucket(self):
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return None  # return None if exception

        return self.bucket

    # Delete removes the current key/value pair the cursor is at without
    # invalidating the cursor.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrIncompatibleValue if attempted when the cursor points to a nested
    #     bucket
    #   - ErrTxNotWritable if attempted against a read-only transaction
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Cursor interface implementation.
    def delete(self):
        # Ensure transaction state is valid.
        self.bucket.tx.check_closed()

        # Error if the cursor is exhausted.
        if self.current_iter is None:
            msg = "cursor is exhausted"
            raise DBError(ErrorCode.ErrIncompatibleValue, msg)

        # Do not allow buckets to be deleted via the cursor.
        key = self.current_iter.key()
        if pyutil.bytes_has_prefix(key, bucketIndexPrefix):
            msg = "buckets may not be deleted from a cursor"
            raise DBError(ErrorCode.ErrIncompatibleValue, msg)

        # TOCONSIDER need copy of key?
        self.bucket.tx.delete_key(copy_slice(key), notify_iterators=True)
        return

    # skipPendingUpdates skips any keys at the current database iterator position
    # that are being updated by the transaction.  The forwards flag indicates the
    # direction the cursor is moving.
    def skip_pending_updates(self, forwards: bool):
        while self.db_iter.valid():

            key = self.db_iter.key()

            if self.bucket.tx.pending_remove.has(key):
                skip = True
            elif self.bucket.tx.pending_keys.has(key):
                skip = True
            else:
                skip = False

            if not skip:
                break

            if forwards:
                self.db_iter.next()
            else:
                self.db_iter.prev()

        return

    # chooseIterator first skips any entries in the database iterator that are
    # being updated by the transaction and sets the current iterator to the
    # appropriate iterator depending on their validity and the order they compare
    # in while taking into account the direction flag.  When the cursor is being
    # moved forwards and both iterators are valid, the iterator with the smaller
    # key is chosen and vice versa when the cursor is being moved backwards.
    def choose_iterator(self, forwards: bool) -> bool:
        # Skip any keys at the current database iterator position that are
        # being updated by the transaction.
        self.skip_pending_updates(forwards)

        # When both iterators are exhausted, the cursor is exhausted too.
        if not self.db_iter.valid() and not self.pending_iter.valid():
            self.current_iter = None
            return False

        # Choose the database iterator when the pending keys iterator is
        # exhausted.
        if not self.pending_iter.valid():
            self.current_iter = self.db_iter
            return True

        # Choose the pending keys iterator when the database iterator is
        # exhausted.
        if not self.db_iter.valid():
            self.current_iter = self.pending_iter
            return True

        # Both iterators are valid, so choose the iterator with either the
        # smaller or larger key depending on the forwards flag.
        compare = byte_compare(self.db_iter.key(), self.pending_iter.key())
        if forwards and compare > 0 or (not forwards and compare < 0):
            self.current_iter = self.pending_iter
        else:
            self.current_iter = self.db_iter

        return True

    # First positions the cursor at the first key/value pair and returns whether or
    # not the pair exists.
    #
    # This function is part of the database.Cursor interface implementation.
    def first(self) -> bool:
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return False

        # Seek to the first key in both the database and pending iterators and
        # choose the iterator that is both valid and has the smaller key.
        x = self.db_iter.first()
        y = self.pending_iter.first()
        return self.choose_iterator(forwards=True)

    # Last positions the cursor at the last key/value pair and returns whether or
    # not the pair exists.
    #
    # This function is part of the database.Cursor interface implementation.
    def last(self) -> bool:
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return False

        # Seek to the last key in both the database and pending iterators and
        # choose the iterator that is both valid and has the larger key.

        self.db_iter.last()
        self.pending_iter.last()
        return self.choose_iterator(forwards=False)

    # Next moves the cursor one key/value pair forward and returns whether or not
    # the pair exists.
    #
    # This function is part of the database.Cursor interface implementation.
    def next(self) -> bool:
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return False

        # Nothing to return if cursor is exhausted.
        if self.current_iter is None:
            return False

        # Move the current iterator to the next entry and choose the iterator
        # that is both valid and has the smaller key.
        self.current_iter.next()
        return self.choose_iterator(forwards=True)

    # Prev moves the cursor one key/value pair backward and returns whether or not
    # the pair exists.
    #
    # This function is part of the database.Cursor interface implementation.
    def prev(self) -> bool:
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return False

        # Nothing to return if cursor is exhausted.
        if self.current_iter is None:
            return False

        # Move the current iterator to the previous entry and choose the
        # iterator that is both valid and has the larger key.
        x = self.current_iter.prev()
        return self.choose_iterator(forwards=False)

    # Seek positions the cursor at the first key/value pair that is greater than or
    # equal to the passed seek key.  Returns false if no suitable key was found.
    #
    # This function is part of the database.Cursor interface implementation.
    def seek(self, seek: bytes) -> bool:
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return False

        # Seek to the provided key in both the database and pending iterators
        # then choose the iterator that is both valid and has the larger key.
        seek_key = bucketized_key(self.bucket.id, seek)
        self.db_iter.seek(seek_key)
        self.pending_iter.seek(seek_key)
        return self.choose_iterator(forwards=True)

    # rawKey returns the current key the cursor is pointing to without stripping
    # the current bucket prefix or bucket index prefix.
    def raw_key(self) -> bytes or None:
        # Nothing to return if cursor is exhausted.
        if self.current_iter is None:
            return None

        # TOCONSIDER need deepcopy?
        return copy_slice(self.current_iter.key())

    # Key returns the current key the cursor is pointing to.
    #
    # This function is part of the database.Cursor interface implementation.
    def key(self) -> bytes or None:
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return None

        # Nothing to return if cursor is exhausted.
        if self.current_iter is None:
            return None

        # Slice out the actual key name and make a copy since it is no longer
        # valid after iterating to the next item.
        #
        # The key is after the bucket index prefix and parent ID when the
        # cursor is pointing to a nested bucket.
        key = self.current_iter.key()
        # if key is None:  # TODO
        #     return None

        if pyutil.bytes_has_prefix(key, bucketIndexPrefix):
            key = key[len(bucketIndexPrefix) + 4:]
            return copy_slice(key)

        # The key is after the bucket ID when the cursor is pointing to a
        # normal entry.
        key = key[len(self.bucket.id):]
        return copy_slice(key)

    # rawValue returns the current value the cursor is pointing to without
    # stripping without filtering bucket index values.
    def raw_value(self) -> bytes or None:
        # Nothing to return if cursor is exhausted.
        if self.current_iter is None:
            return None

        # TOCONSIDER need deepcopy?
        return copy_slice(self.current_iter.value())

    def value(self):
        # Ensure transaction state is valid.
        try:
            self.bucket.tx.check_closed()
        except Exception as e:
            _logger.debug(e)
            return None

        # Nothing to return if cursor is exhausted.
        if self.current_iter is None:
            return None

        # # TODO
        # if self.current_iter.key() is None:
        #     return None

        # Return nil for the value when the cursor is pointing to a nested
        # bucket.
        if pyutil.bytes_has_prefix(self.current_iter.key(), bucketIndexPrefix):
            return None

        return copy_slice(self.current_iter.value())


# cursorType defines the type of cursor to create.
class CursorType(IntEnum):
    # ctKeys iterates through all of the keys in a given bucket.
    ctKeys = 0

    # ctBuckets iterates through all directly nested buckets in a given
    # bucket.
    ctBuckets = 1

    # ctFull iterates through both the keys and the directly nested buckets
    # in a given bucket.
    ctFull = 2


# cursorFinalizer is either invoked when a cursor is being garbage collected or
# called manually to ensure the underlying cursor iterators are released.
def cursor_finalizer(c: Cursor):
    c.db_iter.release()
    c.pending_iter.release()


# BytesPrefix returns start, limit that satisfy the given prefix.
# This only applicable for the standard 'bytes comparer'.
def helper_bytes_prefix(prefix: bytes):
    limit = bytes()
    i = len(prefix) - 1
    while i >= 0:
        c = prefix[i]
        if c < 0xff:
            limit = prefix[:i] + bytes([c + 1])
            break
        i -= 1
    return prefix, limit


# newCursor returns a new cursor for the given bucket, bucket ID, and cursor
# type.
#
# NOTE: The caller is responsible for calling the cursorFinalizer function on
# the returned cursor.
def new_cursor(b: Bucket, bucket_id: bytes, cursor_type: CursorType) -> Cursor:
    if cursor_type == CursorType.ctKeys:
        prefix = bucket_id
        start, limit = helper_bytes_prefix(prefix)
        db_iter = b.tx.snapshot.new_iterator(start, limit)
        pending_iter = new_ldb_treap_iter(b.tx, start, limit)
    elif cursor_type == CursorType.ctBuckets:
        prefix = bucketIndexPrefix + bucket_id
        start, limit = helper_bytes_prefix(prefix)
        db_iter = b.tx.snapshot.new_iterator(start, limit)
        pending_iter = new_ldb_treap_iter(b.tx, start, limit)
    else:
        # About key
        prefix = bucket_id
        start, limit = helper_bytes_prefix(prefix)
        key_db_iter = b.tx.snapshot.new_iterator(start, limit)
        key_pending_iter = new_ldb_treap_iter(b.tx, start, limit)

        # About bucket
        prefix = bucketIndexPrefix + bucket_id
        start, limit = helper_bytes_prefix(prefix)
        bucket_db_iter = b.tx.snapshot.new_iterator(start, limit)
        bucket_pending_iter = new_ldb_treap_iter(b.tx, start, limit)

        # Merge them
        db_iter = new_merged_iterator([key_db_iter, bucket_db_iter])
        pending_iter = new_merged_iterator([key_pending_iter, bucket_pending_iter])

    return Cursor(bucket=b, db_iter=db_iter, pending_iter=pending_iter)


dbType = "ffldb"


# TODO
def roll_back_panic(tx):
    pass


# db represents a collection of namespaces which are persisted and implements
# the database.DB interface.  All database access is performed through
# transactions which are obtained through the specific Namespace.
class DB(database.DB):
    def __init__(self, store, cache, write_lock=None, close_lock=None, closed=None):
        """

        :param pyutil.Lock write_lock:
        :param pyutil.RWLock close_lock:
        :param bool closed:
        :param BlockStore store:
        :param DBCache cache:
        """

        # Limit to one write transaction at a time.
        self.write_lock = write_lock or pyutil.Lock()

        # Make database close block while txns active.
        self.close_lock = close_lock or pyutil.RWLock()

        # Is the database closed?
        self.closed = closed or False

        # Handles read/writing blocks to flat files.
        self.store = store

        # Cache layer which wraps underlying leveldb DB.
        self.cache = cache

    # Type returns the database driver type the current database instance was
    # created with.
    #
    # This function is part of the database.DB interface implementation.
    def type(self) -> str:
        return dbType

    # begin is the implementation function for the Begin database method.  See its
    # documentation for more details.
    #
    # This function is only separate because it returns the internal transaction
    # which is used by the managed transaction code while the database method
    # returns the interface.
    def _begin(self, writeable: bool) -> Transaction:
        # Whenever a new writable transaction is started, grab the write lock
        # to ensure only a single write transaction can be active at the same
        # time.  This lock will not be released until the transaction is
        # closed (via Rollback or Commit).
        if writeable:
            self.write_lock.acquire()

        # Whenever a new transaction is started, grab a read lock against the
        # database to ensure Close will wait for the transaction to finish.
        # This lock will not be released until the transaction is closed (via
        # Rollback or Commit).
        self.close_lock.reader_acquire()
        if self.closed:
            self.close_lock.reader_release()
            if writeable:
                self.write_lock.release()

            raise DBError(ErrorCode.ErrDbNotOpen, errDbNotOpenStr)

        # Grab a snapshot of the database cache (which in turn also handles the
        # underlying database).
        try:
            snapshot = self.cache.snapshot()
        except Exception as e:
            _logger.debug(e)
            self.close_lock.reader_release()
            if writeable:
                self.write_lock.release()
            raise e

        # The metadata and block index buckets are internal-only buckets, so
        # they have defined IDs.
        tx = Transaction(
            writable=writeable,
            db=self,
            snapshot=snapshot,
            pending_keys=treap.Mutable(),
            pending_remove=treap.Mutable(),
        )
        tx.meta_bucket = Bucket(tx=tx, id=metadataBucketID)
        tx.block_idx_bucket = Bucket(tx=tx, id=blockIdxBucketID)
        return tx

    # Begin starts a transaction which is either read-only or read-write depending
    # on the specified flag.  Multiple read-only transactions can be started
    # simultaneously while only a single read-write transaction can be started at a
    # time.  The call will block when starting a read-write transaction when one is
    # already open.
    #
    # NOTE: The transaction must be closed by calling Rollback or Commit on it when
    # it is no longer needed.  Failure to do so will result in unclaimed memory.
    #
    # This function is part of the database.DB interface implementation.
    def begin(self, writeable: bool) -> database.Tx:
        return self._begin(writeable)

    # View invokes the passed function in the context of a managed read-only
    # transaction with the root bucket for the namespace.  Any errors returned from
    # the user-supplied function are returned from this function.
    #
    # This function is part of the database.DB interface implementation.
    def view(self, fn):
        # Start a read-only transaction.
        tx = self._begin(writeable=False)

        # TOCHANGE So strange here     # golang defer rollbackOnPanic(tx) pattern
        # try:
        tx.managed = True
        try:
            fn(tx)
        except Exception as e:
            try:
                tx.managed = False
                tx.rollback()
            except Exception as e2:
                pass
            raise e

        tx.managed = False
        return tx.rollback()

        # except Exception as e:
        #     # Since the user-provided function might panic, ensure the transaction
        #     # releases all mutexes and resources.  There is no guarantee the caller
        #     # won't use recover and keep going.  Thus, the database must still be
        #     # in a usable state on panics due to caller issues.
        #     tx.managed = False
        #     try:
        #         tx.rollback()
        #     except:
        #         pass
        #     raise e

    # Update invokes the passed function in the context of a managed read-write
    # transaction with the root bucket for the namespace.  Any errors returned from
    # the user-supplied function will cause the transaction to be rolled back and
    # are returned from this function.  Otherwise, the transaction is committed
    # when the user-supplied function returns a nil error.
    #
    # This function is part of the database.DB interface implementation.
    def update(self, fn):
        tx = self._begin(writeable=True)

        # TOCHANGE So strange here     # golang defer rollbackOnPanic(tx) pattern
        # try:
        tx.managed = True
        try:
            fn(tx)
        except Exception as e:
            try:
                tx.managed = False  # ?
                tx.rollback()
            except Exception as e2:
                pass
            raise e

        tx.managed = False
        try:
            tx.commit()
        except Exception as e:
            tx.rollback()
            raise e

        return

        # except Exception as e:
        #     # Since the user-provided function might panic, ensure the transaction
        #     # releases all mutexes and resources.  There is no guarantee the caller
        #     # won't use recover and keep going.  Thus, the database must still be
        #     # in a usable state on panics due to caller issues.
        #     tx.managed = False
        #     try:
        #         tx.rollback()
        #     except:
        #         pass
        #
        #     raise e

    # Close cleanly shuts down the database and syncs all data.  It will block
    # until all database transactions have been finalized (rolled back or
    # committed).
    #
    # This function is part of the database.DB interface implementation.
    def close(self):
        # Since all transactions have a read lock on this mutex, this will
        # cause Close to wait for all readers to complete.
        self.close_lock.lock()

        # TOCHANGE Damn pattern
        try:
            if self.closed:
                raise DBError(ErrorCode.ErrDbNotOpen, errDbNotOpenStr)

            self.closed = True

            # NOTE: Since the above lock waits for all transactions to finish and
            # prevents any new ones from being started, it is safe to flush the
            # cache and clear all state without the individual locks.

            # Close the database cache which will flush any existing entries to
            # disk and close the underlying leveldb database.  Any error is saved
            # and returned at the end after the remaining cleanup since the
            # database will be marked closed even if this fails given there is no
            # good way for the caller to recover from a failure here anyways.
            self.cache.close()

            # Close any open flat files that house the blocks.
            try:
                wc = self.store.write_cursor
                if wc.cur_file.file is not None:
                    try:
                        wc.cur_file.file.close()
                    except:
                        pass
                    wc.cur_file.file = None

                for _, block_file in self.store.open_block_files.items():
                    try:
                        block_file.file.close()
                    except:
                        pass
            finally:
                self.store.open_block_files = {}
                self.store.open_blocks_lru = LRUList()
                self.store.file_num_to_lru_elem = {}

            return
        finally:
            self.close_lock.unlock()


# initDB creates the initial buckets and values used by the package.  This is
# mainly in a separate function for testing purposes.
def init_db(ldb):
    # The starting block file write cursor location is file num 0, offset
    # 0.
    batch = ldb.write_batch()
    batch.put(bucketized_key(metadataBucketID, writeLocKeyName),
              serialize_write_row(cur_block_file_num=0, cur_file_offset=0))

    # Create block index bucket and set the current bucket id.
    #
    # NOTE: Since buckets are virtualized through the use of prefixes,
    # there is no need to store the bucket index data for the metadata
    # bucket in the database.  However, the first bucket ID to use does
    # need to account for it to ensure there are no key collisions.
    batch.put(bucketized_key(metadataBucketID, blockIdxBucketName),
              blockIdxBucketID)
    batch.put(curBucketIDKeyName, blockIdxBucketID)

    try:
        batch.write()
    except Exception as e:
        msg = "failed to initialize metadata database: %s" % repr(e)
        raise convert_err(msg, e)
    return


# openDB opens the database at the provided path.  database.ErrDbDoesNotExist
# is returned if the database doesn't exist and the create flag is not set.
def open_db(db_path: str, network: wire.BitcoinNet, create: bool) -> database.DB:
    # Error if the database doesn't exist and the create flag is not set.
    metadata_db_path = os.path.join(db_path, metadataDbName)
    db_exists = os.path.exists(metadata_db_path)
    if not create and not db_exists:
        msg = "database %s does not exist" % metadata_db_path
        raise DBError(ErrorCode.ErrDbDoesNotExist, msg)

    # Ensure the full path to the database exists.
    if not db_exists:
        # The error can be ignored here since the call to
        # leveldb.OpenFile will fail if the directory couldn't be
        # created.
        try:
            os.makedirs(db_path, mode=0o700)
        except:
            pass

    # Open the metadata database (will create it if needed).
    opt = {
        "create_if_missing": create,
        "error_if_exists": create,
        # "compression": False,  # TOCHECK why raise '\\'compression\\' must be None or a string' error?
    }
    try:
        ldb = plyvel.DB(metadata_db_path, **opt)
    except Exception as e:
        raise convert_err(repr(e), e)

    # Create the block store which includes scanning the existing flat
    # block files to find what the current write cursor position is
    # according to the data that is actually on disk.  Also create the
    # database cache which wraps the underlying leveldb database to provide
    # write caching.
    store = BlockStore.new_from_path_network(db_path, network)
    cache = DBCache(ldb=ldb, store=store)
    pdb = DB(store=store, cache=cache)

    if create:
        init_db(pdb.cache.ldb)

    return reconcile_db(pdb)
