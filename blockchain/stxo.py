import database
import chainhash
import btcutil
import wire
from .compress import *

# # spendJournalBucketName is the name of the db bucket used to house
# # transactions outputs that are spent in each block.
# spendJournalBucketName = b"spendjournal"


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
    def __init__(self, amount=None, pk_script=None, height=None, is_coin_base=None):
        # Amount is the amount of the output.
        self.amount = amount or 0

        # PkScipt is the the public key script for the output.
        self.pk_script = pk_script or bytes()

        # Height is the height of the the block containing the creating tx.
        self.height = height or 0

        # Denotes if the creating tx is a coinbase.
        self.is_coin_base = is_coin_base or False


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


# spentTxOutSerializeSize returns the number of bytes it would take to
# serialize the passed stxo according to the format described above.
def spent_tx_out_serialize_size(stxo: SpentTxOut) -> int:
    size = serialize_size_vlq(spent_tx_out_header_code(stxo))
    if stxo.height > 0:
        # The legacy v1 spend journal format conditionally tracked the
        # containing transaction version when the height was non-zero,
        # so this is required for backwards compat.
        size += serialize_size_vlq(0)

    return size + compressed_tx_out_size(stxo.amount, stxo.pk_script)


# putSpentTxOut serializes the passed stxo according to the format described
# above directly into the passed target byte slice.  The target byte slice must
# be at least large enough to handle the number of bytes returned by the
# spentTxOutSerializeSize function or it will panic.
def put_spent_tx_out(target: bytearray, stxo: SpentTxOut) -> int:
    header_code = spent_tx_out_header_code(stxo)
    offset = put_vlq(target, header_code)
    if stxo > 0:
        # The legacy v1 spend journal format conditionally tracked the
        # containing transaction version when the height was non-zero,
        # so this is required for backwards compat.

        # TOCHECK
        # Not use offset += put_vlq(target[offset:], 0) because it cannot change target as expected
        # So below is a workround
        target_slice = target[offset:]
        offset += put_vlq(target_slice, 0)
        target[offset:] = target_slice

    # the same workaround as upwards
    target_slice = target[offset:]
    tx_out_offset = put_compressed_tx_out(target_slice, stxo.amount, stxo.pk_script)
    target[offset:] = target_slice

    offset += tx_out_offset
    return offset


# decodeSpentTxOut decodes the passed serialized stxo entry, possibly followed
# by other data, into the passed stxo struct.  It returns the number of bytes
# read.
def decode_spent_tx_out(serialized: bytes, stxo: SpentTxOut) -> int:
    # Ensure there are bytes to decode
    if len(serialized) == 0:
        raise DeserializeError("no serialized bytes")

    # Deserialize the header code.
    code, offset = deserialize_vlq(serialized)
    if offset >= len(serialized):
        raise DeserializeError("unexpected end of data after header code")

    # Decode the header code.
    #
    # Bit 0 indicates containing transaction is a coinbase.
    # Bits 1-x encode height of containing transaction.
    stxo.is_coin_base = (code & 0x01) != 0
    stxo.height = code >> 1

    if stxo.height > 0:
        # The legacy v1 spend journal format conditionally tracked the
        # containing transaction version when the height was non-zero,
        # so this is required for backwards compat.
        _, bytes_read = deserialize_vlq(serialized[offset:])
        offset += bytes_read
        if offset >= len(serialized):
            raise DeserializeError("unexpected end of data after reserved")

    # Decode the compressed txout.
    try:
        amount, pk_script, bytes_read = decode_compressed_tx_out(serialized[offset:])
    except Exception as e:
        # TOADD here missing the offset info to caller.
        # Add latter if need.
        raise DeserializeError("unable to decode txout: %s" % e)

    offset += bytes_read
    stxo.amount = amount
    stxo.pk_script = pk_script
    return offset


# deserializeSpendJournalEntry decodes the passed serialized byte slice into a
# slice of spent txouts according to the format described in detail above.
#
# Since the serialization format is not self describing, as noted in the
# format comments, this function also requires the transactions that spend the
# txouts.
def deserialize_spend_journal_entry(serialized: bytes, txns: [wire.MsgTx]) -> [SpentTxOut]:
    # Caclucate the total number of stxos
    num_stxos = 0

    for tx in txns:
        num_stxos += len(tx.tx_ins)

    # When a block has no spent txouts there is nothing to serialize.
    if len(serialized) == 0:
        # Ensure the block actually has no stxos.  This should never
        # happen unless there is database corruption or an empty entry
        # erroneously made its way into the database.
        if num_stxos != 0:
            raise AssertError(
                "mismatched spend journal serialization - no serialization for expected %d stxos" % num_stxos)

        return []

    # TOCONSIDER
    # 1. Why loop reversed here?, seems no affect
    # 2. the `append and reversed` pattern seems a little odd here, any better solutions?
    # Loop backwards through all transactions so everything is read in
    # reverse order to match the serialization order.
    stxos = []
    offset = 0
    for tx in reversed(txns):
        # Loop backwards through all of the transaction inputs and read
        # the associated stxo.
        for tx_in in reversed(tx.tx_ins):
            stxo = SpentTxOut()

            try:
                n = decode_spent_tx_out(serialized[offset:], stxo)
                offset += n
            except Exception as e:
                raise DeserializeError("unable to decode stxo for %s: %s" % (
                    tx_in.previous_out_point, e
                ))

            stxos.append(stxo)

    return reversed(stxos)


# serializeSpendJournalEntry serializes all of the passed spent txouts into a
# single byte slice according to the format described in detail above.
def serialize_spend_journal_entry(stxos: [SpentTxOut]) -> bytes or None:
    if len(stxos) == 0:
        return None

    # Calculate the size needed to serialize the entire journal entry.
    size = 0
    for stxo in stxos:
        size += spent_tx_out_serialize_size(stxo)

    serialized = bytearray(size)

    # Serialize each individual stxo directly into the slice in reverse
    # order one after the other.
    offset = 0
    for stxo in reversed(stxos):
        slice = serialized[offset:]
        this_offset = put_spent_tx_out(slice, stxo)
        serialized[offset:] = slice

        offset += this_offset

    return bytes(serialized)


# dbFetchSpendJournalEntry fetches the spend journal entry for the passed block
# and deserializes it into a slice of spent txout entries.
#
# NOTE: Legacy entries will not have the coinbase flag or height set unless it
# was the final output spend in the containing transaction.  It is up to the
# caller to handle this properly by looking the information up in the utxo set.
def db_fetch_spend_journal_entry(db_tx: database.Tx, block: btcutil.Block) -> [SpentTxOut]:
    # Exclude the coinbase transaction since it can't spend anything.
    spend_bucket = db_tx.metadata().bucket(spendJournalBucketName)
    serialized = spend_bucket.get(block.hash().to_bytes())
    block_txns = block.get_msg_block().transactions[1:]

    try:
        stoxs = deserialize_spend_journal_entry(serialized, block_txns)
    except DeserializeError as e:

        raise database.DBError(
            database.ErrorCode.ErrCorruption,
            "corrupt spend information for %s: %s" % (block.hash(), e)
        )

    return stoxs


# dbPutSpendJournalEntry uses an existing database transaction to update the
# spend journal entry for the given block hash using the provided slice of
# spent txouts.   The spent txouts slice must contain an entry for every txout
# the transactions in the block spend in the order they are spent.
def db_put_spend_journal_entry(db_tx: database.Tx, block_hash: chainhash.Hash, stxos: [SpentTxOut]):
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
