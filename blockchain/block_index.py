from enum import Flag, auto


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


# blockNode represents a block within the block chain and is primarily used to
# aid in selecting the best chain to be the main chain.  The main chain is
# stored into the block database.
class BlockNode:
    def __init__(self, parent=None, hash=None, work_sum=None, height=None,
                 version=None, bits=None, nonce=None, timestamp=None, merkle_root=None,
                 status=None):
        """

        :param parent:
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
        self.parent = parent

        # hash is the double sha 256 of the block.
        self.hash = hash

        # workSum is the total amount of work in the chain up to and including
        # this node.
        self.work_sum = work_sum

        # height is the position in the block chain.
        self.height = height

        # Some fields from block headers to aid in best chain selection and
        # reconstructing headers from memory.  These must be treated as
        # immutable and are intentionally ordered to avoid padding on 64-bit
        # platforms.
        self.version = version
        self.bits = bits
        self.nonce = nonce
        self.timestamp = timestamp
        self.merkle_root = merkle_root

        # status is a bitfield representing the validation state of the block. The
        # status field, unlike the other fields, may be written to and so should
        # only be accessed using the concurrent-safe NodeStatus method on
        # blockIndex once the node has been added to the global index.
        self.status = status


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
