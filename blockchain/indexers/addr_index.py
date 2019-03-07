import database
import chaincfg
import pyutil


class AddrIndex:
    def __init__(self, db: database.DB, chain_params: chaincfg.Params,
                 unconfirmed_lock: pyutil.RWLock, txns_by_addr: dict, addrs_bt_tx: dict):
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
        self.addrs_bt_tx = addrs_bt_tx
