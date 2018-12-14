from .block_index import *
import threading


# BlockLocator is used to help locate a specific block.  The algorithm for
# building the block locator is to add the hashes in reverse order until
# the genesis block is reached.  In order to keep the list of locator hashes
# to a reasonable number of entries, first the most recent previous 12 block
# hashes are added, then the step is doubled each loop iteration to
# exponentially decrease the number of hashes as a function of the distance
# from the block being located.
#
# For example, assume a block chain with a side chain as depicted below:
# 	genesis -> 1 -> 2 -> ... -> 15 -> 16  -> 17  -> 18
# 	                              \-> 16a -> 17a
#
# The block locator for block 17a would be the hashes of blocks:
# [17a 16a 15 14 13 12 11 10 9 8 7 6 4 genesis]
class BlockLocator(list):
    pass


# chainView provides a flat view of a specific branch of the block chain from
# its tip back to the genesis block and provides various convenience functions
# for comparing chains.
#
# For example, assume a block chain with a side chain as depicted below:
#   genesis -> 1 -> 2 -> 3 -> 4  -> 5 ->  6  -> 7  -> 8
#                         \-> 4a -> 5a -> 6a
#
# The chain view for the branch ending in 6a consists of:
#   genesis -> 1 -> 2 -> 3 -> 4a -> 5a -> 6a
class ChainView:
    def __init__(self, lock=None, nodes=None):
        """

        :param threading.Lock lock:
        :param []*blockNode nodes:
        """
        self.lock = lock or threading.Lock()
        self.nodes = nodes or []

    @classmethod
    def new_from(cls, tip: BlockNode):
        # The mutex is intentionally not held since this is a constructor.
        c = cls()
        c._set_tip(tip)
        return c

    # genesis returns the genesis block for the chain view.  This only differs from
    # the exported version in that it is up to the caller to ensure the lock is
    # held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _genesis(self):
        if len(self.nodes) == 0:
            return None

        return self.nodes[0]

    # Genesis returns the genesis block for the chain view.
    #
    # This function is safe for concurrent access.
    def genesis(self):
        self.lock.acquire()
        genesis = self._genesis()
        self.lock.release()
        return genesis

    # tip returns the current tip block node for the chain view.  It will return
    # nil if there is no tip.  This only differs from the exported version in that
    # it is up to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _tip(self) -> BlockNode:
        if len(self.nodes) == 0:
            return None

        return self.nodes[-1]

    # Tip returns the current tip block node for the chain view.  It will return
    # nil if there is no tip.
    #
    # This function is safe for concurrent access.
    def tip(self) -> BlockNode:
        self.lock.acquire()
        tip = self._tip()
        self.lock.release()
        return tip

    # setTip sets the chain view to use the provided block node as the current tip
    # and ensures the view is consistent by populating it with the nodes obtained
    # by walking backwards all the way to genesis block as necessary.  Further
    # calls will only perform the minimum work needed, so switching between chain
    # tips is efficient.  This only differs from the exported version in that it is
    # up to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for writes).
    def _set_tip(self, node: BlockNode):
        if node is None:
            self.nodes = []
            return

        # Change self.nodes length to fit with node.height
        # in order to fill self.nodes with node and it's ancestors
        needed = node.height + 1
        if len(self.nodes) < needed:
            self.nodes += [None] * (needed - len(self.nodes))
        elif len(self.nodes) > needed:
            self.nodes = self.nodes[0:needed]

        # let's fill self.nodes, untile we meet some node that right index as we need
        # so we assume it and every node before it is all we need
        while node is not None and self.nodes[node.height] != node:
            self.nodes[node.height] = node
            node = node.parent

        return

    # SetTip sets the chain view to use the provided block node as the current tip
    # and ensures the view is consistent by populating it with the nodes obtained
    # by walking backwards all the way to genesis block as necessary.  Further
    # calls will only perform the minimum work needed, so switching between chain
    # tips is efficient.
    #
    # This function is safe for concurrent access.
    def set_tip(self, node: BlockNode):
        self.lock.acquire()
        self._set_tip(node)
        self.lock.release()

    # height returns the height of the tip of the chain view.  It will return -1 if
    # there is no tip (which only happens if the chain view has not been
    # initialized).  This only differs from the exported version in that it is up
    # to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _height(self):
        return len(self.nodes) - 1

    # Height returns the height of the tip of the chain view.  It will return -1 if
    # there is no tip (which only happens if the chain view has not been
    # initialized).
    #
    # This function is safe for concurrent access.
    def height(self):
        self.lock.acquire()
        height = self._height()
        self.lock.release()
        return height

    # nodeByHeight returns the block node at the specified height.  Nil will be
    # returned if the height does not exist.  This only differs from the exported
    # version in that it is up to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _node_by_height(self, height: int) -> BlockNode:
        if height < 0 or height >= len(self.nodes):
            return None
        return self.nodes[height]

    # NodeByHeight returns the block node at the specified height.  Nil will be
    # returned if the height does not exist.
    #
    # This function is safe for concurrent access.
    def node_by_height(self, height: int) -> BlockNode:
        self.lock.acquire()
        node = self._node_by_height(height)
        self.lock.release()
        return node

    # Equals returns whether or not two chain views are the same.  Uninitialized
    # views (tip set to nil) are considered equal.
    #
    # This function is safe for concurrent access.
    def equals(self, other: 'ChainView'):
        self.lock.acquire()
        other.lock.acquire()
        equals = (len(self.nodes) == len(other.nodes) and self._tip() == other._tip())
        other.lock.release()
        self.lock.release()
        return equals

    # contains returns whether or not the chain view contains the passed block
    # node.  This only differs from the exported version in that it is up to the
    # caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _contains(self, node: BlockNode):
        return self._node_by_height(node.height) == node

    # Contains returns whether or not the chain view contains the passed block
    # node.
    #
    # This function is safe for concurrent access.
    def contains(self, node: BlockNode):
        self.lock.acquire()
        contains = self._contains(node)
        self.lock.release()
        return contains

    # next returns the successor to the provided node for the chain view.  It will
    # return nil if there is no successor or the provided node is not part of the
    # view.  This only differs from the exported version in that it is up to the
    # caller to ensure the lock is held.
    #
    # See the comment on the exported function for more details.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _next(self, node: BlockNode):
        if node is None or not self._contains(node):
            return None

        return self._node_by_height(node.height + 1)

    # Next returns the successor to the provided node for the chain view.  It will
    # return nil if there is no successfor or the provided node is not part of the
    # view.
    #
    # For example, assume a block chain with a side chain as depicted below:
    #   genesis -> 1 -> 2 -> 3 -> 4  -> 5 ->  6  -> 7  -> 8
    #                         \-> 4a -> 5a -> 6a
    #
    # Further, assume the view is for the longer chain depicted above.  That is to
    # say it consists of:
    #   genesis -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
    #
    # Invoking this function with block node 5 would return block node 6 while
    # invoking it with block node 5a would return nil since that node is not part
    # of the view.
    #
    # This function is safe for concurrent access.
    def next(self, node: BlockNode):
        self.lock.acquire()
        next = self._next(node)
        self.lock.release()
        return next

    # findFork returns the final common block between the provided node and the
    # the chain view.  It will return nil if there is no common block.  This only
    # differs from the exported version in that it is up to the caller to ensure
    # the lock is held.
    #
    # See the exported FindFork comments for more details.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _find_fork(self, node: BlockNode) -> BlockNode:
        # No fork point for node that doesn't exist.
        if node is None:
            return None

        # When the height of the passed node is higher than the height of the
        # tip of the current chain view, walk backwards through the nodes of
        # the other chain until the heights match (or there or no more nodes in
        # which case there is no common node between the two).
        #
        # NOTE: This isn't strictly necessary as the following section will
        # find the node as well, however, it is more efficient to avoid the
        # contains check since it is already known that the common node can't
        # possibly be past the end of the current chain view.  It also allows
        # this code to take advantage of any potential future optimizations to
        # the Ancestor function such as using an O(log n) skip list.
        chain_height = self._height()
        if node.height > chain_height:
            node = node.ancestor(chain_height)

        # Walk the other chain backwards as long as the current one does not
        # contain the node or there are no more nodes in which case there is no
        # common node between the two.
        while node is not None and not self._contains(node):
            node = node.parent

        return node

    # FindFork returns the final common block between the provided node and the
    # the chain view.  It will return nil if there is no common block.
    #
    # For example, assume a block chain with a side chain as depicted below:
    #   genesis -> 1 -> 2 -> ... -> 5 -> 6  -> 7  -> 8
    #                                \-> 6a -> 7a
    #
    # Further, assume the view is for the longer chain depicted above.  That is to
    # say it consists of:
    #   genesis -> 1 -> 2 -> ... -> 5 -> 6 -> 7 -> 8.
    #
    # Invoking this function with block node 7a would return block node 5 while
    # invoking it with block node 7 would return itself since it is already part of
    # the branch formed by the view.
    #
    # This function is safe for concurrent access.
    def find_fork(self, node: BlockNode) -> BlockNode:
        self.lock.acquire()
        fork = self._find_fork(node)
        self.lock.release()
        return fork

    # blockLocator returns a block locator for the passed block node.  The passed
    # node can be nil in which case the block locator for the current tip
    # associated with the view will be returned.  This only differs from the
    # exported version in that it is up to the caller to ensure the lock is held.
    #
    # See the exported BlockLocator function comments for more details.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _block_locator(self, node: BlockNode) -> BlockLocator:
        # Use the current tip if requested.
        if node is None:
            node = self._tip()

        if node is None:
            return None

        locator = BlockLocator()
        step = 1
        while node is not None:
            locator.append(node.hash)

            #  Nothing more to add once the genesis block has been added.
            if node.height == 0:
                break

            # Calculate height of previous node to include ensuring the
            # final node is the genesis block.
            height = node.height - step
            if height < 0:
                height = 0

            # When the node is in the current chain view, all of its
            # ancestors must be too, so use a much faster O(1) lookup in
            # that case.  Otherwise, fall back to walking backwards through
            # the nodes of the other chain to the correct ancestor.
            if self._contains(node):
                node = self.nodes[height]
            else:
                node = node.ancestor(height)

            # Once 11 entries have been included, start doubling the
            # distance between included hashes.
            if len(locator) > 10:
                step *= 2
        return locator

    # BlockLocator returns a block locator for the passed block node.  The passed
    # node can be nil in which case the block locator for the current tip
    # associated with the view will be returned.
    #
    # See the BlockLocator type for details on the algorithm used to create a block
    # locator.
    #
    # This function is safe for concurrent access.
    def block_locator(self, node: BlockNode) -> BlockLocator:
        self.lock.acquire()
        locator = self._block_locator(node)
        self.lock.release()
        return locator
