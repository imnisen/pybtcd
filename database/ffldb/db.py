import database
import pyutil


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

    def remove_active_iter(self):
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
