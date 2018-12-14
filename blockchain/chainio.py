import io
import copy
import database
import chainhash
from btcec.utils import int_to_bytes, bytes_to_int
from .utxo_viewpoint import *
from .compress import *
from .stxo import *


# Constant
# blockIndexBucketName is the name of the db bucket used to house to the
# block headers and contextual information.
blockIndexBucketName = b"blockheaderidx"

# hashIndexBucketName is the name of the db bucket used to house to the
# block hash -> block height index.
hashIndexBucketName = b"hashidx"

# heightIndexBucketName is the name of the db bucket used to house to
# the block height -> block hash index.
heightIndexBucketName = b"heightidx"

# byteOrder is the preferred byte order used for serializing numeric
# fields for storage in the database.
byteOrder = "little"

# chainStateKeyName is the name of the db key used to store the best
# chain state.
chainStateKeyName = b"chainstate"

# utxoSetBucketName is the name of the db bucket used to house the
# unspent transaction output set.
utxoSetBucketName = b"utxosetv2"



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


# -----------------------------------------------------------------------------
# The best chain state consists of the best block hash and height, the total
# number of transactions up to and including those in the best block, and the
# accumulated work sum up to and including the best block.
#
# The serialized format is:
#
#   <block hash><block height><total txns><work sum length><work sum>
#
#   Field             Type             Size
#   block hash        chainhash.Hash   chainhash.HashSize
#   block height      uint32           4 bytes
#   total txns        uint64           8 bytes
#   work sum length   uint32           4 bytes
#   work sum          big.Int          work sum length
# -----------------------------------------------------------------------------

# bestChainState represents the data to be stored the database for the current
# best chain state.
class BestChainState:
    def __init__(self, hash: chainhash.Hash, height: int, total_txns: int, work_sum: int):
        self.hash = hash
        self.height = height
        self.total_txns = total_txns
        self.work_sum = work_sum


# serializeBestChainState returns the serialization of the passed block best
# chain state.  This is data to be stored in the chain state bucket.
def serialize_best_chain_state(state: BestChainState):
    work_sum_bytes = int_to_bytes(state.work_sum)  # TOCHECK
    return state.hash.to_bytes() + state.height.to_bytes(4, byteOrder) + state.total_txns.to_bytes(8, byteOrder) + \
           len(work_sum_bytes).to_bytes(4, byteOrder) + work_sum_bytes


# deserializeBestChainState deserializes the passed serialized best chain
# state.  This is data stored in the chain state bucket and is updated after
# every block is connected or disconnected form the main chain.
# block.
def deserialize_best_chain_state(serialized_data: bytes) -> BestChainState:
    if len(serialized_data) < chainhash.HashSize + 16:
        raise database.DBError(c=database.ErrorCode.ErrCorruption, desc="corrupt best chain state")

    the_hash = chainhash.Hash(serialized_data[0: chainhash.HashSize])

    offset = chainhash.HashSize
    height = int.from_bytes(serialized_data[offset: offset + 4], byteOrder)

    offset += 4
    total_txns = int.from_bytes(serialized_data[offset: offset + 8], byteOrder)

    offset += 8
    work_sum_bytes_len = int.from_bytes(serialized_data[offset: offset + 4], byteOrder)

    offset += 4
    if len(serialized_data[offset:]) < work_sum_bytes_len:
        raise database.DBError(c=database.ErrorCode.ErrCorruption, desc="corrupt best chain state")

    work_sum_bytes = serialized_data[offset:offset + work_sum_bytes_len]
    work_sum = bytes_to_int(work_sum_bytes)
    return BestChainState(hash=the_hash, height=height, total_txns=total_txns, work_sum=work_sum)


def db_put_best_state(db_tx: database.Tx, snapshot, work_sum: int):
    """

    :param database.Tx db_tx:
    :param BestState snapshot:
    :param int work_sum:
    :return:
    """
    # Serialize the current best chain state.
    serialized_data = serialize_best_chain_state(
        BestChainState(
            hash=snapshot.hash,
            height=snapshot.height,
            total_txns=snapshot.total_txns,
            work_sum=work_sum
        ))
    #  Store the current best chain state into the database.
    return db_tx.metadata().put(chainStateKeyName, serialized_data)


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


# TODO
def outpoint_key(outpoint):
    pass


def recyle_outpoint_key(key):
    pass


