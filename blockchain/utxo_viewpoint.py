import chainhash
from .stxo import *
from .utxo import *


# UtxoViewpoint represents a view into the set of unspent transaction outputs
# from a specific point of view in the chain.  For example, it could be for
# the end of the main chain, some point in the history of the main chain, or
# down a side chain.
#
# The unspent outputs are needed by other transactions for things such as
# script validation and double spend prevention.
class UtxoViewpoint:
    def __init__(self, entries: dict = None, best_hash: chainhash.Hash = None):
        """

        :param dict of wire.OutPoint: UtxoEntry entries:
        :param chainhash.Hash best_hash:
        """
        self.entries = entries or {}
        self.best_hash = best_hash or chainhash.Hash()

    # BestHash returns the hash of the best block in the chain the view currently
    # respresents.
    def get_best_hash(self) -> chainhash.hash:
        return self.best_hash

    # SetBestHash sets the hash of the best block in the chain the view currently
    # respresents.
    def set_best_hash(self, hash: chainhash.Hash):
        self.best_hash = hash

    # LookupEntry returns information about a given transaction output according to
    # the current state of the view.  It will return nil if the passed output does
    # not exist in the view or is otherwise not available such as when it has been
    # disconnected during a reorg.
    def lookup_entry(self, outpoint: wire.OutPoint) -> UtxoEntry or None:
        return self.entries.get(outpoint)

    # RemoveEntry removes the given transaction output from the current state of
    # the view.  It will have no effect if the passed output does not exist in the
    # view.
    def remove_entry(self, outpoint: wire.OutPoint):
        del self.entries[outpoint]
        return

    # Entries returns the underlying map that stores of all the utxo entries.
    def get_entries(self):
        return self.entries

    # commit prunes all entries marked modified that are now fully spent and marks
    # all entries as unmodified.
    def commit(self):
        # # Due to: `RuntimeError: dictionary changed size during iteration`
        # for outpoint, entry in self.entries.items():
        #     if entry is None or (entry.is_modified and entry.is_spent()):
        #         del self.entries[outpoint]
        #         continue
        #
        #     entry.packed_flags ^= tfModified  # Tocheck the xor operator

        new_entries = {}
        for outpoint, entry in self.entries.items():
            if entry is None or (entry.is_modified and entry.is_spent()):
                continue

            entry.packed_flags ^= tfModified  # Tocheck the xor operator
            new_entries[outpoint] = entry
        self.entries = new_entries

        return

    # addTxOut adds the specified output to the view if it is not provably
    # unspendable.  When the view already has an entry for the output, it will be
    # marked unspent.  All fields will be updated for existing entries since it's
    # possible it has changed during a reorg.
    def _add_tx_out(self, outpoint: wire.OutPoint, tx_out: wire.TxOut, is_coin_base: bool, block_height: int):
        # Don't add provably unspendable outputs.
        if txscript.is_unspendabe(tx_out.pk_script):
            return

        # Update existing entries.  All fields are updated because it's
        # possible (although extremely unlikely) that the existing entry is
        # being replaced by a different transaction with the same hash.  This
        # is allowed so long as the previous transaction is fully spent.
        entry = self.lookup_entry(outpoint)
        if entry is None:
            entry = UtxoEntry()
            self.entries[outpoint] = entry

        entry.amount = tx_out.value
        entry.pk_script = tx_out.pk_script
        entry.block_height = block_height
        entry.packed_flags = tfModified

        if is_coin_base:
            entry.packed_flags |= tfCoinBase

        return

    # AddTxOut adds the specified output of the passed transaction to the view if
    # it exists and is not provably unspendable.  When the view already has an
    # entry for the output, it will be marked unspent.  All fields will be updated
    # for existing entries since it's possible it has changed during a reorg.
    def add_tx_out(self, tx: btcutil.Tx, tx_out_idx: int, block_height: int):
        # Can't add an output for an out of bounds index.
        if tx_out_idx >= len(tx.get_msg_tx().tx_outs):
            return

        # Update existing entries.  All fields are updated because it's
        # possible (although extremely unlikely) that the existing entry is
        # being replaced by a different transaction with the same hash.  This
        # is allowed so long as the previous transaction is fully spent.
        prev_out = wire.OutPoint(hash=tx.hash(), index=tx_out_idx)
        tx_out = tx.get_msg_tx().tx_outs[tx_out_idx]
        self._add_tx_out(prev_out, tx_out, tx.is_coin_base(), block_height)

        return

    # AddTxOuts adds all outputs in the passed transaction which are not provably
    # unspendable to the view.  When the view already has entries for any of the
    # outputs, they are simply marked unspent.  All fields will be updated for
    # existing entries since it's possible it has changed during a reorg.
    def add_tx_outs(self, tx: btcutil.Tx, block_height: int):
        coin_base_p = tx.is_coin_base()

        for idx, tx_out in enumerate(tx.get_msg_tx().tx_outs):
            # Update existing entries.  All fields are updated because it's
            # possible (although extremely unlikely) that the existing
            # entry is being replaced by a different transaction with the
            # same hash.  This is allowed so long as the previous
            # transaction is fully spent.
            prev_out = wire.OutPoint(hash=tx.hash(), index=idx)
            self._add_tx_out(prev_out, tx_out, coin_base_p, block_height)
        return

    # connectTransaction updates the view by adding all new utxos created by the
    # passed transaction and marking all utxos that the transactions spend as
    # spent.  In addition, when the 'stxos' argument is not nil, it will be updated
    # to append an entry for each spent txout.  An error will be returned if the
    # view does not contain the required utxos.
    def connect_transaction(self, tx: btcutil.Tx, block_height: int, stxos: [SpentTxOut]):
        """
        Notice: This method will change the passed `stxos`

        :param tx:
        :param block_height:
        :param stxos:
        :return:
        """
        # Coinbase transactions don't have any inputs to spend.
        if tx.is_coin_base():
            # Add the transaction's outputs as available utxos.
            self.add_tx_outs(tx, block_height)
            return

        # Spend the referenced utxos by marking them spent in the view and,
        # if a slice was provided for the spent txout details, append an entry
        # to it.
        for tx_in in tx.get_msg_tx().tx_ins:
            # Ensure the referenced utxo exists in the view.  This should
            # never happen unless there is a bug is introduced in the code.
            entry = self.entries.get(tx_in.previous_out_point)
            if entry is None:
                raise AssertError("view missing input %s" % tx_in.previous_out_point)

            # Only create the stxo details if requested.
            if stxos is not None:
                # Populate the stxo details using the utxo entry.
                stxo = SpentTxOut(
                    amount=entry.get_amount(),
                    pk_script=entry.get_pk_script(),
                    height=entry.get_block_height(),
                    is_coin_base=entry.is_coin_base()
                )
                stxos.append(stxo)

            # Mark the entry as spent.  This is not done until after the
            # relevant details have been accessed since spending it might
            # clear the fields from memory in the future.
            entry.spend()

        # Add the transaction's outputs as available utxos.
        self.add_tx_outs(tx, block_height)
        return

    # connectTransactions updates the view by adding all new utxos created by all
    # of the transactions in the passed block, marking all utxos the transactions
    # spend as spent, and setting the best hash for the view to the passed block.
    # In addition, when the 'stxos' argument is not nil, it will be updated to
    # append an entry for each spent txout.
    def connect_transactions(self, block: btcutil.Block, stxos: [SpentTxOut]):
        for tx in block.get_transactions():
            self.connect_transaction(tx, block.height(), stxos)

        # Update the best hash for view to include this block since all of its
        # transactions have been connected.
        self.set_best_hash(block.hash())
        return

    # fetchEntryByHash attempts to find any available utxo for the given hash by
    # searching the entire set of possible outputs for the given hash.  It checks
    # the view first and then falls back to the database if needed.
    def fetch_entry_by_hash(self, db: database.DB, hash: chainhash.Hash) -> UtxoEntry:
        # First attempt to find a utxo with the provided hash in the view.
        for idx in range(MaxOutputsPerBlock):
            prev_out = wire.OutPoint(hash=hash, index=idx)
            entry = self.lookup_entry(prev_out)
            if entry:
                return entry

        # Check the database since it doesn't exist in the view.  This will
        # often by the case since only specifically referenced utxos are loaded
        # into the view.
        entry = None

        def fn(db_tx: database.Tx):
            nonlocal entry
            entry = db_fetch_utxo_entry_by_hash(db_tx, hash)
            return

        db.view(fn)

        return entry

    # disconnectTransactions updates the view by removing all of the transactions
    # created by the passed block, restoring all utxos the transactions spent by
    # using the provided spent txo information, and setting the best hash for the
    # view to the block before the passed block.
    def disconnect_transactions(self, db: database.DB, block: btcutil.Block, stxos: [SpentTxOut]):
        # Sanity check the correct number of stxos are provided.
        if len(stxos) != count_spent_outputs(block):
            raise AssertError("disconnectTransactions called with bad spent transaction out information")

        # Loop backwards through all transactions so everything is unspent in
        # reverse order.  This is necessary since transactions later in a block
        # can spend from previous ones.
        stxo_idx = len(stxos) - 1
        transactions = block.get_transactions()
        for tx_idx in range(len(transactions) - 1, -1, -1):  # loop backwards
            tx = transactions[tx_idx]

            # All entries will need to potentially be marked as a coinbase
            packed_flags = TxoFlags(0)
            is_coin_base_p = (tx_idx == 0)
            if is_coin_base_p:
                packed_flags |= tfCoinBase

            # Mark all of the spendable outputs originally created by the
            # transaction as spent.  It is instructive to note that while
            # the outputs aren't actually being spent here, rather they no
            # longer exist, since a pruned utxo set is used, there is no
            # practical difference between a utxo that does not exist and
            # one that has been spent.
            #
            # When the utxo does not already exist in the view, add an
            # entry for it and then mark it spent.  This is done because
            # the code relies on its existence in the view in order to
            # signal modifications have happened.
            tx_hash = tx.hash()

            for tx_out_idx, tx_out in enumerate(tx.get_msg_tx().tx_outs):
                if txscript.is_unspendabe(tx_out.pk_script):
                    continue
                prev_out = wire.OutPoint(hash=tx_hash, index=tx_out_idx)
                entry = self.entries.get(prev_out)
                if not entry:
                    entry = UtxoEntry(
                        amount=tx_out.value,
                        pk_script=tx_out.pk_script,
                        block_height=block.height(),
                        packed_flags=packed_flags
                    )
                    self.entries[prev_out] = entry

                entry.spend()

            # Loop backwards through all of the transaction inputs (except
            # for the coinbase which has no inputs) and unspend the
            # referenced txos.  This is necessary to match the order of the
            # spent txout entries.
            if is_coin_base_p:
                continue

            for tx_in_idx in range(len(tx.get_msg_tx().tx_ins) - 1, -1, -1):  # loop backwards
                # Ensure the spent txout index is decremented to stay
                # in sync with the transaction input.
                stxo = stxos[stxo_idx]
                stxo_idx -= 1

                # When there is not already an entry for the referenced
                # output in the view, it means it was previously spent,
                # so create a new utxo entry in order to resurrect it.
                origin_out = tx.get_msg_tx().tx_ins[tx_in_idx].previous_out_point
                entry = self.entries.get(origin_out)
                if not entry:
                    entry = UtxoEntry()
                    self.entries[origin_out] = entry

                # The legacy v1 spend journal format only stored the
                # coinbase flag and height when the output was the last
                # unspent output of the transaction.  As a result, when
                # the information is missing, search for it by scanning
                # all possible outputs of the transaction since it must
                # be in one of them.
                #
                # It should be noted that this is quite inefficient,
                # but it realistically will almost never run since all
                # new entries include the information for all outputs
                # and thus the only way this will be hit is if a long
                # enough reorg happens such that a block with the old
                # spend data is being disconnected.  The probability of
                # that in practice is extremely low to begin with and
                # becomes vanishingly small the more new blocks are
                # connected.  In the case of a fresh database that has
                # only ever run with the new v2 format, this code path
                # will never run.
                if stxo.height == 0:
                    utxo = self.fetch_entry_by_hash(db, tx_hash)
                    if utxo is None:
                        raise AssertError("unable to resurrect legacy stxo %s" % origin_out)

                    stxo.height = utxo.get_block_height()
                    stxo.is_coin_base = utxo.is_coin_base()

                # Restore the utxo using the stxo data from the spend
                # journal and mark it as modified.
                entry.amount = stxo.amount
                entry.pk_script = stxo.pk_script
                entry.block_height = stxo.height
                entry.packed_flags = tfModified
                if stxo.is_coin_base:
                    entry.packed_flags |= tfCoinBase

        # Update the best hash for view to the previous block since all of the
        # transactions for the current block have been disconnected.
        self.set_best_hash(block.get_msg_block().header.prev_block)
        return

    # fetchUtxosMain fetches unspent transaction output data about the provided
    # set of outpoints from the point of view of the end of the main chain at the
    # time of the call.
    #
    # Upon completion of this function, the view will contain an entry for each
    # requested outpoint.  Spent outputs, or those which otherwise don't exist,
    # will result in a nil entry in the view.
    def fetch_utxos_main(self, db: database.DB, outpoints: dict):
        """

        :param db:
        :param {wire.OutPoint:{}}outpoints:  # TOCHANGE outpoints struct  dict -> set
        :return:
        """
        # Nothing to do if there are no requested outputs.
        if len(outpoints) == 0:
            return

        # Load the requested set of unspent transaction outputs from the point
        # of view of the end of the main chain.
        #
        # NOTE: Missing entries are not considered an error here and instead
        # will result in nil entries in the view.  This is intentionally done
        # so other code can use the presence of an entry in the store as a way
        # to unnecessarily avoid attempting to reload it from the database.
        def fn(db_tx: database.Tx):
            for outpoint in outpoints.keys():
                entry = db_fetch_utxo_entry(db_tx, outpoint)
                self.entries[outpoint] = entry
            return
        db.view(fn)
        return

    # fetchUtxos loads the unspent transaction outputs for the provided set of
    # outputs into the view from the database as needed unless they already exist
    # in the view in which case they are ignored.
    def fetch_utxos(self, db: database.DB, outpoints: dict):
        """

        :param db:
        :param {wire.OutPoint:{}}outpoints:  # TOCHANGE outpoints struct  dict -> set
        :return:
        """
        # Nothing to do if there are no requested outputs.
        if len(outpoints) == 0:
            return

        # Filter entries that are already in the view.
        needed_set = {}
        for outpoint in outpoints.keys():
            # Already loaded into the current view.
            if self.entries.get(outpoint):
                continue

            needed_set[outpoint] = {}

        # Request the input utxos from the database.
        return self.fetch_utxos_main(db, needed_set)

    # fetchInputUtxos loads the unspent transaction outputs for the inputs
    # referenced by the transactions in the given block into the view from the
    # database as needed.  In particular, referenced entries that are earlier in
    # the block are added to the view and entries that are already in the view are
    # not modified.
    def fetch_input_utxos(self, db: database.DB, block: btcutil.Block):
        # Build a map of in-flight transactions because some of the inputs in
        # this block could be referencing other transactions earlier in this
        # block which are not yet in the chain.
        tx_in_flight = {}
        transactions = block.get_transactions()
        for i, tx in enumerate(transactions):
            tx_in_flight[tx.hash()] = i

        # Loop through all of the transaction inputs (except for the coinbase
        # which has no inputs) collecting them into sets of what is needed and
        # what is already known (in-flight).
        needed_set = {}
        for i, tx in enumerate(transactions[1:]):
            for tx_in in tx.get_msg_tx().tx_ins:
                # It is acceptable for a transaction input to reference
                # the output of another transaction in this block only
                # if the referenced transaction comes before the
                # current one in this block.  Add the outputs of the
                # referenced transaction as available utxos when this
                # is the case.  Otherwise, the utxo details are still
                # needed.
                #
                # NOTE: The >= is correct here because i is one less
                # than the actual position of the transaction within
                # the block due to skipping the coinbase.
                origin_hash = tx_in.previous_out_point.hash
                if origin_hash in tx_in_flight:
                    in_flight_idx = tx_in_flight[origin_hash]
                    if i >= in_flight_idx:
                        origin_tx = transactions[in_flight_idx]
                        self.add_tx_outs(origin_tx, block.height())
                        continue

                # Don't request entries that are already in the view
                # from the database.
                if self.entries.get(tx_in.previous_out_point):
                    continue

                needed_set[tx_in.previous_out_point] = {}

        # Request the input utxos from the database.
        return self.fetch_utxos_main(db, needed_set)


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
            # recycle_outpoint_key(key)
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


# countSpentOutputs returns the number of utxos the passed block spends.
def count_spent_outputs(block: btcutil.Block):
    # Exclude the coinbase transaction since it can't spend anything.
    num_spent = 0
    for tx in block.get_transactions()[1:]:
        num_spent += len(tx.get_msg_tx().tx_ins)
    return num_spent
