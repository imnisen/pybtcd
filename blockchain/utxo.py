import database
from .error import *
from .constant import *
from .compress import *


# txoFlags is a bitmask defining additional information and state for a
# transaction output in a utxo view.
class TxoFlags(int):
    pass


# tfCoinBase indicates that a txout was contained in a coinbase tx.
tfCoinBase = TxoFlags(1 << 0)

# tfSpent indicates that a txout is spent.
tfSpent = TxoFlags(1 << 1)

# tfModified indicates that a txout has been modified since it was
# loaded.
tfModified = TxoFlags(1 << 2)


class UtxoEntry:
    def __init__(self, amount: int = None, pk_script: bytes = None, block_height: int = None,
                 packed_flags: TxoFlags = None):
        """

        :param int64 amount:
        :param bytes pk_script:
        :param int32 block_height:
        :param TxoFlags packed_flags:
        """
        self.amount = amount or 0

        # The public key script for the output.
        self.pk_script = pk_script or bytes()

        # Height of block containing tx.
        self.block_height = block_height or 0

        # packedFlags contains additional info about output such as whether it
        # is a coinbase, whether it is spent, and whether it has been modified
        # since it was loaded.  This approach is used in order to reduce memory
        # usage since there will be a lot of these in memory.
        self.packed_flags = packed_flags

    def __eq__(self, other):
        return self.amount == other.amount and \
               self.pk_script == other.pk_script and \
               self.block_height == other.block_height and \
               self.packed_flags == other.packed_flags

    # isModified returns whether or not the output has been modified since it was
    # loaded.
    def is_modified(self) -> bool:
        return self.packed_flags & tfModified == tfModified

    # IsCoinBase returns whether or not the output was contained in a coinbase
    # transaction.
    def is_coin_base(self) -> bool:
        return self.packed_flags & tfCoinBase == tfCoinBase

    # IsSpent returns whether or not the output has been spent based upon the
    # current state of the unspent transaction output view it was obtained from.
    def is_spent(self) -> bool:
        return self.packed_flags & tfSpent == tfSpent

    # BlockHeight returns the height of the block containing the output.
    def get_block_height(self) -> int:
        return self.block_height

    # Spend marks the output as spent.  Spending an output that is already spent
    # has no effect.
    def spend(self):
        if self.is_spent():
            return

        self.packed_flags = self.packed_flags | (tfSpent | tfModified)

    # Amount returns the amount of the output.
    def get_amount(self):
        return self.amount

    # PkScript returns the public key script for the output.
    def get_pk_script(self):
        return self.pk_script

    # Clone returns a shallow copy of the utxo entry.
    def clone(self):
        return UtxoEntry(
            amount=self.amount,
            pk_script=self.pk_script,
            block_height=self.block_height,
            packed_flags=self.packed_flags,
        )


# -----------------------------------------------------------------------------
# The unspent transaction output (utxo) set consists of an entry for each
# unspent output using a format that is optimized to reduce space using domain
# specific compression algorithms.  This format is a slightly modified version
# of the format used in Bitcoin Core.
#
# Each entry is keyed by an outpoint as specified below.  It is important to
# note that the key encoding uses a VLQ, which employs an MSB encoding so
# iteration of utxos when doing byte-wise comparisons will produce them in
# order.
#
# The serialized key format is:
#   <hash><output index>
#
#   Field                Type             Size
#   hash                 chainhash.Hash   chainhash.HashSize
#   output index         VLQ              variable
#
# The serialized value format is:
#
#   <header code><compressed txout>
#
#   Field                Type     Size
#   header code          VLQ      variable
#   compressed txout
#     compressed amount  VLQ      variable
#     compressed script  []byte   variable
#
# The serialized header code format is:
#   bit 0 - containing transaction is a coinbase
#   bits 1-x - height of the block that contains the unspent txout
#
# Example 1:
# From tx in main blockchain:
# Blk 1, 0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098:0
#
#    03320496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52
#    <><------------------------------------------------------------------>
#     |                                          |
#   header code                         compressed txout
#
#  - header code: 0x03 (coinbase, height 1)
#  - compressed txout:
#    - 0x32: VLQ-encoded compressed amount for 5000000000 (50 BTC)
#    - 0x04: special script type pay-to-pubkey
#    - 0x96...52: x-coordinate of the pubkey
#
# Example 2:
# From tx in main blockchain:
# Blk 113931, 4a16969aa4764dd7507fc1de7f0baa4850a246de90c45e59a3207f9a26b5036f:2
#
#    8cf316800900b8025be1b3efc63b0ad48e7f9f10e87544528d58
#    <----><------------------------------------------>
#      |                             |
#   header code             compressed txout
#
#  - header code: 0x8cf316 (not coinbase, height 113931)
#  - compressed txout:
#    - 0x8009: VLQ-encoded compressed amount for 15000000 (0.15 BTC)
#    - 0x00: special script type pay-to-pubkey-hash
#    - 0xb8...58: pubkey hash
#
# Example 3:
# From tx in main blockchain:
# Blk 338156, 1b02d1c8cfef60a189017b9a420c682cf4a0028175f2f563209e4ff61c8c3620:22
#
#    a8a2588ba5b9e763011dd46a006572d820e448e12d2bbb38640bc718e6
#    <----><-------------------------------------------------->
#      |                             |
#   header code             compressed txout
#
#  - header code: 0xa8a258 (not coinbase, height 338156)
#  - compressed txout:
#    - 0x8ba5b9e763: VLQ-encoded compressed amount for 366875659 (3.66875659 BTC)
#    - 0x01: special script type pay-to-script-hash
#    - 0x1d...e6: script hash
# -----------------------------------------------------------------------------

