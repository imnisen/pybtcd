import database
import btcutil
import chainhash
import chaincfg
import pyutil
import txscript
import wire
from .common import *
from .tx_index import *
import copy
import typing
import io

# addrIndexName is the human-readable name for the index.
addrIndexName = "address index"

# level0MaxEntries is the maximum number of transactions that are
# stored in level 0 of an address index entry.  Subsequent levels store
# 2^n * level0MaxEntries entries, or in words, double the maximum of
# the previous level.
level0MaxEntries = 8

# Size of a transaction entry.  It consists of 4 bytes block id + 4
# bytes offset + 4 bytes length.
txEntrySize = 4 + 4 + 4

# addrIndexKey is the key of the address index and the db bucket used
# to house it.
addrIndexKey = b"txbyaddridx"

# addrKeySize is the number of bytes an address key consumes in the
# index.  It consists of 1 byte address type + 20 bytes hash160.
addrKeySize = 1 + 20

# levelKeySize is the number of bytes a level key in the address index
# consumes.  It consists of the address key + 1 byte for the level.
levelKeySize = addrKeySize + 1

# levelOffset is the offset in the level key which identifes the level.
levelOffset = levelKeySize - 1

# addrKeyTypePubKeyHash is the address type in an address key which
# represents both a pay-to-pubkey-hash and a pay-to-pubkey address.
# This is done because both are identical for the purposes of the
# address index.
addrKeyTypePubKeyHash = 0

# addrKeyTypeScriptHash is the address type in an address key which
# represents a pay-to-script-hash address.  This is necessary because
# the hash of a pubkey address might be the same as that of a script
# hash.
addrKeyTypeScriptHash = 1

# addrKeyTypePubKeyHash is the address type in an address key which
# represents a pay-to-witness-pubkey-hash address. This is required
# as the 20-byte data push of a p2wkh witness program may be the same
# data push used a p2pkh address.
addrKeyTypeWitnessPubKeyHash = 2

# addrKeyTypeScriptHash is the address type in an address key which
# represents a pay-to-witness-script-hash address. This is required,
# as p2wsh are distinct from p2sh addresses since they use a new
# script template, as well as a 32-byte data push.
addrKeyTypeWitnessScriptHash = 3

# -----------------------------------------------------------------------------
# The address index maps addresses referenced in the blockchain to a list of
# all the transactions involving that address.  Transactions are stored
# according to their order of appearance in the blockchain.  That is to say
# first by block height and then by offset inside the block.  It is also
# important to note that this implementation requires the transaction index
# since it is needed in order to catch up old blocks due to the fact the spent
# outputs will already be pruned from the utxo set.
#
# The approach used to store the index is similar to a log-structured merge
# tree (LSM tree) and is thus similar to how leveldb works internally.
#
# Every address consists of one or more entries identified by a level starting
# from 0 where each level holds a maximum number of entries such that each
# subsequent level holds double the maximum of the previous one.  In equation
# form, the number of entries each level holds is 2^n * firstLevelMaxSize.
#
# New transactions are appended to level 0 until it becomes full at which point
# the entire level 0 entry is appended to the level 1 entry and level 0 is
# cleared.  This process continues until level 1 becomes full at which point it
# will be appended to level 2 and cleared and so on.
#
# The result of this is the lower levels contain newer transactions and the
# transactions within each level are ordered from oldest to newest.
#
# The intent of this approach is to provide a balance between space efficiency
# and indexing cost.  Storing one entry per transaction would have the lowest
# indexing cost, but would waste a lot of space because the same address hash
# would be duplicated for every transaction key.  On the other hand, storing a
# single entry with all transactions would be the most space efficient, but
# would cause indexing cost to grow quadratically with the number of
# transactions involving the same address.  The approach used here provides
# logarithmic insertion and retrieval.
#
# The serialized key format is:
#
#   <addr type><addr hash><level>
#
#   Field           Type      Size
#   addr type       uint8     1 byte
#   addr hash       hash160   20 bytes
#   level           uint8     1 byte
#   -----
#   Total: 22 bytes
#
# The serialized value format is:
#
#   [<block id><start offset><tx length>,...]
#
#   Field           Type      Size
#   block id        uint32    4 bytes
#   start offset    uint32    4 bytes
#   tx length       uint32    4 bytes
#   -----
#   Total: 12 bytes per indexed tx
# -----------------------------------------------------------------------------


byteOrder = 'little'


