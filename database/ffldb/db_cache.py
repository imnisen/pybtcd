import plyvel
from .utils import *
import pyutil
import database.treap as treap
import time

# dbCacheSnapshot defines a snapshot of the database cache and underlying
# database at a particular point in time.
class DBCacheSnapshot:
    def __init__(self, db_snapshot, pending_keys, pending_remove):
        """

        :param plyvel.Snapshot db_snapshot:
        :param treap.Immutable pending_keys:
        :param treap.Immutable pending_remove:
        """
        self.db_snapshot = db_snapshot
        self.pending_keys = pending_keys
        self.pending_remove = pending_remove

    # Has returns whether or not the passed key exists.
    def has(self, key: bytes):
        # Check the cached entries first.
        if self.pending_remove.has(key):
            return False

        if self.pending_keys.has(key):
            return True

        # consult the database
        return self.db_snapshot.get(key) is not None

    # Get returns the value for the passed key.  The function will return nil when
    # the key does not exist.
    def get(self, key: bytes):
        # Check the cached entries first.
        if self.pending_remove.has(key):
            return None

        value = self.pending_keys.get(key)
        if value is not None:
            return value

        # consult the database
        return self.db_snapshot.get(key)

    # Release releases the snapshot.
    def release(self):
        self.db_snapshot.release()
        self.pending_keys = None
        self.pending_remove = None
        return



