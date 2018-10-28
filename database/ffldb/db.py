import chainhash
import database
import pyutil
import database.treap as treap


# bulkFetchData is allows a block location to be specified along with the
# index it was requested from.  This in turn allows the bulk data loading
# functions to sort the data accesses based on the location to improve
# performance while keeping track of which result the data is for.
class BulkFetchData:
    def __init__(self, block_location, reply_index):
        self.block_location = block_location
        self.reply_index = reply_index


# pendingBlock houses a block that will be written to disk when the database
# transaction is committed.
class PendingBlock:
    def __init__(self, pb_hash, pb_bytes):
        self.pb_hash = pb_hash
        self.pb_bytes = pb_bytes


# transaction represents a database transaction.  It can either be read-only or
# read-write and implements the database.Tx interface.  The transaction
# provides a root bucket against which all read and writes occur.
class Transaction:
    def __init__(self, managed=None, closed=None, writable=None, db=None, snapshot=None, meta_bucket=None,
                 block_idx_bucket=None, pending_blocks=None, pending_block_data=None,
                 pending_keys=None, pending_remove=None,
                 active_iter_lock=None, active_iters=None, ):
        """

        :param bool managed:
        :param bool closed:
        :param bool writable:
        :param *db db:
        :param *dbCacheSnapshot snapshot:
        :param *bucket meta_bucket:
        :param *bucket block_idx_bucket:
        :param map[chainhash.Hash]int pending_blocks:
        :param []pendingBlock pending_block_data:
        :param *treap.Mutable pending_keys:
        :param *treap.Mutable pending_remove:
        :param RWLock active_iter_lock:
        :param []*treap.Iterator active_iters:
        """
        # Is the transaction managed?
        self.managed = managed

        # Is the transaction closed?
        self.closed = closed

        # Is the transaction writable?
        self.writable = writable

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
        self.pending_blocks = pending_blocks
        self.pending_block_data = pending_block_data

        # Keys that need to be stored or deleted on commit.
        self.pending_keys = pending_keys
        self.pending_remove = pending_remove

        # Active iterators that need to be notified when the pending keys have
        # been updated so the cursors can properly handle updates to the
        # transaction state.
        self.active_iter_lock = active_iter_lock
        self.active_iters = active_iters

    # removeActiveIter removes the passed iterator from the list of active
    # iterators against the pending keys treap.
    def remove_active_iter(self, the_iter: treap.Iterator):
        pass

    # addActiveIter adds the passed iterator to the list of active iterators for
    # the pending keys treap.
    def add_active_iter(self, the_iter: treap.Iterator):
        pass

    # notifyActiveIters notifies all of the active iterators for the pending keys
    # treap that it has been updated.
    def notify_active_iters(self):
        pass

    # checkClosed returns an error if the the database or transaction is closed.
    def check_closed(self):
        pass

    # hasKey returns whether or not the provided key exists in the database while
    # taking into account the current transaction state.
    def has_key(self, key: bytes) -> bool:
        pass

    # putKey adds the provided key to the list of keys to be updated in the
    # database when the transaction is committed.
    #
    # NOTE: This function must only be called on a writable transaction.  Since it
    # is an internal helper function, it does not check.
    def put_key(self, key: bytes, value: bytes):
        pass

    # fetchKey attempts to fetch the provided key from the database cache (and
    # hence underlying database) while taking into account the current transaction
    # state.  Returns nil if the key does not exist.
    def fetch_key(self, key: bytes) -> bytes:
        pass

    # deleteKey adds the provided key to the list of keys to be deleted from the
    # database when the transaction is committed.  The notify iterators flag is
    # useful to delay notifying iterators about the changes during bulk deletes.
    #
    # NOTE: This function must only be called on a writable transaction.  Since it
    # is an internal helper function, it does not check.
    def delete_key(self, key: bytes, notify_iterators: bool):
        pass

    # nextBucketID returns the next bucket ID to use for creating a new bucket.
    #
    # NOTE: This function must only be called on a writable transaction.  Since it
    # is an internal helper function, it does not check.
    def next_bucket_id(self):
        pass

    # Metadata returns the top-most bucket for all metadata storage.
    #
    # This function is part of the database.Tx interface implementation.
    def meta_data(self):
        pass

    # hasBlock returns whether or not a block with the given hash exists.
    def _has_block(self, hash: chainhash.Hash):
        pass

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
    def store_block(self):
        pass

    # HasBlock returns whether or not a block with the given hash exists in the
    # database.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Tx interface implementation.
    def has_block(self, hash: chainhash.Hash):
        pass

    # HasBlocks returns whether or not the blocks with the provided hashes
    # exist in the database.
    #
    # Returns the following errors as required by the interface contract:
    #   - ErrTxClosed if the transaction has already been closed
    #
    # This function is part of the database.Tx interface implementation.
    def has_blocks(self, hashes: [chainhash.Hash]):
        pass

    # fetchBlockRow fetches the metadata stored in the block index for the provided
    # hash.  It will return ErrBlockNotFound if there is no entry.
    def fetch_block_row(self, hash: chainhash.Hash):
        pass

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
        pass

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
        pass

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
        pass

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
    def fetch_blocks(self):
        pass


# cursor is an internal type used to represent a cursor over key/value pairs
# and nested buckets of a bucket and implements the database.Cursor interface.
class Cursor(database.Cursor):
    def __init__(self, bucket, db_iter, pending_iter, current_iter):
        self._bucket = bucket
        # TODO need other fields?

    # Bucket returns the bucket the cursor was created for.
    #
    # This function is part of the database.Cursor interface implementation.
    def bucket(self):
        # Ensure transaction state is valid.
        self._bucket.tx.check_closed()

        return self._bucket

    def delete(self):
        pass


# db represents a collection of namespaces which are persisted and implements
# the database.DB interface.  All database access is performed through
# transactions which are obtained through the specific Namespace.
class DB(database.DB):
    def __init__(self, write_lock=None, close_lock=None, closed=None, store=None, cache=None, ):
        """

        :param pyutil.Lock write_lock:
        :param pyutil.RWLock close_lock:
        :param bool closed:
        :param *blockStore store:
        :param *dbCache cache:
        """

        # Limit to one write transaction at a time.
        self.write_lock = write_lock or pyutil.Lock()

        # Make database close block while txns active.
        self.close_lock = close_lock or pyutil.RWLock()

        # Is the database closed?
        self.closed = closed or False

        # Handles read/writing blocks to flat files.
        self.store = store  # TODO the default value

        # Cache layer which wraps underlying leveldb DB.
        self.cache = cache  # TODO the default value
