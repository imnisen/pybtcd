import plyvel
from .utils import *
import pyutil
import database.treap as treap
import time
from .leveldb_iterator import Iterator
from functools import wraps

# defaultCacheSize is the default size for the database cache.
defaultCacheSize = 100 * 1024 * 1024  # 100 MB

# defaultFlushSecs is the default number of seconds to use as a
# threshold in between database cache flushes when the cache size has
# not been exceeded.
defaultFlushSecs = 300  # 5 minutes

# ldbBatchHeaderSize is the size of a leveldb batch header which
# includes the sequence header and record counter.
#
# ldbRecordIKeySize is the size of the ikey used internally by leveldb
# when appending a record to a batch.
#
# These are used to help preallocate space needed for a batch in one
# allocation instead of letting leveldb itself constantly grow it.
# This results in far less pressure on the GC and consequently helps
# prevent the GC from allocating a lot of extra unneeded space.
ldbBatchHeaderSize = 12
ldbRecordIKeySize = 8


class DBCacheIterator(Iterator):
    def __init__(self, cache_snapshot, db_iter, cache_iter, current_iter=None, released=None):
        """

        :param cache_snapshot:
        :param db_iter:
        :param cache_iter:
        :param current_iter:
        :param released:
        """
        self.cache_snapshot = cache_snapshot
        self.db_iter = db_iter
        self.cache_iter = cache_iter
        self.current_iter = current_iter or None
        self.released = released or False

    # skipPendingUpdates skips any keys at the current database iterator position
    # that are being updated by the cache.  The forwards flag indicates the
    # direction the iterator is moving.
    def _skip_pending_updates(self, forwards: bool):
        while self.db_iter.valid():

            key = self.db_iter.key()

            if self.cache_snapshot.pending_remove.has(key):
                skip = True
            elif self.cache_snapshot.pending_keys.has(key):
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
    # being updated by the cache and sets the current iterator to the appropriate
    # iterator depending on their validity and the order they compare in while taking
    # into account the direction flag.  When the iterator is being moved forwards
    # and both iterators are valid, the iterator with the smaller key is chosen and
    # vice versa when the iterator is being moved backwards.
    def _choose_iterator(self, forwards: bool) -> bool:
        # Skip any keys at the current database iterator position that are
        # being updated by the transaction.
        self._skip_pending_updates(forwards)

        # When both iterators are exhausted, the iterator is exhausted too.
        if not self.db_iter.valid() and not self.cache_iter.valid():
            self.current_iter = None
            return False

        # Choose the database iterator when the cache keys iterator is
        # exhausted.
        if not self.cache_iter.valid():
            self.current_iter = self.db_iter
            return True

        # Choose the cache iterator when the database iterator is exhausted.
        if not self.db_iter.valid():
            self.current_iter = self.cache_iter
            return True

            # Both iterators are valid, so choose the iterator with either the
            # smaller or larger key depending on the forwards flag.
        compare = byte_compare(self.db_iter.key(), self.cache_iter.key())
        if forwards and compare > 0 or (not forwards and compare < 0):
            self.current_iter = self.cache_iter
        else:
            self.current_iter = self.db_iter

        return True

    # First positions the iterator at the first key/value pair and returns whether
    # or not the pair exists.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def first(self) -> bool:
        x = self.db_iter.first()  # should return false not true
        y = self.cache_iter.first()
        return self._choose_iterator(True)

    # Last positions the iterator at the last key/value pair and returns whether or
    # not the pair exists.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def last(self) -> bool:
        self.db_iter.last()
        self.cache_iter.last()
        return self._choose_iterator(False)

    # Next moves the iterator one key/value pair forward and returns whether or not
    # the pair exists.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def next(self) -> bool:
        if self.current_iter is None:
            return False

        self.current_iter.next()
        return self._choose_iterator(True)

    # Next moves the iterator one key/value pair forward and returns whether or not
    # the pair exists.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def prev(self):
        if self.current_iter is None:
            return False

        self.current_iter.prev()
        return self._choose_iterator(False)

    # Seek positions the iterator at the first key/value pair that is greater than
    # or equal to the passed seek key.  Returns false if no suitable key was found.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def seek(self, key: bytes) -> bool:
        self.db_iter.seek(key)
        self.cache_iter.seek(key)
        return self._choose_iterator(True)

    # Valid indicates whether the iterator is positioned at a valid key/value pair.
    # It will be considered invalid when the iterator is newly created or exhausted.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def valid(self) -> bool:
        return self.current_iter is not None

    # Key returns the current key the iterator is pointing to.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def key(self) -> bytes or None:
        if self.current_iter is None:
            return None

        return self.current_iter.key()

    # Value returns the current value the iterator is pointing to.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def value(self) -> bytes or None:
        if self.current_iter is None:
            return None

        return self.current_iter.value()

    # Release releases the iterator by removing the underlying treap iterator from
    # the list of active iterators against the pending keys treap.
    #
    # This is part of the leveldb iterator.Iterator interface implementation.
    def release(self):
        if not self.released:
            self.db_iter.release()
            self.cache_iter.release()
            self.current_iter = None
            self.released = True

        return


