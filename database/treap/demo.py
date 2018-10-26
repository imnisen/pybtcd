"""
Treap Implementation in Python

Attempts to keep a binary tree balanced by maintaining a priority
heap using randomly generated values.

Includes full-coverage and stress tests.

> coverage run treap.py
100% |########################################################################|
100% |########################################################################|
100% |########################################################################|
..
----------------------------------------------------------------------
Ran 2 tests in 11.329s

OK

> coverage report -m
Name    Stmts   Miss  Cover   Missing
-------------------------------------
treap     191      0   100%
"""

import os
import sys
import doctest
import unittest
from random import Random


class _TreapNode:
    """Treap Node"""

    def __init__(self, key, value, heap_id,
                 parent=None, left=None, right=None):
        self.key = key
        self.value = value
        self.heap_id = heap_id
        self.parent = parent
        self.left = left
        self.right = right

    def __repr__(self):
        return str((self.key, self.value, self.heap_id))


class Treap:
    """
    Treap

    Dictionary-like object with sorted keys.

    >>> treap = Treap()
    >>> treap['a'] = 1
    >>> treap['a']
    1
    >>> treap['b'] = 2
    >>> 'b' in treap
    True
    >>> del treap['b']
    >>> 'b' in treap
    False
    """

    def __init__(self, seed=0, max_heap_id=sys.maxint):
        self.random = Random(seed)
        self.max_heap_id = max_heap_id
        self.root = None

    def __setitem__(self, key, value):
        """Set a key, value pair in the tree."""
        node, parent = self._find_node(key, self.root)
        if node is None:
            heap_id = self.random.randrange(self.max_heap_id)
            node = _TreapNode(key, value, heap_id)
            if parent is None:
                self.root = node
            elif node.key < parent.key:
                parent.left = node
            else:
                parent.right = node
            node.parent = parent
            self._prioritize(node)
        else:
            node.value = value

    def _find_node(self, key, node, parent=None):
        while True:
            if node is None or key == node.key:
                return node, parent
            elif key < node.key:
                node, parent = node.left, node
            else:
                node, parent = node.right, node

    def _pivot_up(self, node):
        parent = node.parent
        if parent is None: return

        if parent.left == node:
            """
            Given the following binary search tree:
                   5
                  / \
                 3   C
                / \
               A   B
            Imagine we need to pivot 3 and 5 (to maintain the heap
            property). The resulting tree will look like:
                   3
                  / \
                 A   5
                    / \
                   B   C
            """
            node.right, parent.left = parent, node.right
            if parent.left: parent.left.parent = parent
        else:
            node.left, parent.right = parent, node.left
            if parent.right: parent.right.parent = parent

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
        while node.parent and node.parent.heap_id < node.heap_id:
            self._pivot_up(node)

    def __contains__(self, key):
        """Return True iff key is found in tree, else False."""
        node = self._find_node(key, self.root)[0]
        return node is not None

    def __getitem__(self, key):
        """Return the value corresponding to key in the tree."""
        node = self._find_node(key, self.root)[0]
        if node is None:
            raise KeyError(key)
        else:
            return node.value

    def __delitem__(self, key):
        """Delete a key, value pair identified by key from the tree."""
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

    def min(self):
        """Return the (key, value) pair with minimum key."""
        if self.root is None: return None
        node, parent = self._traverse(self.root, 'left')
        return node.key, node.value

    def max(self):
        """Return the (key, value) pair with maximum key."""
        if self.root is None: return None
        node, parent = self._traverse(self.root, 'right')
        return node.key, node.value

    def clear(self):
        """Clear all the (key, value) pairs from the tree."""
        self.root = None

    def _traverse(self, node, attr, parent=None):
        while getattr(node, attr):
            node, parent = getattr(node, attr), node
        return node, parent

    def check(self):
        """Check treap invariants."""
        nodes = [(self.root, -sys.maxint, sys.maxint)]
        while nodes:
            node, min_bound, max_bound = nodes.pop()
            if node:
                assert min_bound < node.key < max_bound
                if node.left: assert node.key > node.left.key
                if node.right: assert node.key < node.right.key
                if node.parent:
                    parent = node.parent
                    assert node.heap_id < parent.heap_id
                    assert parent.left == node or parent.right == node
                nodes.append((node.left, min_bound, node.key))
                nodes.append((node.right, node.key, max_bound))

    def __repr__(self):
        """Return a string representation of treap."""
        lines = []
        nodes = [(self.root, 0)]
        while nodes:
            node, indent = nodes.pop()
            name = str(node) if node else 'None'
            lines.append(' ' * indent + name)
            if node:
                nodes.append((node.right, indent + 1))
                nodes.append((node.left, indent + 1))
        return os.linesep.join(lines)


class TestTreap(unittest.TestCase):
    def setUp(self):
        self.treap = Treap()

    def test_tree(self):
        treap = self.treap
        treap[1] = 'a'
        treap[2] = 'b'
        treap[0] = 'c'
        self.assertEqual(repr(treap), repr(treap))

        self.assertEqual(treap[1], 'a')
        treap[1] = 'b'
        self.assertEqual(treap[1], 'b')
        self.assertRaises(KeyError, treap.__getitem__, 3)

        self.assertTrue(1 in treap)
        self.assertFalse(3 in treap)

        del treap[1]
        del treap[2]
        treap[1] = 'a'
        del treap[0]
        del treap[1]
        self.assertRaises(KeyError, treap.__delitem__, 1)

        treap[5] = 'a'
        treap[3] = 'b'
        treap[1] = 'c'
        treap[2] = 'd'
        treap[4] = 'e'
        treap[9] = 'f'
        treap[7] = 'g'
        treap[6] = 'h'
        treap[8] = 'i'
        self.assertEqual(treap.min(), (1, 'c'))
        self.assertEqual(treap.max(), (9, 'f'))
        treap.check()
        del treap[3]
        del treap[9]
        del treap[5]
        del treap[2]
        treap.clear()
        self.assertEqual(treap.min(), None)
        self.assertEqual(treap.max(), None)

    def test_stress(self):
        try:
            from progressbar import ProgressBar
        except ImportError:
            ProgressBar = lambda: iter
        from random import Random

        random = Random(0)
        treap = self.treap
        treap.clear()
        keys = range(1000)

        random.shuffle(keys)
        progress = ProgressBar()
        for key in progress(keys):
            treap[key] = -1
            treap.check()

        random.shuffle(keys)
        progress = ProgressBar()
        for key in progress(keys):
            assert key in treap

        random.shuffle(keys)
        progress = ProgressBar()
        for key in progress(keys):
            del treap[key]
            assert key not in treap
            treap.check()


if __name__ == '__main__':
    doctest.testmod()
    unittest.main()

"""
Copyright (c) 2013 Grant Jenks

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""