# serializeAddrIndexEntry serializes the provided block id and transaction
# location according to the format described in detail above.
def serialize_addr_index_entry(block_id: int, tx_loc: wire.TxLoc) -> bytes:
    s = io.BytesIO()
    wire.write_element(s, "uint32", byteOrder)
    wire.write_element(s, "uint32", tx_loc.tx_start)
    wire.write_element(s, "uint32", tx_loc.tx_len)
    return s.getvalue()


# deserializeAddrIndexEntry decodes the passed serialized byte slice into the
# provided region struct according to the format described in detail above and
# uses the passed block hash fetching function in order to conver the block ID
# to the associated block hash.
def deserialize_addr_index_entry(serialized: bytes, region: database.BlockRegion,
                                 fetch_block_hash_func: typing.Callable[bytes, chainhash.Hash]):
    # Ensure there are enough bytes to decode.
    if len(serialized) < txEntrySize:
        return DeserializeError("unexpected end of data")

    region.hash = fetch_block_hash_func(serialized[0:4])
    region.offset = wire.read_element(serialized[4:8], "uint32")
    region.len = wire.read_element(serialized[8:12], "uint32")
    return


# keyForLevel returns the key for a specific address and level in the address
# index entry.
def key_for_level(addr_key: bytes, level: int) -> bytes:
    return addr_key + bytes([level])


# dbPutAddrIndexEntry updates the address index to include the provided entry
# according to the level-based scheme described in detail above.
def db_put_addr_index_entry(bucket: InternalBucket, addr_key: bytes, block_id: int, tx_loc: wire.TxLoc):
    # Start with level 0 and its initial max number of entries.
    cur_level = 0
    max_level_bytes = level0MaxEntries * txEntrySize

    # Simply append the new entry to level 0 and return now when it will
    # fit.  This is the most common path.
    new_data = serialize_addr_index_entry(block_id, tx_loc)
    level_0_key = key_for_level(addr_key, level=0)
    level_0_data = bucket.get(level_0_key)
    if len(level_0_data) + len(new_data) <= max_level_bytes:
        merged_data = level_0_data + new_data
        return bucket.put(level_0_key, merged_data)

    # What here do is, if levele_0 if full, find upwards, find a non-full entry, then move each entry one step up
    # So level0 could be empty, for latter use.

    # At this point, level 0 is full, so merge each level into higher
    # levels as many times as needed to free up level 0.
    prev_level_data = level_0_data
    while True:
        # Each new level holds twice as much as the previous one
        cur_level += 1
        max_level_bytes *= 2

        # Move to the next level as long as the current level is full
        cur_level_key = key_for_level(addr_key, level=cur_level)
        cur_level_data = bucket.get(cur_level_key)
        if len(cur_level_data) == max_level_bytes:
            prev_level_data = cur_level_data
            continue

        # The current level has room for the data in the previous one,
        # so merge the data from previous level into it.
        merged_data = prev_level_data + cur_level_data
        bucket.put(cur_level_key, merged_data)

        # Move all of the levels before the previous one up a level.
        for merge_level in range(cur_level - 1, 0, -1):
            merge_level_key = key_for_level(addr_key, merge_level)
            prev_level_key = key_for_level(addr_key, merge_level - 1)
            prev_data = bucket.get(prev_level_key)
            bucket.put(merge_level_key, prev_data)

        break

    # Finally, insert the new entry into level 0 noew that it is empty
    return bucket.put(level_0_key, new_data)


# maxEntriesForLevel returns the maximum number of entries allowed for the
# given address index level.
def max_entries_for_level(level: int) -> int:
    return level0MaxEntries * pow(2, level)


# minEntriesToReachLevel returns the minimum number of entries that are
# required to reach the given address index level.
def min_entries_to_reach_level(level: int) -> int:
    max_entries_for_l = level0MaxEntries
    min_required = 1
    for _ in range(1, level + 1):
        min_required += max_entries_for_l
        max_entries_for_l *= 2
    return min_required