# utxoEntryHeaderCode returns the calculated header code to be used when
# serializing the provided utxo entry.
def utxo_entry_header_code(entry: UtxoEntry):
    if entry.is_spent():
        raise AssertError("attempt to serialize spent utxo header")

    # As described in the serialization format comments, the header code
    # encodes the height shifted over one bit and the coinbase flag in the
    # lowest bit.
    header_code = entry.get_block_height() << 1
    if entry.is_coin_base():
        header_code |= 0x01
    return header_code


# serializeUtxoEntry returns the entry serialized to a format that is suitable
# for long-term storage.  The format is described in detail above.
def serialize_utxo_entry(entry: UtxoEntry) -> bytes or None:
    # Spent outputs have no serialization
    if entry.is_spent():
        return None

    # Encode the header code
    header_code = utxo_entry_header_code(entry)

    # Calculate the size needed to serialize the entry.
    size = serialize_size_vlq(header_code) + compressed_tx_out_size(entry.get_amount(), entry.get_pk_script())

    # Serialize the header code followed by the compressed unspent
    # transaction output.
    serialized = bytearray(size)
    offset = put_vlq(serialized, header_code)

    # do some trick as slice pass not work as reference  # TOCHANGE
    header_offset = offset
    serialized_slice = serialized[header_offset:]
    offset += put_compressed_tx_out(serialized_slice, entry.get_amount(), entry.get_pk_script())
    serialized[header_offset:] = serialized_slice
    return bytes(serialized)


# deserializeUtxoEntry decodes a utxo entry from the passed serialized byte
# slice into a new UtxoEntry using a format that is suitable for long-term
# storage.  The format is described in detail above.
def deserialize_utxo_entry(serialized: bytes) -> UtxoEntry:
    # Deserialize the header code.
    code, offset = deserialize_vlq(serialized)
    if offset >= len(serialized):
        raise DeserializeError("unexpected end of data after header")

    # Decode the header code.
    #
    # Bit 0 indicates whether the containing transaction is a coinbase.
    # Bits 1-x encode height of containing transaction.
    is_coin_base_p = (code & 0x01 != 0)
    block_height = code >> 1

    # Decode the compressed unspent transaction output.
    try:
        amount, pk_script, _ = decode_compressed_tx_out(serialized[offset:])
    except Exception as e:
        raise DeserializeError(msg="unable to decode utxo: %s" % str(e))

    entry = UtxoEntry(
        amount=amount,
        pk_script=pk_script,
        block_height=block_height,
        packed_flags=TxoFlags(0)
    )
    if is_coin_base_p:
        entry.packed_flags |= tfCoinBase

    return entry


# dbPutUtxoView uses an existing database transaction to update the utxo set
# in the database based on the provided utxo view contents and state.  In
# particular, only the entries that have been marked as modified are written
# to the database.
def db_put_utxo_view(db_tx: database.Tx, view: UtxoViewpoint):
    utxo_bucket = db_tx.metadata().bucket(utxoSetBucketName)
    for outpoint, entry in view.entries.items():
        # No need to update the database if the entry was not modified.
        if entry is None or not entry.is_modified():
            continue

        # Remove the utxo entry if it is spent.
        if entry.is_spent():
            key = outpoint_key(outpoint)
            utxo_bucket.delete(key)
            recyle_outpoint_key(key)

            continue

        # Serialize and store the utxo entry.
        serialized = serialize_utxo_entry(entry)

        key = outpoint_key(outpoint)
        utxo_bucket.put(key, serialized)

        # NOTE: The key is intentionally not recycled here since the
        # database interface contract prohibits modifications.  It will
        # be garbage collected normally when the database is done with
        # it.

    return

# TODO
# dbFetchUtxoEntryByHash attempts to find and fetch a utxo for the given hash.
# It uses a cursor and seek to try and do this as efficiently as possible.
#
# When there are no entries for the provided hash, nil will be returned for the
# both the entry and the error.
def db_fetch_utxo_entry_by_hash(db_tx: database.Tx, hash: chainhash.Hash):
    pass

# TODO
# dbFetchUtxoEntry uses an existing database transaction to fetch the specified
# transaction output from the utxo set.
#
# When there is no entry for the provided output, nil will be returned for both
# the entry and the error.
def db_fetch_utxo_entry(db_tx: database.Tx, outpoint: wire.OutPoint) -> UtxoEntry:
    pass

# countSpentOutputs returns the number of utxos the passed block spends.
def count_spent_outputs(block: btcutil.Block)-> int:
    # Exclude the coinbase transaction since it can't spend anything.
    num_spent = 0
    for tx in block.get_transactions():
        num_spent += len(tx.get_msg_tx().tx_ins)
    return num_spent
