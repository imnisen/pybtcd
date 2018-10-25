import unittest
import random
import pyutil
from blockchain.chain_view import *


# get a random uint32
def testNoncePrng():
    return random.randint(0, pyutil.MaxUint32)


# chainedNodes returns the specified number of nodes constructed such that each
# subsequent node points to the previous one to create a chain.  The first node
# will point to the passed parent which can be nil if desired.
def chained_nodes(parent: BlockNode or None, num_nodes: int) -> list:
    nodes = []
    tip = parent
    for i in range(num_nodes):
        header = wire.BlockHeader(nonce=testNoncePrng())
        if tip is not None:
            header.prev_block = tip.hash

        new_block_node = BlockNode.init_from(header, tip)
        nodes.append(new_block_node)
        tip = new_block_node
    return nodes


# tstTip is a convenience function to grab the tip of a chain of block nodes
# created via chainedNodes.
def tst_tip(nodes):
    return nodes[-1]


# locatorHashes is a convenience function that returns the hashes for all of
# the passed indexes of the provided nodes.  It is used to construct expected
# block locators in the tests.
def locator_hashes(nodes, *indexes):
    hashes = []
    for idx in indexes:
        hashes.append(nodes[idx].hash)
    return hashes


# zipLocators is a convenience function that returns a single block locator
# given a variable number of them and is used in the tests.
def zip_locators(*locators):
    hashes = []
    for locator in locators:
        hashes.extend(locator)
    return hashes


# TestChainView ensures all of the exported functionality of chain views works
# as intended with the exception of some special cases which are handled in
# other tests.
class TestChainView(unittest.TestCase):
    def test_chain_view(self):
        # Construct a synthetic block index consisting of the following
        # structure.
        # 0 -> 1 -> 2  -> 3  -> 4
        #       \-> 2a -> 3a -> 4a  -> 5a -> 6a -> 7a -> ... -> 26a
        #             \-> 3a'-> 4a' -> 5a'
        branch0Nodes = chained_nodes(None, num_nodes=5)
        branch1Nodes = chained_nodes(branch0Nodes[1], num_nodes=25)
        branch2Nodes = chained_nodes(branch1Nodes[0], num_nodes=3)

        tests = [
            # Create a view for branch 0 as the active chain and
            # another view for branch 1 as the side chain.
            {
                "name": "chain0-chain1",
                "view": ChainView.new_from(tst_tip(branch0Nodes)),
                "genesis": branch0Nodes[0],
                "tip": tst_tip(branch0Nodes),
                "side": ChainView.new_from(tst_tip(branch1Nodes)),
                "sideTip": tst_tip(branch1Nodes),
                "fork": branch0Nodes[1],
                "contains": branch0Nodes,
                "noContains": branch1Nodes,
                "equal": ChainView.new_from(tst_tip(branch0Nodes)),
                "unequal": ChainView.new_from(tst_tip(branch1Nodes)),
                "locator": locator_hashes(branch0Nodes, 4, 3, 2, 1, 0),
            },

            # Create a view for branch 1 as the active chain and
            # another view for branch 2 as the side chain.
            {
                "name": "chain1-chain2",
                "view": ChainView.new_from(tst_tip(branch1Nodes)),
                "genesis": branch0Nodes[0],
                "tip": tst_tip(branch1Nodes),
                "side": ChainView.new_from(tst_tip(branch2Nodes)),
                "sideTip": tst_tip(branch2Nodes),
                "fork": branch1Nodes[0],
                "contains": branch1Nodes,
                "noContains": branch2Nodes,
                "equal": ChainView.new_from(tst_tip(branch1Nodes)),
                "unequal": ChainView.new_from(tst_tip(branch2Nodes)),
                "locator": zip_locators(
                    locator_hashes(branch1Nodes, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 11, 7),
                    locator_hashes(branch0Nodes, 1, 0)),
            },

            # Create a view for branch 2 as the active chain and
            # another view for branch 2 as the side chain.
            {
                "name": "chain2-chain0",
                "view": ChainView.new_from(tst_tip(branch2Nodes)),
                "genesis": branch0Nodes[0],
                "tip": tst_tip(branch2Nodes),
                "side": ChainView.new_from(tst_tip(branch0Nodes)),
                "sideTip": tst_tip(branch0Nodes),
                "fork": branch0Nodes[1],
                "contains": branch2Nodes,
                "noContains": branch0Nodes[2:],
                "equal": ChainView.new_from(tst_tip(branch2Nodes)),
                "unequal": ChainView.new_from(tst_tip(branch0Nodes)),
                "locator": zip_locators(
                    locator_hashes(branch2Nodes, 2, 1, 0),
                    locator_hashes(branch1Nodes, 0),
                    locator_hashes(branch0Nodes, 1, 0)),
            },
        ]

        for test in tests:

            self.assertEqual(test['view'].height(), test['tip'].height)
            self.assertEqual(test['side'].height(), test['sideTip'].height)

            self.assertEqual(test['view'].genesis(), test['genesis'])
            self.assertEqual(test['view'].tip(), test['tip'])
            self.assertEqual(test['side'].tip(), test['sideTip'])

            forkNode = test['view'].find_fork(test['side'].tip())
            self.assertEqual(forkNode, test['fork'])

            forkNode = test['side'].find_fork(test['view'].tip())
            self.assertEqual(forkNode, test['fork'])

            forkNode = test['view'].find_fork(test['view'].tip())
            self.assertEqual(forkNode, test['view'].tip())

            for node in test['contains']:
                self.assertTrue(test['view'].contains(node))

            for node in test['noContains']:
                self.assertFalse(test['view'].contains(node))

            self.assertTrue(test['view'].equals(test['equal']))
            self.assertFalse(test['view'].equals(test['unequal']))

            # Ensure all nodes contained in the view return the expected
            # next node.
            for i, node in enumerate(test['contains']):

                next = test['view'].next(node)
                if i < len(test['contains']) - 1:
                    expected = test['contains'][i + 1]
                else:
                    expected = None

                self.assertEqual(next, expected)

            # Ensure nodes that are not contained in the view do not
            # produce a successor node.
            for node in test['noContains']:
                next = test['view'].next(node)
                self.assertIsNone(next)

            # Ensure all nodes contained in the view can be retrieved by
            # height.
            for wantNode in test['contains']:
                node = test['view'].node_by_height(wantNode.height)
                self.assertEqual(node, wantNode)

            # Ensure the block locator for the tip of the active view
            # consists of the expected hashes.
            locator = test['view'].block_locator(test['view'].tip())
            self.assertListEqual(locator, test['locator'])