# ldbCacheIter wraps a treap iterator to provide the additional functionality
# needed to satisfy the leveldb iterator.Iterator interface.
class LdbCacheIter:
    def __init__(self, iter):
        self.the_iter = iter

    def __getattr__(self, attr):
        return getattr(self.the_iter, attr)

    # required by leveldb Iterator
    def release(self):
        pass


def new_ldb_cache_iter(snap, start, limit) -> LdbCacheIter:
    iter = snap.pending_keys.iterator(start, limit)
    return LdbCacheIter(iter=iter)

#
# def exception_return_as_false(fn):
#     @wraps(fn)
#     def inner_fn(self, *args, **kwargs):
#         try:
#             x = fn(self, *args, **kwargs)
#             return x
#         except:
#             return False
#
#     return inner_fn
#
#
# def exception_return_as_None(fn):
#     @wraps(fn)
#     def inner_fn(self, *args, **kwargs):
#         try:
#             return fn(self, *args, **kwargs)
#         except:
#             return None
#
#     return inner_fn

# Need to decide use valid to check valid every time
# or use the return value of first(), next(), etc.
# Let's try make a compatible way
class snapshotRangedIter(Iterator):
    def __init__(self, iter, start=None, limit=None):
        self.raw_iter = iter
        self.start = start
        self.limit = limit

    # Use return value True or False
    def _check_range(self, key):

        if self.start and self.limit and not self.start <= key < self.limit:
            return False

        if self.start and not self.limit and not self.start <= key:
            return False

        if not self.start and self.limit and not key < self.limit:
            return False

        return True

    def valid(self) -> bool:
        return self._check_range(self.raw_iter.key()) and self.raw_iter.valid()

    def key(self) -> bytes or None:
        if self.valid():
            return self.raw_iter.key()
        else:
            return None

    def value(self) -> bytes or None:
        if self.valid():
            return self.raw_iter.value()
        else:
            return None

    def first(self) -> bool:
        if self.start is None:
            self.raw_iter.seek_to_first()
        else:
            self.raw_iter.seek(self.start)
        return self.valid()

    def last(self) -> bool:
        if self.limit is None:
            self.raw_iter.seek_to_last()
        else:
            self.raw_iter.seek(self.limit)
        return self.valid()

    def seek(self, key: bytes) -> bool:
        if self._check_range(key):
            self.raw_iter.seek(key)
            return self.valid()
        else:
            return False

    def next(self) -> bool:
        self.raw_iter.next()
        return self.valid()

    def prev(self) -> bool:
        self.raw_iter.prev()
        return self.valid()

    def release(self):
        return self.raw_iter.close()

    def release_setter(self):
        pass

    def error(self):
        pass


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

    # NewIterator returns a new iterator for the snapshot.  The newly returned
    # iterator is not pointing to a valid item until a call to one of the methods
    # to position it is made.
    #
    # The slice parameter allows the iterator to be limited to a range of keys.
    # The start key is inclusive and the limit key is exclusive.  Either or both
    # can be nil if the functionality is not desired.
    def new_iterator(self, start, limit):

        raw_db_iter = self.db_snapshot.raw_iterator()

        # # Modify the plyvel.RawIterator to statisfy leveldb_iterator.Iterator inteface
        # db_iter.first = db_iter.seek_to_start
        # db_iter.last = db_iter.seek_to_stop
        # db_iter.release = db_iter.close
        # TODO

        db_iter = snapshotRangedIter(raw_db_iter, start=start, limit=limit)

        return DBCacheIterator(
            db_iter=db_iter,
            cache_iter=new_ldb_cache_iter(self, start, limit),
            cache_snapshot=self
        )


