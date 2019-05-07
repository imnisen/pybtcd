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

# addrIndexName is the human-readable name for the index.
addrIndexName = "address index"

# addrIndexKey is the key of the address index and the db bucket used
# to house it.
addrIndexKey = b"txbyaddridx"


# writeIndexData represents the address index data to be written for one block.
# It consists of the address mapped to an ordered list of the transactions
# that involve the address in block.  It is ordered so the transactions can be
# stored in the order they appear in the block.
class WriteIndexData(dict):
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


# TODO
def addr_to_key(addr: btcutil.Address) -> bytes:
    pass


def db_put_addr_index_entry(bucket: InternalBucket, addr_key: bytes, block_id: int, tx_loc: wire.TxLoc):
    pass


def db_remove_addr_index_entries(bucket: InternalBucket, addr_key: bytes, count: int):
    pass


def db_fetch_addr_index_entries(bucket: InternalBucket, addr_key: bytes, num_to_skip: int, num_requested: int,
                                reverse: bool, fetch_block_hash: typing.Callable) -> ([database.BlockRegion], int):
    pass
