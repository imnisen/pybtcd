import chainhash
import time
from .chainio import *
from .best_chain_state import *
from .utxo import *

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


# upgradeUtxoSetToV2 migrates the utxo set entries from version 1 to 2 in
# batches.  It is guaranteed to updated if this returns without failure.
def upgrade_utxo_set_to_v2(db: database.DB, interrupt):
    # Hardcoded bucket names so updates to the global values do not affect
    # old upgrades.
    v1_bucket_name = b"utxoset"
    v2_bucket_name = b"utxosetv2"

    logger.info("Upgrading utxo set to v2.  This will take a while...")
    start = int(time.time())

    # Create the new utxo set bucket as needed.
    def fn1(db_tx: database.Tx):
        db_tx.metadata().create_bucket_if_not_exists(v2_bucket_name)

    db.update(fn1)

    # doBatch contains the primary logic for upgrading the utxo set from
    # version 1 to 2 in batches.  This is done because the utxo set can be
    # huge and thus attempting to migrate in a single database transaction
    # would result in massive memory usage and could potentially crash on
    # many systems due to ulimits.
    #
    # It returns the number of utxos processed.
    max_utxos = 200000

    def do_batch(db_tx: database.Tx) -> int:
        v1_bucket = db_tx.metadata().bucket(v1_bucket_name)
        v2_bucket = db_tx.metadata().bucket(v2_bucket_name)
        v1_cursor = v1_bucket.cursor()

        # Migrate utxos so long as the max number of utxos for this
        # batch has not been exceeded.
        num_utxos = 0
        ok = v1_cursor.first()
        while ok and num_utxos < max_utxos:

            # Old key was the transaction hash.
            old_key = v1_cursor.key()
            tx_hash = chainhash.Hash(old_key)

            # Deserialize the old entry which included all utxos
            # for the given transaction.
            utxos = deserialize_utxo_entry_v0(v1_cursor.value())

            # Add an entry for each utxo into the new bucket using
            # the new format.
            for tx_out_idx, utxo in utxos.items():
                reserialized = serialize_utxo_entry(utxo)

                key = outpoint_key(wire.OutPoint(
                    hash=tx_hash,
                    index=tx_out_idx  # why index set tx_out_idx
                ))

                v2_bucket.put(key, reserialized)

            # Remove old entry
            v1_bucket.delete(old_key)

            num_utxos += len(utxos)

            if interrupt_requested(interrupt):
                # No error here so the database transaction
                # is not cancelled and therefore outstanding
                # work is written to disk.
                break

            ok = v1_cursor.next()

        return num_utxos

    # Migrate all entries in batches for the reasons mentioned above.
    total_utxos = 0
    while True:
        num_utxos = 0

        def fn2(db_tx: database.Tx):
            nonlocal num_utxos
            num_utxos = do_batch(db_tx)
            return

        db.update(fn2)

        if interrupt_requested(interrupt):
            raise InterruptRequestedError

        if num_utxos == 0:
            break

        total_utxos += num_utxos
        logger.info("Migrated %d utxos (%d total" % (num_utxos, total_utxos))

    # Remove the old bucket and update the utxo set version once it has
    # been fully migrated.
    def fn_delete_bucket(db_tx: database.Tx):
        db_tx.metadata().delete_bucket(v1_bucket_name)

        db_put_version(db_tx, utxoSetVersionKeyName, version=2)
        return

    db.update(fn_delete_bucket)

    seconds = int(time.time()) - start
    logger.info("Done upgrading utxo set.  Total utxos: %d in %d seconds" % (total_utxos, seconds))

    return