class TestChainViewForkCorners(unittest.TestCase):
    def test_find_fork(self):
        # Construct two unrelated single branch synthetic block indexes.
        branchNodes = chained_nodes(None, 5)
        unrelatedBranchNodes = chained_nodes(None, 7)

        # Create chain views for the two unrelated histories.
        view1 = ChainView.new_from(tst_tip(branchNodes))
        view2 = ChainView.new_from(tst_tip(unrelatedBranchNodes))

        # Ensure attempting to find a fork point with a node that doesn't exist
        # doesn't produce a node.
        self.assertIsNone(view1.find_fork(None))

        # Ensure attempting to find a fork point in two chain views with
        # totally unrelated histories doesn't produce a node.
        for node in branchNodes:
            self.assertIsNone(view2.find_fork(node))

        for node in unrelatedBranchNodes:
            self.assertIsNone(view1.find_fork(node))


# TestChainViewSetTip ensures changing the tip works as intended including
# capacity changes.
class TestChainViewSetTip(unittest.TestCase):
    def test_set_tip(self):
        # Construct a synthetic block index consisting of the following
        # structure.
        # 0 -> 1 -> 2  -> 3  -> 4
        #       \-> 2a -> 3a -> 4a  -> 5a -> 6a -> 7a -> ... -> 26a
        branch0Nodes = chained_nodes(None, 5)
        branch1Nodes = chained_nodes(branch0Nodes[1], 25)

        tests = [
            # Create an empty view and set the tip to increasingly
            # longer chains.
            {
                "name": "increasing",
                "view": ChainView.new_from(None),
                "tips": [tst_tip(branch0Nodes), tst_tip(branch1Nodes)],
                "contains": [branch0Nodes, branch1Nodes]
            }
        ]

        for test in tests:
            for i, tip in enumerate(test['tips']):
                test['view'].set_tip(tip)
                self.assertEqual(test['view'].tip(), tip)

                for node in test['contains'][i]:
                    self.assertTrue(test['view'].contains(node))


# TestChainViewNil ensures that creating and accessing a nil chain view behaves
# as expected.
class TestChainViewNil(unittest.TestCase):
    def test_chain_view_nil(self):
        view = ChainView.new_from(None)

        # Ensure two unininitialized views are considered equal.
        self.assertTrue(view.equals(ChainView.new_from(None)))

        # Ensure the genesis of an uninitialized view does not produce a node.
        self.assertIsNone(view.genesis())

        # Ensure the tip of an uninitialized view does not produce a node.
        self.assertIsNone(view.tip())

        # Ensure the height of an uninitialized view is the expected value.
        self.assertEqual(view.height(), -1)

        # Ensure attempting to get a node for a height that does not exist does
        # not produce a node.
        self.assertIsNone(view.node_by_height(10))

        # Ensure an uninitialized view does not report it contains nodes.
        fakeNode = chained_nodes(None, 1)[0]
        self.assertFalse(view.contains(fakeNode))

        # Ensure the next node for a node that does not exist does not produce
        # a node.
        self.assertIsNone(view.next(None))

        # Ensure the next node for a node that exists does not produce a node.
        self.assertIsNone(view.next(fakeNode))

        # Ensure attempting to find a fork point with a node that doesn't exist
        # doesn't produce a node.
        self.assertIsNone(view.find_fork(None))

        # Ensure attempting to get a block locator for the tip doesn't produce
        # one since the tip is nil.
        self.assertIsNone(view.block_locator(None))

        # Ensure attempting to get a block locator for a node that exists still
        # works as intended.
        branchNodes = chained_nodes(None, 50)
        wantLocator = locator_hashes(branchNodes, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 36, 32, 24, 8, 0)
        locator = view.block_locator(tst_tip(branchNodes))
        self.assertListEqual(locator, wantLocator)
