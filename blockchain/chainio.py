import io
import copy
import database
import chainhash

# Constant
# blockIndexBucketName is the name of the db bucket used to house to the
# block headers and contextual information.
blockIndexBucketName = b"blockheaderidx"

# hashIndexBucketName is the name of the db bucket used to house to the
# block hash -> block height index.
hashIndexBucketName = b"hashidx"

# byteOrder is the preferred byte order used for serializing numeric
# fields for storage in the database.
byteOrder = "little"


# blockIndexKey generates the binary key for an entry in the block index
# bucket. The key is composed of the block height encoded as a big-endian
# 32-bit unsigned int followed by the 32 byte block hash.
def block_index_key(block_hash: chainhash.Hash, block_height: int) -> bytes:
    return block_height.to_bytes(4, "big") + block_hash.to_bytes()


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


class NotInMainChainErr(Exception):
    pass
