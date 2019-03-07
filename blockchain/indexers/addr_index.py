import database
import chaincfg
import pyutil
from .common import *


# addrIndexName is the human-readable name for the index.
addrIndexName = "address index"

# addrIndexKey is the key of the address index and the db bucket used
# to house it.
addrIndexKey = b"txbyaddridx"

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
        raise addrIndexKey
    
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

    # TODO writeIndexData and indexPkScript


