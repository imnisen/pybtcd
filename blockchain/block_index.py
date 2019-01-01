import database
import pyutil
from .chainio import *


# blockIndex provides facilities for keeping track of an in-memory index of the
# block chain.  Although the name block chain suggests a single chain of
# blocks, it is actually a tree-shaped structure where any node can have
# multiple children.  However, there can only be one active branch which does
# indeed form a chain from the tip all the way back to the genesis block.
class BlockIndex:
    def __init__(self, db, chain_params, lock=None, index=None, dirty=None):
        """

        :param database.DB db:
        :param *chaincfg.Params chain_params:
        :param RWLock lock:
        :param map[chainhash.Hash]*blockNode index:
        :param map[*blockNode]struct{} dirty:
        """
        # The following fields are set when the instance is created and can't
        # be changed afterwards, so there is no need to protect them with a
        # separate mutex.
        self.db = db
        self.chain_params = chain_params

        self.lock = lock or pyutil.RWLock()
        self.index = index or dict()
        self.dirty = dirty or dict()  # TOCHANGEchange to set

    # HaveBlock returns whether or not the block index contains the provided hash.
    #
    # This function is safe for concurrent access.
    def have_block(self, hash: chainhash.Hash) -> bool:
        self.lock.reader_acquire()
        has_block = hash in self.index
        self.lock.reader_release()
        return has_block

    # LookupNode returns the block node identified by the provided hash.  It will
    # return nil if there is no entry for the hash.
    #
    # This function is safe for concurrent access.
    def lookup_node(self, hash: chainhash.Hash) -> BlockNode:
        self.lock.reader_acquire()
        node = self.index.get(hash, None)
        self.lock.reader_release()
        return node

    # AddNode adds the provided node to the block index and marks it as dirty.
    # Duplicate entries are not checked so it is up to caller to avoid adding them.
    #
    # This function is safe for concurrent access.
    def add_node(self, node: BlockNode):
        self.lock.writer_acquire()
        self._add_node(node)
        self.dirty[node] = {}  # TODO
        self.lock.writer_release()
        return

    # addNode adds the provided node to the block index, but does not mark it as
    # dirty. This can be used while initializing the block index.
    #
    # This function is NOT safe for concurrent access.
    def _add_node(self, node: BlockNode):
        self.index[node.hash] = node

    # NodeStatus provides concurrent-safe access to the status field of a node.
    #
    # This function is safe for concurrent access.
    def node_status(self, node: BlockNode):
        self.lock.reader_acquire()
        status = node.status
        self.lock.reader_release()
        return status

    # SetStatusFlags flips the provided status flags on the block node to on,
    # regardless of whether they were on or off previously. This does not unset any
    # flags currently on.
    #
    # This function is safe for concurrent access.
    def set_status_flags(self, node: BlockNode, flags: BlockStatus):
        self.lock.writer_acquire()
        node.status |= flags
        self.dirty[node] = {}
        self.lock.writer_release()

    # UnsetStatusFlags flips the provided status flags on the block node to off,
    # regardless of whether they were on or off previously.
    #
    # This function is safe for concurrent access.
    def unset_status_flags(self, node: BlockNode, flags: BlockStatus):
        self.lock.writer_acquire()
        node.status = node.status & (~ flags)  # TOCHECK it the operator right?
        self.dirty[node] = {}
        self.lock.writer_reslease()

    # flushToDB writes all dirty block nodes to the database. If all writes
    # succeed, this clears the dirty set.
    def flush_to_db(self):
        self.lock.writer_acquire()

        if len(self.dirty) == 0:
            self.lock.writer_release()
            return

        # TOCHECK
        # Will the exception pass as expected ?
        # Is there a better way do this?

        def f(db_tx: database.Tx):
            for node in self.dirty:
                db_store_block_node(db_tx, node)
            return

        try:
            self.db.update(f)
        except Exception as e:
            self.lock.writer_release()
            raise e
        else:
            self.dirty = {}

        self.lock.writer_release()