# TOCONSIDER the delete logic here is confusing TODO
# dbRemoveAddrIndexEntries removes the specified number of entries from from
# the address index for the provided key.  An assertion error will be returned
# if the count exceeds the total number of entries in the index.
def db_remove_addr_index_entries(bucket: InternalBucket, addr_key: bytes, count: int):
    # Nothing to do if no entries are being deleted
    if count <= 0:
        return

    # Make use of a local map to track pending updates and define a closure
    # to apply it to the database.  This is done in order to reduce the
    # number of database reads and because there is more than one exit
    # path that needs to apply the updates.
    pending_updates = {}

    def apply_pending():
        for level, data in pending_updates.items():
            cur_level_key = key_for_level(addr_key, level)
            if len(data) == 0:
                bucket.delete(cur_level_key)
                continue

            bucket.put(cur_level_key, data)
        return

    # Loop forwards through the levels while removing entries until the
    # specified number has been removed.  This will potentially result in
    # entirely empty lower levels which will be backfilled below.
    highest_loaded_level = 0
    num_remaining = count
    level = -1
    while num_remaining > 0:
        level += 1

        # Load the data for the level from the database
        cur_level_key = key_for_level(addr_key, level)
        cur_level_data = bucket.get(cur_level_key)
        if len(cur_level_data) == 0 and num_remaining > 0:
            raise AssertionError(
                "dbRemoveAddrIndexEntries not enough entries for address key %s to delete %s entries" % addr_key, count)

        pending_updates[level] = cur_level_data
        highest_loaded_level = level

        # Delete the entrie level as needed
        num_entries = len(cur_level_data) // txEntrySize
        if num_remaining >= num_entries:
            pending_updates[level] = bytes()
            num_remaining -= num_entries
            continue

        # Remove remaining entries to delete from the level.
        offset_end = len(cur_level_data) - (num_remaining * txEntrySize)
        pending_updates = cur_level_data[:offset_end]
        break

    # When all elements in level 0 were not removed there is nothing left to do other than updating the databse
    if len(pending_updates) != 0:
        return apply_pending()

    # At this point there are one or more empty levels before the current
    # level which need to be backfilled and the current level might have
    # had some entries deleted from it as well.  Since all levels after
    # level 0 are required to either be empty, half full, or completely
    # full, the current level must be adjusted accordingly by backfilling
    # each previous levels in a way which satisfies the requirements.  Any
    # entries that are left are assigned to level 0 after the loop as they
    # are guaranteed to fit by the logic in the loop.  In other words, this
    # effectively squashes all remaining entries in the current level into
    # the lowest possible levels while following the level rules.
    #
    # Note that the level after the current level might also have entries
    # and gaps are not allowed, so this also keeps track of the lowest
    # empty level so the code below knows how far to backfill in case it is
    # required.
    lowest_empty_level = 255
    cur_level_data = pending_updates[highest_loaded_level]
    cur_level_max_entries = max_entries_for_level(highest_loaded_level)  # TODO
    for level in range(highest_loaded_level, 0, -1):
        # When there are not enough entries left in the current level
        # for the number that would be required to reach it, clear the
        # the current level which effectively moves them all up to the
        # previous level on the next iteration.  Otherwise, there are
        # are sufficient entries, so update the current level to
        # contain as many entries as possible while still leaving
        # enough remaining entries required to reach the level.
        num_entries = len(cur_level_data) // txEntrySize
        prev_level_max_entries = cur_level_max_entries // 2
        min_prev_required = min_entries_to_reach_level(level - 1)  # TODO
        if num_entries < prev_level_max_entries + min_prev_required:
            lowest_empty_level = level
            pending_updates[level] = bytes()
        else:
            # This level can only be completely full or half full,
            # so choose the appropriate offset to ensure enough
            # entries remain to reach the level.
            if num_entries - cur_level_max_entries >= min_prev_required:
                offset = cur_level_max_entries * txEntrySize
            else:
                offset = prev_level_max_entries * txEntrySize

            pending_updates[level] = cur_level_data[:offset]
            cur_level_data = cur_level_data[offset:]

        cur_level_max_entries = prev_level_max_entries

    pending_updates[0] = cur_level_data
    if len(cur_level_data) == 0:
        lowest_empty_level = 0

    # When the highest loaded level is empty, it's possible the level after
    # it still has data and thus that data needs to be backfilled as well.
    while len(pending_updates[highest_loaded_level]) == 0:
        # When the next level is empty too, the is no data left to
        # continue backfilling, so there is nothing left to do.
        # Otherwise, populate the pending updates map with the newly
        # loaded data and update the highest loaded level accordingly.

        level = highest_loaded_level + 1
        cur_level_key = key_for_level(addr_key, level)
        level_data = bucket.get(cur_level_key)
        if len(level_data) == 0:
            break

        pending_updates[level] = level_data
        highest_loaded_level = level

        # At this point the highest level is not empty, but it might
        # be half full.  When that is the case, move it up a level to
        # simplify the code below which backfills all lower levels that
        # are still empty.  This also means the current level will be
        # empty, so the loop will perform another another iteration to
        # potentially backfill this level with data from the next one.
        cur_level_max_entries = max_entries_for_level(level)
        if len(level_data) // txEntrySize != cur_level_max_entries:
            pending_updates[level] = bytes()
            pending_updates[level - 1] = level_data
            level -= 1
            cur_level_max_entries //= 2

        # Backfill all lower levels that are still empty by iteratively
        # halfing the data until the lowest empty level is filled.
        while level > lowest_empty_level:
            offset = cur_level_max_entries // 2 * txEntrySize
            pending_updates[level] = level_data[:offset]
            level_data = level_data[offset:]
            pending_updates[level - 1] = level_data
            level -= 1
            cur_level_max_entries //= 2

        # The lowest possible empty level is now the highest loaded
        # level.
        lowest_empty_level = highest_loaded_level

    # Apply the pending updates
    return apply_pending()