# TOCONSIDER
# Don't like the origin, I don't use sync.Pool here, for simplicity.
def outpoint_key(outpoint: wire.OutPoint) -> bytes:
    outpoint_index_bytearray = bytearray(serialize_size_vlq(outpoint.index))
    put_vlq(outpoint_index_bytearray, outpoint.index)
    return outpoint.hash.to_bytes() + bytes(outpoint_index_bytearray)  # TOCHECK


# def recycle_outpoint_key(key):
#     pass


# utxoEntryHeaderCode returns the calculated header code to be used when
# serializing the provided utxo entry.
def utxo_entry_header_code(entry: UtxoEntry) -> int:
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


# dbFetchUtxoEntryByHash attempts to find and fetch a utxo for the given hash.
# It uses a cursor and seek to try and do this as efficiently as possible.
#
# When there are no entries for the provided hash, nil will be returned for the
# both the entry and the error.
def db_fetch_utxo_entry_by_hash(db_tx: database.Tx, hash: chainhash.Hash) -> UtxoEntry or None:
    # Attempt to find an entry by seeking for the hash along with a zero
    # index.  Due to the fact the keys are serialized as <hash><index>,
    # where the index uses an MSB encoding, if there are any entries for
    # the hash at all, one will be found.
    cursor = db_tx.metadata().bucket(utxoSetBucketName).cursor()
    key = outpoint_key(wire.OutPoint(hash=hash, index=0))
    ok = cursor.seek(key)
    if not ok:
        return None

    # An entry was found, but it could just be an entry with the next
    # highest hash after the requested one, so make sure the hashes
    # actually match.
    cursor_key = cursor.key()
    if len(cursor_key) < chainhash.HashSize:
        return None

    if hash.to_bytes() != cursor_key[:chainhash.HashSize]:
        return None

    return deserialize_utxo_entry(cursor.value())


# dbFetchUtxoEntry uses an existing database transaction to fetch the specified
# transaction output from the utxo set.
#
# When there is no entry for the provided output, nil will be returned for both
# the entry and the error.
def db_fetch_utxo_entry(db_tx: database.Tx, outpoint: wire.OutPoint) -> UtxoEntry or None:
    # Fetch the unspent transaction output information for the passed
    # transaction output.  Return nil when there is no entry.
    key = outpoint_key(outpoint)
    serialized_utxo = db_tx.metadata().bucket(utxoSetBucketName).get(key)
    if serialized_utxo is None:
        return None

    # A non-nil zero-length entry means there is an entry in the database
    # for a spent transaction output which should never be the case.
    if len(serialized_utxo) == 0:
        raise AssertError("database contains entry for spent tx output %s" % outpoint)

    # Deserialize the utxo entry and return it.
    try:
        entry = deserialize_utxo_entry(serialized_utxo)
    except DeserializeError as e:
        raise database.DBError(c=database.ErrorCode.ErrCorruption,
                               desc="corrupt utxo entry for %s: %s" % (outpoint, e))

    return entry
