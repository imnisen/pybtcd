import database
import chainhash
from .error import NormalError
from .chainio import *
from .utxo_viewpoint import *

import logging

logger = logging.getLogger(__name__)

# blockHdrOffset defines the offsets into a v1 block index row for the
# block header.
#
# The serialized block index row format is:
#   <blocklocation><blockheader>
blockHdrOffset = 12


class BlockChainContext:
    def __init__(self, parent: chainhash.Hash = None, children: [chainhash.Hash] = None, height: int = None,
                 main_chain: bool = None):
        """

        :param chainhash.Hash parent:
        :param [chainhash.Hash] children:
        :param int height:
        :param bool main_chain:
        """
        self.parent = parent
        self.children = children or []
        self.height = height or -1
        self.main_chain = main_chain or False


# migrateBlockIndex migrates all block entries from the v1 block index bucket
# to the v2 bucket. The v1 bucket stores all block entries keyed by block hash,
# whereas the v2 bucket stores the exact same values, but keyed instead by
# block height + hash.
def migrate_block_index(db: database.DB):
    # Hardcoded bucket names so updates to the global values do not affect
    # old upgrades.
    v1_bucket_name = b"ffldb-blockidx"
    v2_bucket_name = b"blockheaderidx"

    def fn(db_tx: database.Tx):
        v1_block_idx_bucket = db_tx.metadata().bucket(v1_bucket_name)
        if v1_block_idx_bucket is None:
            raise NormalError("Bucket %s does not exist" % v1_bucket_name)

        logger.info("Re-indexing block information in the database. This might take a while...")

        v2_block_idx_bucket = db_tx.metadata().bucket(v2_bucket_name)

        # Get tip of the main chain.
        serialized_data = db_tx.metadata().get(chainStateKeyName)
        state = deserialize_best_chain_state(serialized_data)

        tip = state.hash

        # Scan the old block index bucket and construct a mapping of each block
        # to parent block and all child blocks.
        blocks_map = read_block_tree(v1_block_idx_bucket)

        # Use the block graph to calculate the height of each block.
        determine_block_heights(blocks_map)

        # Find blocks on the main chain with the block graph and current tip.
        determine_main_chain_blocks(blocks_map, tip)

        # Now that we have heights for all blocks, scan the old block index
        # bucket and insert all rows into the new one.
        for hash_bytes, block_row in v1_block_idx_bucket.for_each2():

            hash = chainhash.Hash(hash_bytes[:chainhash.HashSize])
            chain_context = blocks_map.get(hash)

            if chain_context.height == -1:
                raise NormalError("Unable to calculate chain height for stored block %s" % hash)

            # Mark blocks as valid if they are part of the main chain.
            status = BlockStatus.statusDataStored
            if chain_context.main_chain:
                status |= BlockStatus.statusValid

            # Write header to v2 bucket
            end_offset = blockHdrOffset + blockHdrSize
            header_bytes = block_row[blockHdrOffset: end_offset]

            value = header_bytes + status.to_bytes()
            key = block_index_key(hash, chain_context.height)
            v2_block_idx_bucket.put(key, value)

            # Delete header from v1 bucket
            truncated_row = block_row[0: blockHdrOffset]
            v1_block_idx_bucket.put(hash_bytes, truncated_row)
            return

    db.update(fn)
    logger.info("Block database migration complete")
    return


# readBlockTree reads the old block index bucket and constructs a mapping of
# each block to its parent block and all child blocks. This mapping represents
# the full tree of blocks. This function does not populate the height or
# mainChain fields of the returned blockChainContext values.
def read_block_tree(v1_block_idx_bucket: database.Bucket) -> dict:
    blocks_map = {}
    for _, block_row in v1_block_idx_bucket.for_each2():
        end_offset = blockHdrOffset + blockHdrSize
        header_bytes = block_row[blockHdrOffset: end_offset]

        header = wire.BlockHeader()
        header.deserialize(io.BytesIO(header_bytes))

        block_hash = header.block_hash()
        prev_hash = header.prev_block

        if block_hash not in blocks_map:
            blocks_map[block_hash] = BlockChainContext()

        if prev_hash not in blocks_map:
            blocks_map[prev_hash] = BlockChainContext()

        blocks_map[block_hash].parent = prev_hash
        blocks_map[prev_hash].children.append(block_hash)

    return blocks_map


# determineBlockHeights takes a map of block hashes to a slice of child hashes
# and uses it to compute the height for each block. The function assigns a
# height of 0 to the genesis hash and explores the tree of blocks
# breadth-first, assigning a height to every block with a path back to the
# genesis block. This function modifies the height field on the blocksMap
# entries.
def determine_block_heights(blocks_map: dict):
    queue = []

    # The genesis block is included in blocksMap as a child of the zero hash
    # because that is the value of the PrevBlock field in the genesis header.
    pre_genesis_context = blocks_map.get(zeroHash, None)
    if pre_genesis_context is None or len(pre_genesis_context.children) == 0:
        raise NormalError("Unable to find genesis block")

    for genesis_hash in pre_genesis_context.children:
        blocks_map[genesis_hash].height = 0
        queue.append(genesis_hash)

    while len(queue) > 0:
        element = queue.pop(0)
        hash = element
        height = blocks_map[hash].height

        # For each block with this one as a parent, assign it a height and
        # push to queue for future processing.
        for child_hash in blocks_map[hash].children:
            blocks_map[chainhash].height = height + 1
            queue.append(child_hash)

    return


# determineMainChainBlocks traverses the block graph down from the tip to
# determine which block hashes that are part of the main chain. This function
# modifies the mainChain field on the blocksMap entries.
def determine_main_chain_blocks(blocks_map: dict, tip: chainhash.Hash):
    next_hash = tip
    while next_hash != zeroHash:
        blocks_map[next_hash].main_chain = True

        next_hash = blocks_map[next_hash].parent
    return