# deserializeUtxoEntryV0 decodes a utxo entry from the passed serialized byte
# slice according to the legacy version 0 format into a map of utxos keyed by
# the output index within the transaction.  The map is necessary because the
# previous format encoded all unspent outputs for a transaction using a single
# entry, whereas the new format encodes each unspent output individually.
#
# The legacy format is as follows:
#
#   <version><height><header code><unspentness bitmap>[<compressed txouts>,...]
#
#   Field                Type     Size
#   version              VLQ      variable
#   block height         VLQ      variable
#   header code          VLQ      variable
#   unspentness bitmap   []byte   variable
#   compressed txouts
#     compressed amount  VLQ      variable
#     compressed script  []byte   variable
#
# The serialized header code format is:
#   bit 0 - containing transaction is a coinbase
#   bit 1 - output zero is unspent
#   bit 2 - output one is unspent
#   bits 3-x - number of bytes in unspentness bitmap.  When both bits 1 and 2
#     are unset, it encodes N-1 since there must be at least one unspent
#     output.
#
# The rationale for the header code scheme is as follows:
#   - Transactions which only pay to a single output and a change output are
#     extremely common, thus an extra byte for the unspentness bitmap can be
#     avoided for them by encoding those two outputs in the low order bits.
#   - Given it is encoded as a VLQ which can encode values up to 127 with a
#     single byte, that leaves 4 bits to represent the number of bytes in the
#     unspentness bitmap while still only consuming a single byte for the
#     header code.  In other words, an unspentness bitmap with up to 120
#     transaction outputs can be encoded with a single-byte header code.
#     This covers the vast majority of transactions.
#   - Encoding N-1 bytes when both bits 1 and 2 are unset allows an additional
#     8 outpoints to be encoded before causing the header code to require an
#     additional byte.
#
# Example 1:
# From tx in main blockchain:
# Blk 1, 0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098
#
#    010103320496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52
#    <><><><------------------------------------------------------------------>
#     | | \--------\                               |
#     | height     |                      compressed txout 0
#  version    header code
#
#  - version: 1
#  - height: 1
#  - header code: 0x03 (coinbase, output zero unspent, 0 bytes of unspentness)
#  - unspentness: Nothing since it is zero bytes
#  - compressed txout 0:
#    - 0x32: VLQ-encoded compressed amount for 5000000000 (50 BTC)
#    - 0x04: special script type pay-to-pubkey
#    - 0x96...52: x-coordinate of the pubkey
#
# Example 2:
# From tx in main blockchain:
# Blk 113931, 4a16969aa4764dd7507fc1de7f0baa4850a246de90c45e59a3207f9a26b5036f
#
#    0185f90b0a011200e2ccd6ec7c6e2e581349c77e067385fa8236bf8a800900b8025be1b3efc63b0ad48e7f9f10e87544528d58
#    <><----><><><------------------------------------------><-------------------------------------------->
#     |    |  | \-------------------\            |                            |
#  version |  \--------\       unspentness       |                    compressed txout 2
#        height     header code          compressed txout 0
#
#  - version: 1
#  - height: 113931
#  - header code: 0x0a (output zero unspent, 1 byte in unspentness bitmap)
#  - unspentness: [0x01] (bit 0 is set, so output 0+2 = 2 is unspent)
#    NOTE: It's +2 since the first two outputs are encoded in the header code
#  - compressed txout 0:
#    - 0x12: VLQ-encoded compressed amount for 20000000 (0.2 BTC)
#    - 0x00: special script type pay-to-pubkey-hash
#    - 0xe2...8a: pubkey hash
#  - compressed txout 2:
#    - 0x8009: VLQ-encoded compressed amount for 15000000 (0.15 BTC)
#    - 0x00: special script type pay-to-pubkey-hash
#    - 0xb8...58: pubkey hash
#
# Example 3:
# From tx in main blockchain:
# Blk 338156, 1b02d1c8cfef60a189017b9a420c682cf4a0028175f2f563209e4ff61c8c3620
#
#    0193d06c100000108ba5b9e763011dd46a006572d820e448e12d2bbb38640bc718e6
#    <><----><><----><-------------------------------------------------->
#     |    |  |   \-----------------\            |
#  version |  \--------\       unspentness       |
#        height     header code          compressed txout 22
#
#  - version: 1
#  - height: 338156
#  - header code: 0x10 (2+1 = 3 bytes in unspentness bitmap)
#    NOTE: It's +1 since neither bit 1 nor 2 are set, so N-1 is encoded.
#  - unspentness: [0x00 0x00 0x10] (bit 20 is set, so output 20+2 = 22 is unspent)
#    NOTE: It's +2 since the first two outputs are encoded in the header code
#  - compressed txout 22:
#    - 0x8ba5b9e763: VLQ-encoded compressed amount for 366875659 (3.66875659 BTC)
#    - 0x01: special script type pay-to-script-hash
#    - 0x1d...e6: script hash
def deserialize_utxo_entry_v0(serialized: bytes) -> dict:
    offset = 0

    # Deserialize the version.
    #
    # NOTE: Ignore version since it is no longer used in the new format.
    _, bytes_read = deserialize_vlq(serialized)
    offset += bytes_read
    if offset >= len(serialized):
        raise DeserializeError("unexpected end of data after version")

    # Deserialize the block height.
    block_height, bytes_read = deserialize_vlq(serialized[offset:])
    offset += bytes_read
    if offset >= len(serialized):
        raise DeserializeError("unexpected end of data after height")

    # Deserialize the header code.
    code, bytes_read = deserialize_vlq(serialized[offset:])
    offset += bytes_read
    if offset >= len(serialized):
        raise DeserializeError("unexpected end of data after header")

    # Decode the header code.
    #
    # Bit 0 indicates whether the containing transaction is a coinbase.
    # Bit 1 indicates output 0 is unspent.
    # Bit 2 indicates output 1 is unspent.
    # Bits 3-x encodes the number of non-zero unspentness bitmap bytes that
    # follow.  When both output 0 and 1 are spent, it encodes N-1.
    is_coin_base = code & 0x01 != 0
    output0_unspent = code & 0x02 != 0
    output1_unspent = code & 0x04 != 0
    num_bitmap_bytes = code >> 3
    if not output0_unspent and not output1_unspent:
        num_bitmap_bytes += 1

    # Ensure there are enough bytes left to deserialize the unspentness
    # bitmap.
    if len(serialized[offset:]) < num_bitmap_bytes:
        raise DeserializeError("unexpected end of data for unspentness bitmap")

    # Add sparse output for unspent outputs 0 and 1 as needed based on the
    # details provided by the header code.
    output_indexes = []
    if output0_unspent:
        output_indexes.append(0)

    if output1_unspent:
        output_indexes.append(1)

    # Decode the unspentness bitmap adding a sparse output for each unspent
    # output.
    for i in range(0, num_bitmap_bytes):
        unspent_byte = serialized[offset]

        for j in range(0, 8):
            if unspent_byte & 0x01 != 0:
                # The first 2 outputs are encoded via the
                # header code, so adjust the output number
                # accordingly.
                output_num = 2 + i * 8 + j  # example [0x00 0x00 0x10] (bit 20 is set, so output 20+2 = 22 is unspent). Cacluated is bit offset.
                output_indexes.append(output_num)

            unspent_byte >>= 1

        offset += 1

    # Map to hold all of the converted outputs.
    entries = {}

    # All entries will need to potentially be marked as a coinbase.
    packed_flags = TxoFlags(0)
    if is_coin_base:
        packed_flags = TxoFlags(packed_flags | tfCoinBase)

    # Decode and add all of the utxos.
    for i, output_index in enumerate(output_indexes):
        # Decode the next utxo.
        try:
            amount, pk_script, bytes_read = decode_compressed_tx_out(serialized[offset:])
        except Exception as e:
            raise DeserializeError("unable to decode utxo at index %d: %s" % (i, e), err=e)

        offset += bytes_read

        # Create a new utxo entry with the details deserialized above.
        entries[output_index] = UtxoEntry(
            amount=amount,
            pk_script=pk_script,
            block_height=block_height,
            packed_flags=packed_flags
        )
    return entries


# TODO
def interrupt_requested(interrupt) -> bool:
    return False
