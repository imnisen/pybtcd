import io
import database
from .block_node import *


# dbFetchVersion fetches an individual version with the given key from the
# metadata bucket.  It is primarily used to track versions on entities such as
# buckets.  It returns zero if the provided key does not exist.
def db_fetch_version(db_tx: database.Tx, key: bytes) -> int:
    serialized = db_tx.metadata().get(key)

    if serialized is None:
        return 0

    return int.from_bytes(serialized, byteOrder)


# dbPutVersion uses an existing database transaction to update the provided
# key in the metadata bucket to the given version.  It is primarily used to
# track versions on entities such as buckets.
def db_put_version(db_tx: database.Tx, key: bytes, version: int):
    serialized = version.to_bytes(4, byteOrder)
    db_tx.metadata().put(key, serialized)
    return


# dbFetchOrCreateVersion uses an existing database transaction to attempt to
# fetch the provided key from the metadata bucket as a version and in the case
# it doesn't exist, it adds the entry with the provided default version and
# returns that.  This is useful during upgrades to automatically handle loading
# and adding version keys as necessary.
def db_fetch_or_create_version(db_tx: database.Tx, key: bytes, default_version: int) -> int:
    version = db_fetch_version(db_tx, key)
    if version == 0:
        version = default_version
        db_put_version(db_tx, key, version)

    return version


# -----------------------------------------------------------------------------
# The block index consists of two buckets with an entry for every block in the
# main chain.  One bucket is for the hash to height mapping and the other is
# for the height to hash mapping.
#
# The serialized format for values in the hash to height bucket is:
#   <height>
#
#   Field      Type     Size
#   height     uint32   4 bytes
#
# The serialized format for values in the height to hash bucket is:
#   <hash>
#
#   Field      Type             Size
#   hash       chainhash.Hash   chainhash.HashSize
# -----------------------------------------------------------------------------

# dbPutBlockIndex uses an existing database transaction to update or add the
# block index entries for the hash to height and height to hash mappings for
# the provided values.
def db_put_block_index(db_tx: database.Tx, hash: chainhash.Hash, height: int):
    # Serialize the height for use in the index entries.
    serialized_height = height.to_bytes(4, byteOrder)

    # Add the block hash to height mapping to the index.
    meta = db_tx.metadata()
    hash_index = meta.bucket(hashIndexBucketName)
    hash_index.put(hash.to_bytes(), serialized_height)

    # Add the block height to hash mapping to the index.
    height_index = meta.bucket(heightIndexBucketName)
    height_index.put(serialized_height, hash.to_bytes())
    return


# dbRemoveBlockIndex uses an existing database transaction remove block index
# entries from the hash to height and height to hash mappings for the provided
# values.
def db_remove_block_index(db_tx: database.Tx, hash: chainhash.Hash, height: int):
    # Remove the block hash to height mapping
    meta = db_tx.metadata()
    hash_index_bucket = meta.bucket(hashIndexBucketName)
    hash_index_bucket.delete(hash.to_bytes())

    # Remove the block height to hash mapping.
    height_index_bucket = meta.bucket(heightIndexBucketName)
    height_index_bucket.delete(height.to_bytes(4, byteOrder))

    return


# dbFetchHeightByHash uses an existing database transaction to retrieve the
# height for the provided hash from the index.
def db_fetch_height_by_hash(db_tx: database.Tx, hash: chainhash.Hash):
    meta = db_tx.metadata()
    hash_index_bucket = meta.bucket(hashIndexBucketName)
    serialized_height = hash_index_bucket.get(hash.to_bytes())
    if serialized_height is None:
        msg = "block %s is not in the main chain" % hash.to_bytes()
        raise NotInMainChainErr(msg)

    return int.from_bytes(serialized_height, byteOrder)


# dbFetchHashByHeight uses an existing database transaction to retrieve the
# hash for the provided height from the index.
def db_fetch_hash_by_height(db_tx: database.Tx, height: int) -> chainhash.Hash:
    meta = db_tx.metadata()
    height_index_bucket = meta.bucket(heightIndexBucketName)
    hash_bytes = height_index_bucket.get(height.to_bytes(4, byteOrder))
    if hash_bytes is None:
        msg = "no block at height %d exists" % height
        raise NotInMainChainErr(msg)

    return chainhash.Hash(hash_bytes)


# deserializeBlockRow parses a value in the block index bucket into a block
# header and block status bitfield.
def deserialize_block_row(block_row: bytes):
    buffer = io.BytesIO(block_row)

    header = wire.BlockHeader()
    header.deserialize(buffer)

    statue_byte = buffer.read(1)

    return header, BlockStatus(
        statue_byte)  # TOCHECK # TODO, the bytes read is not valid enum, so refactor BlockStatus to not use enum


# dbFetchHeaderByHash uses an existing database transaction to retrieve the
# block header for the provided hash.
def db_fetch_header_by_hash(db_tx: database.Tx, hash: chainhash.Hash):
    header_bytes = db_tx.fetch_block_header(hash)
    header = wire.BlockHeader()
    header.deserialize(header_bytes)
    return header


# dbFetchHeaderByHeight uses an existing database transaction to retrieve the
# block header for the provided hash.
def db_fetch_header_by_height(db_tx: database.Tx, height: int):
    hash = db_fetch_hash_by_height(db_tx, height)
    return db_fetch_header_by_hash(db_tx, hash)


# dbFetchBlockByNode uses an existing database transaction to retrieve the
# raw block for the provided node, deserialize it, and return a btcutil.Block
# with the height set.
def db_fetch_block_by_node(db_tx: database.Tx, node: BlockNode) -> btcutil.Block:
    # Load the raw block bytes from the database
    block_bytes = db_tx.fetch_block(node.hash)

    # Create the encapsulated block and set the height appropriately.
    block = btcutil.Block.from_bytes(block_bytes)
    block.set_height(node.height)
    return block


# dbStoreBlockNode stores the block header and validation status to the block
# index bucket. This overwrites the current entry if there exists one.
def db_store_block_node(db_tx: database.Tx, node):
    """

    :param database.Tx db_tx:
    :param BlockNode node:
    :return:
    """
    # Serialize block data to be stored.
    header = node.header()
    w = io.BytesIO()
    header.serialize(w)
    value = w.getvalue()

    # Write block header data to block index bucket.
    block_index_bucket = db_tx.metadata().bucket(blockIndexBucketName)
    key = block_index_key(node.hash, node.height)
    return block_index_bucket.put(key, value)


# dbStoreBlock stores the provided block in the database if it is not already
# there. The full block data is written to ffldb.
def db_store_block(db_tx: database.Tx, block: btcutil.Block):
    has_block = db_tx.has_block(block.hash())
    if has_block:
        return
    return db_tx.store_block(block)


# blockIndexKey generates the binary key for an entry in the block index
# bucket. The key is composed of the block height encoded as a big-endian
# 32-bit unsigned int followed by the 32 byte block hash.
def block_index_key(block_hash: chainhash.Hash, block_height: int) -> bytes:
    return block_height.to_bytes(4, "big") + block_hash.to_bytes()


class NotInMainChainErr(Exception):
    pass


# countSpentOutputs returns the number of utxos the passed block spends.
def count_spent_outputs(block: btcutil.Block) -> int:
    # Exclude the coinbase transaction since it can't spend anything.
    num_spent = 0
    for tx in block.get_transactions():
        num_spent += len(tx.get_msg_tx().tx_ins)
    return num_spent
