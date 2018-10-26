from .common import *
import random
import pyutil

class Mutable:
    def __init__(self, root=None, count=None, total_size=None, seed=None, max_priority=None):
        self.root = root
        self.count = count or 0
        self.total_size = total_size or 0
        self.seed = seed or 0
        self.random = random.Random(seed)
        self.max_priority = max_priority or pyutil.MaxInt64


    # Len returns the number of items stored in the treap.
    def len(self):
        return self.count

        # Size returns a best estimate of the total number of bytes the treap is

    # consuming including all of the fields used to represent the nodes as well as
    # the size of the keys and values.  Shared values are not detected, so the
    # returned size assumes each value is pointing to different memory.
    def size(self):
        return self.total_size

    # _find_node returns the treap node that contains the passed key and its parent.  When
    # the found node is the root of the tree, the parent will be nil.  When the key
    # does not exist, both the node and the parent will be nil.
    def _find_node(self, key, node=None, parent=None):
        if node is None:
            node = self.root

        while True:
            if node is None or key == node.key:
                return node, parent
            elif key < node.key:
                parent = node
                node = node.left
            else:
                parent = node
                node = node.right


    # get returns the treap node that contains the passed key and its parent.  When
    # the found node is the root of the tree, the parent will be nil.  When the key
    # does not exist, both the node and the parent will be nil.
    def get(self, key: bytes):
        node, _ = self._find_node(key)
        if node is None:
            return None
        else:
            return node.value

    # Has returns whether or not the passed key exists.
    def has(self, key:bytes):
        node, _ = self._find_node(key)
        return node is not None


    def _pivot_up(self,node):
        parent = node.parent
        if parent is None:
            return

        if parent.left == node: # right rotation
            node.right, parent.left = parent, node.right
            if parent.left:
                parent.left.parent = parent
        else:
            node.left, parent.right = parent, node.left
            if parent.right:
                parent.right.parent = parent

        grandparent = parent.parent
        node.parent, parent.parent = grandparent, node
        if grandparent:
            if grandparent.left == parent:
                grandparent.left = node
            else:
                grandparent.right = node
        else:
            self.root = node


    def _prioritize(self, node):
        while node.parent and node.parent.priority < node.priority:
            self._pivot_up(node)
    def node_size(self, node):
        pass

    # Put inserts the passed key/value pair.
    def put(self, key: bytes, value: bytes):
        # Use an empty byte slice for the value when none was provided.  This
        # ultimately allows key existence to be determined from the value since
        # an empty byte slice is distinguishable from nil.

        node, parent = self._find_node(key)
        if node is None:
            # Add new node
            node = TreapNode(key=key, value=value,
                             priority=self.random.randrange(self.max_priority))

            # update counter
            self.count += 1
            self.total_size += self.node_size(node)

            # Add new node to parent's left or right size
            if parent is None:
                self.root = node
            elif node.key < parent.key:
                parent.left = node
            else:
                parent.right = node
            node.parent = parent

            self._prioritize(node)
        else:
            # The key already exists, so update its value.
            self.total_size -= len(node.value)
            self.total_size += len(value)
            node.value = value


    def delete(self, key):

        node, parent = self._find_node(key, self.root)

        if node is None:
            raise KeyError(key)
        elif parent is None and not (node.left and node.right):
            self.root = node.left or node.right
            if self.root: self.root.parent = None
        else:
            while node.left and node.right:
                # Pivot a child node up while the node to be deleted has
                # both left and right children.
                if node.left.heap_id > node.right.heap_id:
                    self._pivot_up(node.left)
                else:
                    self._pivot_up(node.right)

            child = node.left or node.right
            if node.parent.left == node:
                node.parent.left = child
                if child: child.parent = node.parent
            else:
                node.parent.right = child
                if child: child.parent = node.parent

        node.parent = None
        node.left = None
        node.right = None









        
