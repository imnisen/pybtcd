import io
import copy
import database
import chainhash
from btcec.utils import int_to_bytes, bytes_to_int
from .utxo_viewpoint import *
from .compress import *

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

# spendJournalBucketName is the name of the db bucket used to house
# transactions outputs that are spent in each block.
spendJournalBucketName = b"spendjournal"


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
    header_code = entry.block_height() << 1
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
    size = serialize_size_vlq(header_code) + compressed_tx_out_size(entry.amount(), entry.pk_script())

    # Serialize the header code followed by the compressed unspent
    # transaction output.
    serialized = bytearray(size)
    offset = put_vlq(serialized, header_code)

    # do some trick as slice pass not work as reference  # TOCHANGE
    header_offset = offset
    serialized_slice = serialized[header_offset:]
    offset += put_compressed_tx_out(serialized_slice, entry.amount(), entry.pk_script())
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


# -----------------------------------------------------------------------------
# The transaction spend journal consists of an entry for each block connected
# to the main chain which contains the transaction outputs the block spends
# serialized such that the order is the reverse of the order they were spent.
#
# This is required because reorganizing the chain necessarily entails
# disconnecting blocks to get back to the point of the fork which implies
# unspending all of the transaction outputs that each block previously spent.
# Since the utxo set, by definition, only contains unspent transaction outputs,
# the spent transaction outputs must be resurrected from somewhere.  There is
# more than one way this could be done, however this is the most straight
# forward method that does not require having a transaction index and unpruned
# blockchain.
#
# NOTE: This format is NOT self describing.  The additional details such as
# the number of entries (transaction inputs) are expected to come from the
# block itself and the utxo set (for legacy entries).  The rationale in doing
# this is to save space.  This is also the reason the spent outputs are
# serialized in the reverse order they are spent because later transactions are
# allowed to spend outputs from earlier ones in the same block.
#
# The reserved field below used to keep track of the version of the containing
# transaction when the height in the header code was non-zero, however the
# height is always non-zero now, but keeping the extra reserved field allows
# backwards compatibility.
#
# The serialized format is:
#
#   [<header code><reserved><compressed txout>],...
#
#   Field                Type     Size
#   header code          VLQ      variable
#   reserved             byte     1
#   compressed txout
#     compressed amount  VLQ      variable
#     compressed script  []byte   variable
#
# The serialized header code format is:
#   bit 0 - containing transaction is a coinbase
#   bits 1-x - height of the block that contains the spent txout
#
# Example 1:
# From block 170 in main blockchain.
#
#    1300320511db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c
#    <><><------------------------------------------------------------------>
#     | |                                  |
#     | reserved                  compressed txout
#    header code
#
#  - header code: 0x13 (coinbase, height 9)
#  - reserved: 0x00
#  - compressed txout 0:
#    - 0x32: VLQ-encoded compressed amount for 5000000000 (50 BTC)
#    - 0x05: special script type pay-to-pubkey
#    - 0x11...5c: x-coordinate of the pubkey
#
# Example 2:
# Adapted from block 100025 in main blockchain.
#
#    8b99700091f20f006edbc6c4d31bae9f1ccc38538a114bf42de65e868b99700086c64700b2fb57eadf61e106a100a7445a8c3f67898841ec
#    <----><><----------------------------------------------><----><><---------------------------------------------->
#     |    |                         |                        |    |                         |
#     |    reserved         compressed txout                  |    reserved         compressed txout
#    header code                                          header code
#
#  - Last spent output:
#    - header code: 0x8b9970 (not coinbase, height 100024)
#    - reserved: 0x00
#    - compressed txout:
#      - 0x91f20f: VLQ-encoded compressed amount for 34405000000 (344.05 BTC)
#      - 0x00: special script type pay-to-pubkey-hash
#      - 0x6e...86: pubkey hash
#  - Second to last spent output:
#    - header code: 0x8b9970 (not coinbase, height 100024)
#    - reserved: 0x00
#    - compressed txout:
#      - 0x86c647: VLQ-encoded compressed amount for 13761000000 (137.61 BTC)
#      - 0x00: special script type pay-to-pubkey-hash
#      - 0xb2...ec: pubkey hash
# -----------------------------------------------------------------------------

# SpentTxOut contains a spent transaction output and potentially additional
# contextual information such as whether or not it was contained in a coinbase
# transaction, the version of the transaction it was contained in, and which
# block height the containing transaction was included in.  As described in
# the comments above, the additional contextual information will only be valid
# when this spent txout is spending the last unspent output of the containing
# transaction.
class SpentTxOut:
    def __init__(self, amount, pk_script, height, is_coin_base):
        # Amount is the amount of the output.
        self.amount = amount

        # PkScipt is the the public key script for the output.
        self.pk_script = pk_script

        # Height is the height of the the block containing the creating tx.
        self.height = height

        # Denotes if the creating tx is a coinbase.
        self.is_coin_base = is_coin_base


# spentTxOutHeaderCode returns the calculated header code to be used when
# serializing the provided stxo entry.
def spent_tx_out_header_code(stxo: SpentTxOut):
    # As described in the serialization format comments, the header code
    # encodes the height shifted over one bit and the coinbase flag in the
    # lowest bit.
    header_code = stxo.height << 1
    if stxo.is_coin_base:
        header_code |= 0x01
    return header_code


# TODO
# putSpentTxOut serializes the passed stxo according to the format described
# above directly into the passed target byte slice.
def put_spent_tx_out(stxos: SpentTxOut):
    header_code = spent_tx_out_header_code(stxos)
    # TODO


# serializeSpendJournalEntry serializes all of the passed spent txouts into a
# single byte slice according to the format described in detail above.
def serialize_spend_journal_entry(stxos: [SpentTxOut]):
    if len(stxos) == 0:
        return

    # Calculate the size needed to serialize the entire journal entry.
    serilized = b''
    for stxo in stxos:
        serilized += put_spent_tx_out(stxo)
    return serilized


# dbPutSpendJournalEntry uses an existing database transaction to update the
# spend journal entry for the given block hash using the provided slice of
# spent txouts.   The spent txouts slice must contain an entry for every txout
# the transactions in the block spend in the order they are spent.
def db_put_spend_journal_entry(db_tx: database.Tx, block_hash: chainhash.Hash, stxos: []):
    spend_bucket = db_tx.metadata().bucket(spendJournalBucketName)
    serialized = serialize_spend_journal_entry(stxos)
    spend_bucket.put(block_hash.to_bytes(), serialized)
    return


# dbRemoveSpendJournalEntry uses an existing database transaction to remove the
# spend journal entry for the passed block hash.
def db_remove_spend_journal_entry(db_tx: database.Tx, block_hash: chainhash.Hash):
    spend_bucket = db_tx.metadata().bucket(spendJournalBucketName)
    spend_bucket.delete(block_hash.to_bytes())
    return