def db_fetch_addr_index_entries(bucket: InternalBucket, addr_key: bytes, num_to_skip: int, num_requested: int,
                                reverse: bool, fetch_block_hash: typing.Callable) -> ([database.BlockRegion], int):
    pass


# writeIndexData represents the address index data to be written for one block.
# It consists of the address mapped to an ordered list of the transactions
# that involve the address in block.  It is ordered so the transactions can be
# stored in the order they appear in the block.
class WriteIndexData(dict):
    pass


# errUnsupportedAddressType is an error that is used to signal an
# unsupported address type has been
#  used.
class UnsupportedAddressType(Exception):
    pass


class AddrIndex(Indexer, NeedsInputser):
    def __init__(self, db: database.DB, chain_params: chaincfg.Params,
                 unconfirmed_lock: pyutil.RWLock, txns_by_addr: dict, addrs_by_tx: dict):
        # The following fields are set when the instance is created and can't
        # be changed afterwards, so there is no need to protect them with a
        # separate mutex.
        self.db = db
        self.chain_params = chain_params

        # The following fields are used to quickly link transactions and
        # addresses that have not been included into a block yet when an
        # address index is being maintained.  The are protected by the
        # unconfirmedLock field.
        #
        # The txnsByAddr field is used to keep an index of all transactions
        # which either create an output to a given address or spend from a
        # previous output to it keyed by the address.
        #
        # The addrsByTx field is essentially the reverse and is used to
        # keep an index of all addresses which a given transaction involves.
        # This allows fairly efficient updates when transactions are removed
        # once they are included into a block.
        self.unconfirmed_lock = unconfirmed_lock or pyutil.RWLock()
        self.txns_by_addr = txns_by_addr
        self.addrs_by_tx = addrs_by_tx

    # NeedsInputs signals that the index requires the referenced inputs in order
    # to properly create the index.
    #
    # This implements the NeedsInputser interface.
    def need_inputs(self) -> bool:
        return True

    # Init is only provided to satisfy the Indexer interface as there is nothing to
    # initialize for this index.
    #
    # This is part of the Indexer interface.
    def init(self):
        return

    # Key returns the database key to use for the index as a byte slice.
    #
    # This is part of the Indexer interface.
    def key(self) -> bytes:
        return addrIndexKey

    # Name returns the human-readable name of the index.
    #
    # This is part of the Indexer interface.
    def name(self) -> str:
        return addrIndexName

    # Create is invoked when the indexer manager determines the index needs
    # to be created for the first time.  It creates the bucket for the address
    # index.
    #
    # This is part of the Indexer interface.
    def create(self, db_tx: database.Tx):
        db_tx.metadata().create_bucket(addrIndexKey)
        return

    # TOCHECK, the modify of data work?
    # indexPkScript extracts all standard addresses from the passed public key
    # script and maps each of them to the associated transaction using the passed
    # map.
    def index_pk_script(self, data: WriteIndexData, pk_script: bytes, tx_idx: int):
        # Nothing to index if the script is non-standard or otherwise doesn't
        # contain any addresses.
        try:
            _, addrs, _ = txscript.extract_pk_script_addrs(pk_script, self.chain_params)
        except Exception:
            return

        if len(addrs) == 0:
            return

        ret_data = copy.deepcopy(data)
        for addr in addrs:
            try:
                addr_key = addr_to_key(addr)
            except Exception:
                continue

            # TOCONSIDER why
            # Avoid inserting the transaction more than once.  Since the
            # transactions are indexed serially any duplicates will be
            # indexed in a row, so checking the most recent entry for the
            # address is enough to detect duplicates.
            indexed_txns = ret_data[addr_key]
            num_txns = len(indexed_txns)
            if num_txns > 0 and indexed_txns[-1] == tx_idx:
                continue

            indexed_txns.append(tx_idx)
            ret_data[addr_key] = indexed_txns

        return ret_data

        # TOCHECK, the modify of data work?

    # indexBlock extract all of the standard addresses from all of the transactions
    # in the passed block and maps each of them to the associated transaction using
    # the passed map.
    def index_block(self, data: WriteIndexData, block: btcutil.Block, stxos: [blockchain.SpentTxOut]):

        stox_index = 0
        for tx_idx, tx in enumerate(block.get_transactions()):
            # Coinbases do not reference any inputs.  Since the block is
            # required to have already gone through full validation, it has
            # already been proven on the first transaction in the block is
            # a coinbase.
            if tx_idx != 0:
                for _ in tx.get_msg_tx().tx_ins:
                    # We'll access the slice of all the
                    # transactions spent in this block properly
                    # ordered to fetch the previous input script.
                    pk_script = stxos[stox_index].pk_script
                    self.index_pk_script(data, pk_script, tx_idx)

                    # With an input indexed, we'll advance the
                    # stxo coutner.
                    stox_index += 1

            for tx_out in tx.get_msg_tx().tx_outs:
                self.index_pk_script(data, tx_out.pk_script, tx_idx)

        return

    # ConnectBlock is invoked by the index manager when a new block has been
    # connected to the main chain.  This indexer adds a mapping for each address
    # the transactions in the block involve.
    #
    # This is part of the Indexer interface.
    def connect_block(self, db_tx: database.Tx, block: btcutil.Block, stxos: [blockchain.SpentTxOut]):

        # The offset and length of the transactions within the serialized
        # block.
        tx_locs = block.tx_loc()

        # Get the internal block ID associated with the block.
        block_id = db_fetch_block_id_by_hash(db_tx, block.hash())

        # Build all of the address to transaction mappings in a local map.
        addrs_to_txns = WriteIndexData()
        self.index_block(addrs_to_txns, block, stxos)

        # Add all of the index entries for each address.
        addr_idx_bucket = db_tx.metadata().bucket(addrIndexKey)
        for addr_key, tx_idxs in addrs_to_txns.items():
            for tx_idx in tx_idxs:
                db_put_addr_index_entry(addr_idx_bucket, addr_key, block_id, tx_locs[tx_idx])
        return

    # DisconnectBlock is invoked by the index manager when a block has been
    # disconnected from the main chain.  This indexer removes the address mappings
    # each transaction in the block involve.
    #
    # This is part of the Indexer interface.
    def disconnect_block(self, db_tx: database.Tx, block: btcutil.Block, stxos: [blockchain.SpentTxOut]):
        # Build all of the address to transaction mappings in a local map.
        addrs_to_txns = WriteIndexData()
        self.index_block(addrs_to_txns, block, stxos)

        # Remove all of the index entries for each address.
        addr_idx_bucket = db_tx.metadata().bucket(addrIndexKey)
        for addr_key, tx_idxs in addrs_to_txns.items():
            db_remove_addr_index_entries(addr_idx_bucket, addr_key, len(tx_idxs))
        return

    # TxRegionsForAddress returns a slice of block regions which identify each
    # transaction that involves the passed address according to the specified
    # number to skip, number requested, and whether or not the results should be
    # reversed.  It also returns the number actually skipped since it could be less
    # in the case where there are not enough entries.
    #
    # NOTE: These results only include transactions confirmed in blocks.  See the
    # UnconfirmedTxnsForAddress method for obtaining unconfirmed transactions
    # that involve a given address.
    #
    # This function is safe for concurrent access.
    def tx_regions_for_address(self, db_tx: database.Tx, addr: btcutil.Address,
                               num_to_skip: int, num_requested: int, reverse: bool) -> ([database.BlockRegion], int):
        addr_key = addr_to_key(addr)

        regions = []
        skipped = 0

        # TOCHANGE here the api is fucking messy.
        def fn(db_tx: database.Tx):
            # Create closure to lookup the block hash given the ID using
            # the database transaction.
            def fetch_block_hash(id: bytes) -> chainhash.Hash:
                return db_fetch_block_hash_by_serialized_id(db_tx, id)

            addr_index_bucket = db_tx.metadata().bucket(addr_key)

            nonlocal regions, skipped
            regions, skipped = db_fetch_addr_index_entries(addr_index_bucket, addr_key, num_to_skip,
                                                           num_requested, reverse, fetch_block_hash)

        self.db.view(fn)

        return regions, skipped

    # indexUnconfirmedAddresses modifies the unconfirmed (memory-only) address
    # index to include mappings for the addresses encoded by the passed public key
    # script to the transaction.
    #
    # This function is safe for concurrent access.
    def index_unconfirmed_addresses(self, pk_script: bytes, tx: btcutil.Tx):
        # The error is ignored here since the only reason it can fail is if the
        # script fails to parse and it was already validated before being
        # admitted to the mempool.
        _, addrs, _ = txscript.extract_pk_script_addrs(pk_script, self.chain_params)

        for addr in addrs:

            addr_key = addr_to_key(addr)

            self.unconfirmed_lock.lock()

            # Add a mapping from the address to the transaction.
            if addr_key not in self.txns_by_addr:
                self.txns_by_addr[addr_key] = {}
            self.txns_by_addr[addr_key][tx.hash()] = tx

            # Add a mapping from the transaction to the address.
            if tx.hash() not in self.addrs_by_tx:
                self.addrs_by_tx[tx.hash()] = {}
            self.addrs_by_tx[tx.hash()][addr_key] = {}  # TOCHANGE should use set, not map like golang

            self.unconfirmed_lock.unlock()

        return

    # AddUnconfirmedTx adds all addresses related to the transaction to the
    # unconfirmed (memory-only) address index.
    #
    # NOTE: This transaction MUST have already been validated by the memory pool
    # before calling this function with it and have all of the inputs available in
    # the provided utxo view.  Failure to do so could result in some or all
    # addresses not being indexed.
    #
    # This function is safe for concurrent access.
    def add_unconfirmed_tx(self, tx: btcutil.Tx, utxo_view: blockchain.UtxoViewpoint):
        # Index addresses of all referenced previous transaction outputs.
        #
        # The existence checks are elided since this is only called after the
        # transaction has already been validated and thus all inputs are
        # already known to exist.
        for tx_in in tx.get_msg_tx().tx_ins:
            entry = utxo_view.lookup_entry(tx_in.previous_out_point)
            if not entry:
                # Ignore missing entries.  This should never happen
                # in practice since the function comments specifically
                # call out all inputs must be available.
                continue
            self.index_unconfirmed_addresses(entry.get_pk_script(), tx)

        # Index addresses of all created outputs.
        for tx_out in tx.get_msg_tx().tx_outs:
            self.index_unconfirmed_addresses(tx_out.pk_script, tx)

        return

    def remove_unconfirmed_tx(self):
        pass

    # UnconfirmedTxnsForAddress returns all transactions currently in the
    # unconfirmed (memory-only) address index that involve the passed address.
    # Unsupported address types are ignored and will result in no results.
    #
    # This function is safe for concurrent access.
    def unconfirmed_txns_for_address(self, addr: btcutil.Address) -> [btcutil.Tx] or None:
        addr_key = addr_to_key(addr)

        self.unconfirmed_lock.r_lock()
        try:

            if addr_key in self.txns_by_addr:
                txns = self.txns_by_addr[addr_key]
                return copy.deepcopy(txns)
            return None
        finally:
            self.unconfirmed_lock.r_unlock()


