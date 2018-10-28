from .common import *
import random
import pyutil

seed = 0
random_fn = random.Random(seed)


def get_random_int():
    return random_fn.randrange(pyutil.MaxInt64)


def clone_treap_node(node):
    return TreapNode(
        key=node.key,
        value=node.value,
        priority=node.priority,
        left=node.left,
        right=node.right,
    )


# You can refer to https://blog.csdn.net/yang_yulei/article/details/46005845 for treap
class Immutable:
    def __init__(self, root=None, count=None, total_size=None):
        self.root = root
        self.count = count or 0

        # totalSize is the best estimate of the total size of of all data in
        # the treap including the keys, values, and node sizes.
        self.total_size = total_size or 0

    def len(self):
        return self.count

    def size(self):
        return self.total_size

    @staticmethod
    def _key_compare(key1, key2):

        if key1 > key2:
            return 1
        elif key1 == key2:
            return 0
        else:
            return -1

    def _locator_key(self, key):
        """Like the _get, but return node and it's parent stack """

        node = self.root
        parent = None
        parent_stack = ParentStack()
        while node is not None:
            # copy the node following the find path
            node_copy = clone_treap_node(node)

            # change the parent point to new copy
            if parent is not None:
                if parent.left == node:
                    parent.left = node_copy
                else:
                    parent.right = node_copy

            result = self._key_compare(key, node.key)
            if result > 0:
                parent = node_copy
                parent_stack.append(parent)
                node = node.right
            elif result < 0:
                parent = node_copy
                parent_stack.append(parent)
                node = node.left
            else:
                return node_copy, parent, parent_stack
        return None, parent, parent_stack

    def get(self, key: bytes):
        node, _, _ = self._locator_key(key)
        if node is not None:
            return node.value
        else:
            return None

    def has(self, key: bytes):
        node, _, _ = self._locator_key(key)
        return node is not None

    @staticmethod
    def _check_priority_and_rotate_return_root(node, parent_stack):

        new_root = parent_stack.at(len(parent_stack) - 1)
        while len(parent_stack) > 0:
            parent = parent_stack.pop()

            # If one node (and it's ancestors) satisfy heap rule, don't rotate
            if node.priority >= parent.priority:
                break
            # node is on left branch of parent, do right rotation
            if parent.left == node:
                parent.left = node.right
                node.right = parent
            else:
                # on right branch, do left rotation
                parent.right = node.left
                node.left = parent

            # Relink grandparent
            grandparent = parent_stack.at(0)
            if grandparent is None:
                new_root = node
            elif grandparent.left == parent:
                grandparent.left = node
            else:
                grandparent.right = node
        return new_root

    def _attach_node_to_parent(self, node, parent):
        result = self._key_compare(node.key, parent.key)
        if result > 0:
            parent.right = node
        else:
            parent.left = node
        return

    def put(self, key: bytes, value: bytes or None):
        # If put None, we set valye to empty bytes
        if value is None:
            value = bytes()

        # Make new node if it is a empty treap
        # Then make the new Immutable and return
        if self.root is None:
            node = TreapNode(key, value, get_random_int())
            return Immutable(root=node, count=1, total_size=node.node_size())

        # locator the key
        node, parent, parent_stack = self._locator_key(key)

        # We put the key that already exsits
        if node is not None:
            if parent is None:
                new_root = node
            else:
                new_root = parent

            new_total_size = self.total_size - len(node.value) + len(value)
            node.value = value
            return Immutable(root=new_root, count=self.count, total_size=new_total_size)

        # Make a new node
        node = TreapNode(key, value, get_random_int())
        new_count = self.count + 1
        new_total_size = self.total_size + node.node_size()

        # attach to it's parent
        self._attach_node_to_parent(node, parent)

        # rotate node and it's parent if they don't satisfy heap rule
        new_root = self._check_priority_and_rotate_return_root(node, parent_stack)

        return Immutable(root=new_root, count=new_count, total_size=new_total_size)

    def delete(self, key):

        # locator the key
        node, parent, parent_stack = self._locator_key(key)

        # when treap don't has key
        if node is None:
            return

        # when treap only has single node
        if parent is None and node.left is None and node.right is None:
            return Immutable(root=None, count=0, total_size=0)

        # rotate to make node become leaf
        # loop while node has child
        new_root = parent_stack.at(len(parent_stack) - 1)
        while node.left is not None or node.right is not None:
            # choose child with higher priority
            if node.left is None:
                child = node.right
                is_left = False
            elif node.right is None:
                child = node.left
                is_left = True
            elif node.left.priority >= node.right.priority:
                child = node.left
                is_left = True
            else:
                child = node.right
                is_left = False

            child = clone_treap_node(child)

            if is_left:
                # child on left branch, do right rotation
                node.left = child.right
                child.right = node
            else:
                # child on left branch, do right rotation
                node.right = child.left
                child.left = node

            if parent is None:
                new_root = child
            elif parent.left == node:
                parent.left = child
            else:
                parent.right = child

            parent = child

        # pop node from it's parent
        if parent.right == node:
            parent.right = None
        else:
            parent.left = None

        # do count stuff
        new_count = self.count - 1
        new_total_size = self.total_size - node.node_size()
        return Immutable(root=new_root, count=new_count, total_size=new_total_size)

    # TOCHANGE very golang style
    # But now, make the inteface same. After I understand fully, change it better
    def for_each(self, fn):
        """
        fn is function takes two params
        :param fn:
        :return:
        """
        # loop the
        node = self.root
        parent_stack = ParentStack()

        while node is not None:
            parent_stack.append(node)
            node = node.left

        while len(parent_stack) > 0:
            node = parent_stack.pop()

            if not fn(node.key, node.value):
                return

            node = node.right
            while node is not None:
                parent_stack.append(node)
                node = node.left

        return

    def for_each2(self):
        node = self.root
        parent_stack = ParentStack()

        while node is not None:
            parent_stack.append(node)
            node = node.left

        while len(parent_stack) > 0:
            node = parent_stack.pop()

            yield node.key, node.value

            node = node.right
            while node is not None:
                parent_stack.append(node)
                node = node.left

        return
