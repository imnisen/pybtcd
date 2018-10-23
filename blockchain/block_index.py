# blockIndex provides facilities for keeping track of an in-memory index of the
# block chain.  Although the name block chain suggests a single chain of
# blocks, it is actually a tree-shaped structure where any node can have
# multiple children.  However, there can only be one active branch which does
# indeed form a chain from the tip all the way back to the genesis block.
class BlockIndex:
    def __init__(self, db, chain_params, lock, index, dirty):
        """

        :param database.DB db:
        :param *chaincfg.Params chain_params:
        :param RWLock lock:
        :param map[chainhash.Hash]*blockNode index:
        :param  map[*blockNode]struct{} dirty:
        """
        # The following fields are set when the instance is created and can't
        # be changed afterwards, so there is no need to protect them with a
        # separate mutex.
        self.db = db
        self.chain_params = chain_params

        self.lock = lock
        self.index = index
        self.dirty = dirty

    # HaveBlock returns whether or not the block index contains the provided hash.
    #
    # This function is safe for concurrent access.
    def hash_block(self, hash):
        pass

    # LookupNode returns the block node identified by the provided hash.  It will
    # return nil if there is no entry for the hash.
    #
    # This function is safe for concurrent access.
    def lookup_node(self, hash):
        pass

    # AddNode adds the provided node to the block index and marks it as dirty.
    # Duplicate entries are not checked so it is up to caller to avoid adding them.
    #
    # This function is safe for concurrent access.
    def add_node(self, node):
        pass

    # addNode adds the provided node to the block index, but does not mark it as
    # dirty. This can be used while initializing the block index.
    #
    # This function is NOT safe for concurrent access.
    def _add_node(self, node):
        pass

    # NodeStatus provides concurrent-safe access to the status field of a node.
    #
    # This function is safe for concurrent access.
    def node_status(self, node):
        pass

    # SetStatusFlags flips the provided status flags on the block node to on,
    # regardless of whether they were on or off previously. This does not unset any
    # flags currently on.
    #
    # This function is safe for concurrent access.
    def set_status_flags(node, flags):
        pass

    # UnsetStatusFlags flips the provided status flags on the block node to off,
    # regardless of whether they were on or off previously.
    #
    # This function is safe for concurrent access.
    def unset_status_flags(node, flags):
        pass

    # flushToDB writes all dirty block nodes to the database. If all writes
    # succeed, this clears the dirty set.
    def flush_to_db(self):
        pass
