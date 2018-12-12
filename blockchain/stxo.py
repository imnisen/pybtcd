import database
import chainhash

# spendJournalBucketName is the name of the db bucket used to house
# transactions outputs that are spent in each block.
spendJournalBucketName = b"spendjournal"


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
    pass

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
