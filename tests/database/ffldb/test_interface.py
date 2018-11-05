import unittest
import wire
import os

# some constant

# blockDataNet is the expected network in the test block data.
blockDataNet = wire.BitcoinNet.MainNet

# blockDataFile is the path to a file containing the first 256 blocks
# of the block chain.
blockDataFile = os.path.join("..", "testdata", "blocks1-256.bz2")

# loadBlocks loads the blocks contained in the testdata directory and returns
# a slice of them.