# dbCache provides a database cache layer backed by an underlying database.  It
# allows a maximum cache size and flush interval to be specified such that the
# cache is flushed to the database when the cache size exceeds the maximum
# configured value or it has been longer than the configured interval since the
# last flush.  This effectively provides transaction batching so that callers
# can commit transactions at will without incurring large performance hits due
# to frequent disk syncs.
class DBCache:
    def __init__(self, ldb, store, max_size, flush_interval, last_flush,
                 cache_lock=None, cached_keys=None, cached_remove=None):
        """

        :param plyvel.DB ldb:
        :param BlockStore store:
        :param uint64 max_size:
        :param time.Duration flush_interval:
        :param time.Time last_flush:
        :param RWLock cache_lock:
        :param treap.Immutable cached_keys:
        :param treap.Immutable cached_remove:
        """

        # ldb is the underlying leveldb DB for metadata.
        self.ldb = ldb

        # store is used to sync blocks to flat files.
        self.store = store

        # The following fields are related to flushing the cache to persistent
        # storage.  Note that all flushing is performed in an opportunistic
        # fashion.  This means that it is only flushed during a transaction or
        # when the database cache is closed.
        #
        # maxSize is the maximum size threshold the cache can grow to before
        # it is flushed.
        #
        # flushInterval is the threshold interval of time that is allowed to
        # pass before the cache is flushed.
        #
        # lastFlush is the time the cache was last flushed.  It is used in
        # conjunction with the current time and the flush interval.
        #
        # NOTE: These flush related fields are protected by the database write
        # lock.
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.last_flush = last_flush
        
        # The following fields hold the keys that need to be stored or deleted
        # from the underlying database once the cache is full, enough time has
        # passed, or when the database is shutting down.  Note that these are
        # stored using immutable treaps to support O(1) MVCC snapshots against
        # the cached data.  The cacheLock is used to protect concurrent access
        # for cache updates and snapshots.
        self.cache_lock = cache_lock or pyutil.RWLock
        self.cached_keys = cached_keys or treap.Immutable()
        self.cached_remove = cached_remove or treap.Immutable()

    # Snapshot returns a snapshot of the database cache and underlying database at
    # a particular point in time.
    #
    # The snapshot must be released after use by calling Release.
    def snapshot(self) -> DBCacheSnapshot:
        try:
            db_snapshot = self.ldb.snapshot()
        except Exception as e:
            msg = "failed to open transaction"
            raise convert_err(msg, e)

        self.cache_lock.r_lock()
        cache_snapshot = DBCacheSnapshot(
            db_snapshot=db_snapshot,
            pending_keys=self.cached_keys,
            pending_remove=self.cached_remove
        )

        self.cache_lock.r_unlock()
        return cache_snapshot


    # No Need
    # # updateDB invokes the passed function in the context of a managed leveldb
    # # transaction.  Any errors returned from the user-supplied function will cause
    # # the transaction to be rolled back and are returned from this function.
    # # Otherwise, the transaction is committed when the user-supplied function
    # # returns a nil error.
    # def update_db(self, fn):
    #     pass

    
    # commitTreaps atomically commits all of the passed pending add/update/remove
    # updates to the underlying database.
    def commit_treaps(self, pending_keys: treap.Immutable, pending_remove: treap.Immutable):

        try:
            with self.ldb.write_batch(transction=True) as b:

                for k, v in pending_keys.for_each2():
                    b.put(k, v)

                for k, v in pending_remove.for_each2():
                    b.delete(k, v)
        except Exception as e:
            raise convert_err("failed to commit", e)
        return

    
    # flush flushes the database cache to persistent storage.  This involes syncing
    # the block store and replaying all transactions that have been applied to the
    # cache to the underlying database.
    #
    # This function MUST be called with the database write lock held.
    def flush(self):
        self.last_flush = int(time.time)
        
        # Sync the current write file associated with the block store.  This is
        # necessary before writing the metadata to prevent the case where the
        # metadata contains information about a block which actually hasn't
        # been written yet in unexpected shutdown scenarios.
        self.store.sync_blocks()

        # Since the cached keys to be added and removed use an immutable treap,
        # a snapshot is simply obtaining the root of the tree under the lock
        # which is used to atomically swap the root.
        self.cache_lock.r_lock()
        cached_keys = self.cached_keys
        cached_remove = self.cached_remove
        self.cache_lock.r_unlock()

        # Nothing to do if there is no data to flush.
        if cached_keys.len() == 0 and cached_remove.len() == 0:
            return

        # Perform all leveldb updates using an atomic transaction.
        self.commit_treaps(cached_keys, cached_remove)

        # Clear the cache since it has been flushed.
        self.cache_lock.lock()
        self.cached_keys = treap.Immutable()
        self.cached_remove = treap.Immutable()
        self.cache_lock.unlock()

        return


    # needsFlush returns whether or not the database cache needs to be flushed to
    # persistent storage based on its current size, whether or not adding all of
    # the entries in the passed database transaction would cause it to exceed the
    # configured limit, and how much time has elapsed since the last time the cache
    # was flushed.
    #
    # This function MUST be called with the database write lock held.
    def needs_flush(self, tx):  # TODO define the type of tx
        # A flush is needed when more time has elapsed than the configured
	    # flush interval.
        now = int(time.time())
        if now - self.last_flush > self.flush_interval:
            return True

        # A flush is needed when the size of the database cache exceeds the
        # specified max cache size.  The total calculated size is multiplied by
        # 1.5 here to account for additional memory consumption that will be
        # needed during the flush as well as old nodes in the cache that are
        # referenced by the snapshot used by the transaction.

        snap = tx.snapshot
        total_size = snap.pending_keys.size() + snap.pending_remove.size()
        total_size *= 1.5

        return total_size > self.max_size

    # commitTx atomically adds all of the pending keys to add and remove into the
    # database cache.  When adding the pending keys would cause the size of the
    # cache to exceed the max cache size, or the time since the last flush exceeds
    # the configured flush interval, the cache will be flushed to the underlying
    # persistent database.
    #
    # This is an atomic operation with respect to the cache in that either all of
    # the pending keys to add and remove in the transaction will be applied or none
    # of them will.
    #
    # The database cache itself might be flushed to the underlying persistent
    # database even if the transaction fails to apply, but it will only be the
    # state of the cache without the transaction applied.
    #
    # This function MUST be called during a database write transaction which in
    # turn implies the database write lock will be held.
    def commit_tx(self, tx):  # TODO define the type of tx
        # # Flush the cache and write the current transaction directly to the
        # # database if a flush is needed.
        # if self.needs_flush(tx):
        #     self.flush()
        #
        #     #
        pass



        


