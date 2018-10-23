class ChainView:
    def __init__(self, lock, nodes):
        """

        :param Lock lock:
        :param []*blockNode nodes:
        """
        self.lock = lock
        self.nodes = nodes

    # genesis returns the genesis block for the chain view.  This only differs from
    # the exported version in that it is up to the caller to ensure the lock is
    # held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _genesis(self):
        pass

    # Genesis returns the genesis block for the chain view.
    #
    # This function is safe for concurrent access.
    def genesis(self):
        pass

    # tip returns the current tip block node for the chain view.  It will return
    # nil if there is no tip.  This only differs from the exported version in that
    # it is up to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _tip(self):
        pass

    # Tip returns the current tip block node for the chain view.  It will return
    # nil if there is no tip.
    #
    # This function is safe for concurrent access.
    def tip(self):
        pass

    # setTip sets the chain view to use the provided block node as the current tip
    # and ensures the view is consistent by populating it with the nodes obtained
    # by walking backwards all the way to genesis block as necessary.  Further
    # calls will only perform the minimum work needed, so switching between chain
    # tips is efficient.  This only differs from the exported version in that it is
    # up to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for writes).
    def _set_tip(self):
        pass

    # SetTip sets the chain view to use the provided block node as the current tip
    # and ensures the view is consistent by populating it with the nodes obtained
    # by walking backwards all the way to genesis block as necessary.  Further
    # calls will only perform the minimum work needed, so switching between chain
    # tips is efficient.
    #
    # This function is safe for concurrent access.
    def set_tip(self):
        pass

    # height returns the height of the tip of the chain view.  It will return -1 if
    # there is no tip (which only happens if the chain view has not been
    # initialized).  This only differs from the exported version in that it is up
    # to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _height(self):
        pass

    # Height returns the height of the tip of the chain view.  It will return -1 if
    # there is no tip (which only happens if the chain view has not been
    # initialized).
    #
    # This function is safe for concurrent access.
    def height(self):
        pass

    # nodeByHeight returns the block node at the specified height.  Nil will be
    # returned if the height does not exist.  This only differs from the exported
    # version in that it is up to the caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _node_by_height(self):
        pass

    # NodeByHeight returns the block node at the specified height.  Nil will be
    # returned if the height does not exist.
    #
    # This function is safe for concurrent access.
    def node_by_height(self):
        pass

    # Equals returns whether or not two chain views are the same.  Uninitialized
    # views (tip set to nil) are considered equal.
    #
    # This function is safe for concurrent access.
    def equals(self, other):
        pass

    # contains returns whether or not the chain view contains the passed block
    # node.  This only differs from the exported version in that it is up to the
    # caller to ensure the lock is held.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _contains(self, node):
        pass

    # Contains returns whether or not the chain view contains the passed block
    # node.
    #
    # This function is safe for concurrent access.
    def contains(self, node):
        pass

    # next returns the successor to the provided node for the chain view.  It will
    # return nil if there is no successor or the provided node is not part of the
    # view.  This only differs from the exported version in that it is up to the
    # caller to ensure the lock is held.
    #
    # See the comment on the exported function for more details.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _next(self):
        pass

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
    def next(self):
        pass

    # findFork returns the final common block between the provided node and the
    # the chain view.  It will return nil if there is no common block.  This only
    # differs from the exported version in that it is up to the caller to ensure
    # the lock is held.
    #
    # See the exported FindFork comments for more details.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _find_fork(self, node):
        pass

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
    def find_fork(self, node):
        pass

    # blockLocator returns a block locator for the passed block node.  The passed
    # node can be nil in which case the block locator for the current tip
    # associated with the view will be returned.  This only differs from the
    # exported version in that it is up to the caller to ensure the lock is held.
    #
    # See the exported BlockLocator function comments for more details.
    #
    # This function MUST be called with the view mutex locked (for reads).
    def _block_locator(self, node):
        pass

    # BlockLocator returns a block locator for the passed block node.  The passed
    # node can be nil in which case the block locator for the current tip
    # associated with the view will be returned.
    #
    # See the BlockLocator type for details on the algorithm used to create a block
    # locator.
    #
    # This function is safe for concurrent access.
    def block_locator(self, node):
        pass