# addrToKey converts known address types to an addrindex key.  An error is
# returned for unsupported types.
def addr_to_key(addr: btcutil.Address) -> bytes:
    if isinstance(addr, btcutil.AddressPubKeyHash):
        return bytes([addrKeyTypePubKeyHash]) + addr.hash160()
    elif isinstance(addr, btcutil.AddressScriptHash):
        return bytes([addrKeyTypeScriptHash]) + addr.hash160()
    elif isinstance(addr, btcutil.AddressPubKey):
        return bytes([addrKeyTypePubKeyHash]) + addr.address_pub_key_hash().hash160()
    elif isinstance(addr, btcutil.AddressWitnessScriptHash):
        # P2WSH outputs utilize a 32-byte data push created by hashing
        # the script with sha256 instead of hash160. In order to keep
        # all address entries within the database uniform and compact,
        # we use a hash160 here to reduce the size of the salient data
        # push to 20-bytes.
        return bytes([addrKeyTypeWitnessScriptHash]) + pyutil.hash160(addr.script_address())
    elif isinstance(addr, btcutil.AddressWitnessPubKeyHash):
        return bytes([addrKeyTypeWitnessPubKeyHash]) + addr.hash160()
    else:
        raise UnsupportedAddressType("address type is not supported by the address index")
