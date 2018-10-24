from enum import Flag, auto
from .difficulty import *
import pyutil
import chainhash
import wire
from .validate import *
import database
from .chainio import *



# blockStatus is a bit field representing the validation state of the block.
class BlockStatus(Flag):
    # statusDataStored indicates that the block's payload is stored on disk.
    statusDataStored = 1

    # statusValid indicates that the block has been fully validated.
    statusValid = auto()

    # statusValidateFailed indicates that the block has failed validation.
    statusValidateFailed = auto()

    # statusInvalidAncestor indicates that one of the block's ancestors has
    # has failed validation, thus the block is also invalid.
    statusInvalidAncestor = auto()

    # statusNone indicates that the block has no validation state flags set.
    #
    # NOTE: This must be defined last in order to avoid influencing iota.
    statusNone = 0

    # HaveData returns whether the full block data is stored in the database. This
    # will return false for a block node where only the header is downloaded or
    # kept.
    def have_data(self) -> bool:
        return self & BlockStatus.statusDataStored != 0

    # KnownValid returns whether the block is known to be valid. This will return
    # false for a valid block that has not been fully validated yet.
    def known_valid(self) -> bool:
        return self & BlockStatus.statusValid != 0

    # KnownInvalid returns whether the block is known to be invalid. This may be
    # because the block itself failed validation or any of its ancestors is
    # invalid. This will return false for invalid blocks that have not been proven
    # invalid yet.
    def known_invalid(self) -> bool:
        return self & (BlockStatus.statusValidateFailed | BlockStatus.statusInvalidAncestor) != 0


# zeroHash is the zero value for a chainhash.Hash and is defined as
# a package level variable to avoid the need to create a new instance
# every time a check is needed.
zeroHash = chainhash.Hash()

# blockNode represents a block within the block chain and is primarily used to
# aid in selecting the best chain to be the main chain.  The main chain is
# stored into the block database.
class BlockNode:
    def __init__(self, parent=None, hash=None, work_sum=None, height=None,
                 version=None, bits=None, nonce=None, timestamp=None, merkle_root=None,
                 status=None):
        """

        :param BlockNode parent:
        :param chainhash.Hash hash:
        :param *big.Int work_sum:
        :param int32 height:
        :param int32 version:
        :param uint32 bits:
        :param uint32 nonce:
        :param int64 timestamp:
        :param chainhash.Hash merkle_root:
        :param blockStatus status:
        """
        # parent is the parent block for this node.
        self.parent = parent or None

        # hash is the double sha 256 of the block.
        self.hash = hash or chainhash.Hash()

        # workSum is the total amount of work in the chain up to and including
        # this node.
        self.work_sum = work_sum or 0

        # height is the position in the block chain.
        self.height = height or 0

        # Some fields from block headers to aid in best chain selection and
        # reconstructing headers from memory.  These must be treated as
        # immutable and are intentionally ordered to avoid padding on 64-bit
        # platforms.
        self.version = version or 0
        self.bits = bits or 0
        self.nonce = nonce or 0
        self.timestamp = timestamp or 0
        self.merkle_root = merkle_root or chainhash.Hash()

        # status is a bitfield representing the validation state of the block. The
        # status field, unlike the other fields, may be written to and so should
        # only be accessed using the concurrent-safe NodeStatus method on
        # blockIndex once the node has been added to the global index.
        self.status = status or BlockStatus(0)

    @classmethod
    def init_from(cls, block_header, parent):
        """

        :param wire.BlockHeader block_header:
        :param parent:
        :return:
        """
        node = cls(
            hash=block_header.block_hash(),
            work_sum=calc_work(block_header.bits),
            version=block_header.version,
            bits=block_header.bits,
            nonce=block_header.nonce,
            timestamp=block_header.timestamp,
            merkle_root=block_header.merkle_root
        )
        if parent:
            node.parent = parent
            node.height = parent.height + 1
            node.work_sum += parent.work_sum

        return node

    # Header constructs a block header from the node and returns it.
    #
    # This function is safe for concurrent access.
    def header(self) -> wire.BlockHeader:
        # No lock is needed because all accessed fields are immutable.
        if self.parent:
            prev_hash = self.parent.hash
        else:
            prev_hash = zeroHash

        return wire.BlockHeader(
            version=self.version,
            prev_block=prev_hash,
            merkle_root=self.merkle_root,
            timestamp=self.timestamp,
            bits=self.bits,
            nonce=self.nonce
        )

    # Ancestor returns the ancestor block node at the provided height by following
    # the chain backwards from this node.  The returned block will be nil when a
    # height is requested that is after the height of the passed node or is less
    # than zero.
    #
    # This function is safe for concurrent access.
    def ancestor(self, height:int) -> 'BlockNode':
        if height < 0 or height> self.height:
            return None

        n = self
        while n and n.height != height:  # So here assumes first node's parent is None
            n = n.parent

        return n


    # RelativeAncestor returns the ancestor block node a relative 'distance' blocks
    # before this node.  This is equivalent to calling Ancestor with the node's
    # height minus provided distance.
    #
    # This function is safe for concurrent access.
    def relative_ancestor(self, distance: int):
        return self.ancestor(self.height - distance)

    # CalcPastMedianTime calculates the median time of the previous few blocks
    # prior to, and including, the block node.
    #
    # This function is safe for concurrent access.
    def calc_past_median_time(self):
        timestamps = []

        # Recursively add parent timestamp until needed
        i = 0
        iter_node = self
        while i < medianTimeBlocks and iter_node is not None:
            timestamps.append(iter_node.timestamp)
            iter_node = iter_node.parent
            i += 1

        timestamps.sort()

        # NOTE: The consensus rules incorrectly calculate the median for even
        # numbers of blocks.  A true median averages the middle two elements
        # for a set with an even number of elements in it.   Since the constant
        # for the previous number of blocks to be used is odd, this is only an
        # issue for a few blocks near the beginning of the chain.  I suspect
        # this is an optimization even though the result is slightly wrong for
        # a few of the first blocks since after the first few blocks, there
        # will always be an odd number of blocks in the set per the constant.
        #
        # This code follows suit to ensure the same rules are used, however, be
        # aware that should the medianTimeBlocks constant ever be changed to an
        # even number, this code will be wrong.
        median_timestamp = timestamps[len(timestamps)//2]
        return median_timestamp


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
        self.dirty = dirty or dict()

    # HaveBlock returns whether or not the block index contains the provided hash.
    #
    # This function is safe for concurrent access.
    def have_block(self, hash: chainhash.Hash)-> bool:
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
        self.dirty[node] = {} # TODO
        self.lock.writer_acquire()
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
    def set_status_flags(self, node:BlockNode, flags: BlockStatus):
        self.lock.writer_acquire()
        node.status |= flags
        self.dirty[node] = {}
        self.lock.writer_acquire()


    # UnsetStatusFlags flips the provided status flags on the block node to off,
    # regardless of whether they were on or off previously.
    #
    # This function is safe for concurrent access.
    def unset_status_flags(self, node:BlockNode, flags: BlockStatus):
        self.lock.writer_acquire()
        node.status = node.status &(~ flags)  # TOCHECK it the operator right?
        self.dirty[node] = {}
        self.lock.writer_acquire()

    # flushToDB writes all dirty block nodes to the database. If all writes
    # succeed, this clears the dirty set.
    def flush_to_db(self):
        self.lock.writer_acquire()

        if len(self.dirty) == 0:
            self.lock.writer_acquire()
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
        except:
            pass
        else:
            self.dirty = {}

        self.lock.writer_acquire()
