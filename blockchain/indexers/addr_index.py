import database
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
        self.unconfirmed_lock = unconfirmed_lock
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

    # TODO
    def tx_regions_for_addresses(self):
        pass

    def index_unconfirmed_addresses(self):
        pass

    def add_unconfirmed_tx(self):
        pass

    def remove_unconfirmed_tx(self):
        pass

    def unconfirmed_txns_for_addresses(self):
        pass


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