# dbCache provides a database cache layer backed by an underlying database.  It
# allows a maximum cache size and flush interval to be specified such that the
# cache is flushed to the database when the cache size exceeds the maximum
# configured value or it has been longer than the configured interval since the
# last flush.  This effectively provides transaction batching so that callers
# can commit transactions at will without incurring large performance hits due
# to frequent disk syncs.
class DBCache:
    def __init__(self, ldb, store, max_size=None, flush_interval=None, last_flush=None,
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
        self.max_size = max_size or defaultCacheSize
        self.flush_interval = flush_interval or defaultFlushSecs
        self.last_flush = last_flush or int(time.time())

        # The following fields hold the keys that need to be stored or deleted
        # from the underlying database once the cache is full, enough time has
        # passed, or when the database is shutting down.  Note that these are
        # stored using immutable treaps to support O(1) MVCC snapshots against
        # the cached data.  The cacheLock is used to protect concurrent access
        # for cache updates and snapshots.
        self.cache_lock = cache_lock or pyutil.RWLock()
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
            with self.ldb.write_batch(transaction=True) as b:

                for k, v in pending_keys.for_each2():
                    b.put(k, v)

                for k, v in pending_remove.for_each2():
                    b.delete(k)
        except Exception as e:
            raise convert_err("failed to commit", e)
        return

    # flush flushes the database cache to persistent storage.  This involes syncing
    # the block store and replaying all transactions that have been applied to the
    # cache to the underlying database.
    #
    # This function MUST be called with the database write lock held.
    def flush(self):
        self.last_flush = int(time.time())

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
        # Flush the cache and write the current transaction directly to the
        # database if a flush is needed.
        if self.needs_flush(tx):
            self.flush()

            # Perform all leveldb updates using an atomic transaction.
            self.commit_treaps(tx.pending_keys, tx.pending_remove)

            # Clear the transaction entries since they have been committed.
            tx.pending_keys = None
            tx.pending_remove = None
            return

        # At this point a database flush is not needed, so atomically commit
        # the transaction to the cache.

        # Since the cached keys to be added and removed use an immutable treap,
        # a snapshot is simply obtaining the root of the tree under the lock
        # which is used to atomically swap the root.
        self.cache_lock.r_lock()
        new_cached_keys = self.cached_keys
        new_cached_remove = self.cached_remove
        self.cache_lock.r_unlock()

        # Apply every key to add in the database transaction to the cache.
        for k, v in tx.pending_keys.for_each2():
            new_cached_remove = new_cached_remove.delete(k)
            new_cached_keys = new_cached_keys.put(k, v)
        tx.pending_keys = None

        # Apply every key to remove in the database transaction to the cache.
        for k, v in tx.pending_remove.for_each2():
            new_cached_keys = new_cached_keys.delete(k)
            new_cached_remove = new_cached_remove.put(k, v)
        tx.pending_remove = None

        # Atomically replace the immutable treaps which hold the cached keys to
        # add and delete.
        self.cache_lock.lock()
        self.cached_keys = new_cached_keys
        self.cached_remove = new_cached_remove
        self.cache_lock.unlock()
        return

    # Close cleanly shuts down the database cache by syncing all data and closing
    # the underlying leveldb database.
    #
    # This function MUST be called with the database write lock held.
    def close(self):  # TOCHANGE The try except thing ungly here
        # Flush any outstanding cached entries to disk.
        try:
            self.flush()
        except Exception as e:
            # Even if there is an error while flushing, attempt to close
            # the underlying database.  The error is ignored since it would
            # mask the flush error.
            try:
                self.ldb.close()
            except Exception:
                pass
            raise e

        # Close the underlying leveldb database.
        try:
            self.ldb.close()
        except Exception as e:
            msg = "failed to close underlying leveldb database"
            raise convert_err(msg, e)

        return
