import chainhash
import wire
import txscript
import btcutil
from .validate import *


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
        self.the_amount = amount or 0

        # The public key script for the output.
        self.the_pk_script = pk_script or bytes()

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
    def amount(self):
        return self.the_amount

    # PkScript returns the public key script for the output.
    def pk_script(self):
        return self.the_pk_script

    # Clone returns a shallow copy of the utxo entry.
    def clone(self):
        return UtxoEntry(
            amount=self.the_amount,
            pk_script=self.the_pk_script,
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

        :param dict(wire.OutPoint -> UtxoEntry) entries:
        :param chainhash.Hash best_hash:
        """
        self.entries = entries or {}
        self.the_best_hash = best_hash or chainhash.Hash()

    # BestHash returns the hash of the best block in the chain the view currently
    # respresents.
    def best_hash(self) -> chainhash.hash:
        return self.the_best_hash

    # SetBestHash sets the hash of the best block in the chain the view currently
    # respresents.
    def set_best_hash(self, hash: chainhash.Hash):
        self.the_best_hash = hash

    # LookupEntry returns information about a given transaction output according to
    # the current state of the view.  It will return nil if the passed output does
    # not exist in the view or is otherwise not available such as when it has been
    # disconnected during a reorg.
    def lookup_entry(self, outpoint: wire.OutPoint):
        return self.entries.get(outpoint)

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

        entry.the_amount = tx_out.value
        entry.the_pk_script = tx_out.pk_script
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
