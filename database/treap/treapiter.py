from .common import *


class Iterator:
    def __init__(self, t=None, root=None, node=None, parent_stack=None, is_new=None, seek_key=None, start_key=None,
                 limit_key=None):
        """

        :param *Mutable    t:
        :param *treapNode  root:
        :param *treapNode  node:
        :param parentStack parent_stack:
        :param bool        is_new:
        :param []byte      seek_key:
        :param []byte      start_key:
        :param []byte      limit_key:
        """

        # Mutable treap iterator is associated with or nil
        self.t = t

        # Root node of treap iterator is associated with
        self.root = root or None

        # The node the iterator is positioned at
        self.node = node or None

        # The stack of parents needed to iterate
        self.parent_stack = parent_stack or ParentStack()

        # Whether the iterator has been positioned
        self.is_new = is_new or False

        # Used to handle dynamic updates for mutable treap
        self.seek_key = seek_key or None

        # Used to limit the iterator to a range
        self.start_key = start_key or None

        # Used to limit the iterator to a range
        self.limit_key = limit_key or None

    def limit_iterator(self):
        if self.node is None:
            return False

        node = self.node
        if self.start_key is not None and node.key < self.start_key:
            self.node = None
            return False

        if self.limit_key is not None and node.key >= self.limit_key:
            self.node = None
            return False

        return True

    # TOCHECK this function's design is strange
    # seek moves the iterator based on the provided key and flags.
    #
    # When the exact match flag is set, the iterator will either be moved to first
    # key in the treap that exactly matches the provided key, or the one
    # before/after it depending on the greater flag.
    #
    # When the exact match flag is NOT set, the iterator will be moved to the first
    # key in the treap before/after the provided key depending on the greater flag.
    #
    # In all cases, the limits specified when the iterator was created are
    # respected.
    def _seek(self, key, exact_match: bool, greater: bool) -> bool:
        self.node = None
        self.parent_stack = ParentStack()
        selected_node_depth = 0

        node = self.root
        while node is not None:
            self.parent_stack.append(node)

            # When we meet a node that is greater than we seek,
            if node.key > key:
                # mark the greater node , also it's depth in parent stack
                if greater:
                    self.node = node
                    selected_node_depth = len(self.parent_stack) - 1

                node = node.left

            # When we meet a node that is smaller than we seek
            elif node.key < key:
                # mark the smaller node, also it's depth in parent stack
                if not greater:
                    self.node = node
                    selected_node_depth = len(self.parent_stack) - 1
                node = node.right

            # when we meet a node that is equal to we seek
            else:
                # If we need exact math, mark the node found.
                if exact_match:
                    self.node = node
                    self.parent_stack.pop()
                    return self.limit_iterator()
                else:
                    # If we need a greater one
                    if greater:
                        node = node.right
                    else:
                        node = node.left

        i = len(self.parent_stack)
        while i > selected_node_depth:
            self.parent_stack.pop()
            i -= 1
        return self.limit_iterator()

    # First moves the iterator to the first key/value pair.  When there is only a
    # single key/value pair both First and Last will point to the same pair.
    # Returns false if there are no key/value pairs.
    def first(self) -> bool:

        # Seek the start key if the iterator was created with one.  This will
        # result in either an exact match, the first greater key, or an
        # exhausted iterator if no such key exists.
        self.is_new = False
        if self.start_key is not None:
            return self._seek(self.start_key, exact_match=True, greater=True)

        # The smallest key is in the left-most node.
        self.parent_stack = ParentStack()
        node = self.root
        while node is not None:
            if node.left is None:
                self.node = node
                return True
            self.parent_stack.append(node)
            node = node.left

        return False

    # Last moves the iterator to the last key/value pair.  When there is only a
    # single key/value pair both First and Last will point to the same pair.
    # Returns false if there are no key/value pairs.
    def last(self):
        self.is_new = False
        if self.limit_key is not None:
            return self._seek(self.limit_key, exact_match=False, greater=False)

        # The smallest key is in the left-most node.
        self.parent_stack = ParentStack()
        node = self.root
        while node is not None:
            if node.right is None:
                self.node = node
                return True
            self.parent_stack.append(node)
            node = node.right

        return False

    # Next moves the iterator to the next key/value pair and returns false when the
    # iterator is exhausted.  When invoked on a newly created iterator it will
    # position the iterator at the first item.
    def next(self) -> bool:
        if self.is_new:
            return self.first()

        if self.node is None:
            return False

        # Reseek the previous key without allowing for an exact match if a
        # force seek was requested.  This results in the key greater than the
        # previous one or an exhausted iterator if there is no such key.
        seek_key = self.seek_key
        if seek_key is not None:
            self.seek_key = None
            return self._seek(seek_key, exact_match=False, greater=True)

        if self.node.right is None:
            parent = self.parent_stack.pop()
            while parent is not None and parent.right == self.node:
                self.node = parent
                parent = self.parent_stack.pop()
            self.node = parent
            return self.limit_iterator()

        self.parent_stack.append(self.node)
        self.node = self.node.right
        node = self.node.left
        while node is not None:
            self.parent_stack.append(self.node)
            self.node = node
            node = node.left
        return self.limit_iterator()

    # Prev moves the iterator to the previous key/value pair and returns false when
    # the iterator is exhausted.  When invoked on a newly created iterator it will
    # position the iterator at the last item.
    def prev(self) -> bool:
        if self.is_new:
            return self.last()

        if self.node is None:
            return False

        # Reseek the previous key without allowing for an exact match if a
        # force seek was requested.  This results in the key smaller than the
        # previous one or an exhausted iterator if there is no such key.
        seek_key = self.seek_key
        if seek_key is not None:
            self.seek_key = None
            return self._seek(seek_key, exact_match=False, greater=False)

        if self.node.left is None:
            parent = self.parent_stack.pop()
            while parent is not None and parent.left == self.node:
                self.node = parent
                parent = self.parent_stack.pop()
            self.node = parent
            return self.limit_iterator()

        # There is a left node, so the previous node is the right-most node
        # down the left sub-tree.
        self.parent_stack.append(self.node)
        self.node = self.node.left
        node = self.node.right
        while node is not None:
            self.parent_stack.append(self.node)
            self.node = node
            node = node.right
        return self.limit_iterator()

    def seek(self, key):
        self.is_new = False
        return self._seek(key, exact_match=True, greater=True)

    def key(self):
        if self.node is None:
            return None
        return self.node.key

    def value(self):
        if self.node is None:
            return None
        return self.node.value

    def valid(self):
        return self.node is not None

    # ForceReseek notifies the iterator that the underlying mutable treap has been
    # updated, so the next call to Prev or Next needs to reseek in order to allow
    # the iterator to continue working properly.
    #
    # NOTE: Calling this function when the iterator is associated with an immutable
    # treap has no effect as you would expect.
    def force_reseek(self):
        if self.t is None:
            return

        self.root = self.t.root

        if self.node is None:
            self.seek_key = None
            return

        self.seek_key = self.node.key
        return
