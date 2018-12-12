import chainhash
import wire
import txscript
import btcutil
from .validate import *
from .stxo import *

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
    def block_height(self) -> int:
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


# UtxoViewpoint represents a view into the set of unspent transaction outputs
# from a specific point of view in the chain.  For example, it could be for
# the end of the main chain, some point in the history of the main chain, or
# down a side chain.
#
# The unspent outputs are needed by other transactions for things such as
# script validation and double spend prevention.
class UtxoViewpoint:
    def __init__(self, entries: dict=None, best_hash: chainhash.Hash=None):
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
        for outpoint, entry in self.entries.items():
            if entry is None or (entry.is_modified and entry.is_spent()):
                del self.entries[outpoint]
                continue

            entry.packed_flags ^= tfModified  # Tocheck the xor operator

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
        self._add_tx_out(prev_out, tx_out, is_coin_base(tx), block_height)

        return

    # AddTxOuts adds all outputs in the passed transaction which are not provably
    # unspendable to the view.  When the view already has entries for any of the
    # outputs, they are simply marked unspent.  All fields will be updated for
    # existing entries since it's possible it has changed during a reorg.
    def add_tx_outs(self, tx: btcutil.Tx, block_height: int):
        coin_base_p = is_coin_base(tx)
        prev_out = wire.OutPoint(hash=tx.hash(), index=0)
        for idx, tx_out in enumerate(tx.get_msg_tx().tx_outs):
            # Update existing entries.  All fields are updated because it's
            # possible (although extremely unlikely) that the existing
            # entry is being replaced by a different transaction with the
            # same hash.  This is allowed so long as the previous
            # transaction is fully spent.
            prev_out.index = idx
            self._add_tx_out(prev_out, tx_out, coin_base_p, block_height)
        return

    # TODO
    # connectTransaction updates the view by adding all new utxos created by the
    # passed transaction and marking all utxos that the transactions spend as
    # spent.  In addition, when the 'stxos' argument is not nil, it will be updated
    # to append an entry for each spent txout.  An error will be returned if the
    # view does not contain the required utxos.
    def connect_transaction(self, tx:btcutil.Tx, block_height:int, stxos: [SpentTxOut]):
        pass

    # connectTransactions updates the view by adding all new utxos created by all
    # of the transactions in the passed block, marking all utxos the transactions
    # spend as spent, and setting the best hash for the view to the passed block.
    # In addition, when the 'stxos' argument is not nil, it will be updated to
    # append an entry for each spent txout.
    def connect_transactions(self):
        pass

    # fetchEntryByHash attempts to find any available utxo for the given hash by
    # searching the entire set of possible outputs for the given hash.  It checks
    # the view first and then falls back to the database if needed.
    def fetch_entry_by_hash(self):
        pass

    # disconnectTransactions updates the view by removing all of the transactions
    # created by the passed block, restoring all utxos the transactions spent by
    # using the provided spent txo information, and setting the best hash for the
    # view to the block before the passed block.
    def disconnect_transactions(self):
        pass

    # fetchUtxosMain fetches unspent transaction output data about the provided
    # set of outpoints from the point of view of the end of the main chain at the
    # time of the call.
    #
    # Upon completion of this function, the view will contain an entry for each
    # requested outpoint.  Spent outputs, or those which otherwise don't exist,
    # will result in a nil entry in the view.
    def fetch_utxos_main(self):
        pass

    # fetchUtxos loads the unspent transaction outputs for the provided set of
    # outputs into the view from the database as needed unless they already exist
    # in the view in which case they are ignored.
    def fetch_utxos(self):
        pass

    # fetchInputUtxos loads the unspent transaction outputs for the inputs
    # referenced by the transactions in the given block into the view from the
    # database as needed.  In particular, referenced entries that are earlier in
    # the block are added to the view and entries that are already in the view are
    # not modified.
    def fetch_input_utxos(self):
        pass



    