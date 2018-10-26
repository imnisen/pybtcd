
# dbCacheSnapshot defines a snapshot of the database cache and underlying
# database at a particular point in time.
class DBCacheSnapshot:
    def __init__(self, db_snapshot, pending_keys, pending_remove):
        self.db_snapshot = db_snapshot
        self.pending_keys = pending_keys
        self.pending_remove = pending_remove

