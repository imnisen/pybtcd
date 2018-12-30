import chainhash
import wire
from .constant import *
from .difficulty import *
from .block_status import *


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
    def init_from(cls, block_header, parent: 'BlockNode' or None) -> 'BlockNode':
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
    def ancestor(self, height: int) -> 'BlockNode' or None:
        if height < 0 or height > self.height:
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
        median_timestamp = timestamps[len(timestamps) // 2]
        return median_timestamp
