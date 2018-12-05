import wire
import btcutil
import txscript
import pyutil
import time
from .utxo_viewpoint import *
from .error import *

import logging

_logger = logging.Logger(__name__)


class TxValidateItem:
    def __init__(self, tx_in_index: int, tx_in: wire.TxIn,
                 tx: btcutil.Tx, sig_hashes: txscript.TxSigHashes):
        self.tx_in_index = tx_in_index
        self.tx_in = tx_in
        self.tx = tx
        self.sig_hashes = sig_hashes


class TxValidator:
    def __init__(self, utxo_view: UtxoViewpoint, flags: txscript.ScriptFlags,
                 sig_cache: txscript.SigCache, hash_cache: txscript.HashCache):
        self.utxo_view = utxo_view
        self.flags = flags
        self.sig_cache = sig_cache
        self.hash_cache = hash_cache
        # self.validate_chan = None
        # self.quit_chan = None
        # self.result_chan = None

    # TOCHANGE make it parallel on multi core/processor
    def validate_handler(self, item: TxValidateItem):

        # Ensure the referenced input utxo is available.
        tx_in = item.tx_in
        utxo = self.utxo_view.lookup_entry(tx_in.previous_out_point)
        if utxo is None:
            msg = "unable to find unspent output %s referenced from transaction %s:%d" % (tx_in.previous_out_point,
                                                                                          item.tx.hash(),
                                                                                          item.tx_in_index)
            raise RuleError(ErrorCode.ErrMissingTxOut, msg)

        # Create a new script engine for the script pair.
        sig_script = tx_in.signature_script
        witness = tx_in.witness
        pk_script = utxo.pk_script()
        input_amount = utxo.amount()
        try:
            vm = txscript.new_engine(
                pk_script,
                item.tx.get_msg_tx(),
                item.tx_in_index,
                self.flags,
                self.sig_cache,
                item.sig_hashes,
                input_amount
            )
        except Exception as e:
            msg = "failed to parse input %s:%d which references output %s - %s (input witness %s, input script bytes %s, prev output script bytes %s)" \
                  % (
                      item.tx.hash(), item.tx_in_index, tx_in.previous_out_point,
                      e, witness, sig_script, pk_script
                  )
            raise RuleError(ErrorCode.ErrScriptMalformed, msg)

        # Execute the script pair.
        try:
            vm.execute()
        except Exception as e:
            msg = "failed to validate input %s:%d which references output %s - %s (input witness %s, input script bytes %s, prev output script bytes %s)" \
                  % (
                      item.tx.hash(), item.tx_in_index, tx_in.previous_out_point,
                      e, witness, sig_script, pk_script
                  )
            raise RuleError(ErrorCode.ErrScriptValidation, msg)

    # TOCHANGE make it parallel on multi core/processor
    def validate(self, items: [TxValidateItem]):
        if len(items) == 0:
            return

        for item in items:
            self.validate_handler(item)

        return


def validate_transaction_scripts(tx: btcutil.Tx, utxo_view: UtxoViewpoint, flags: txscript.ScriptFlags,
                                 sig_cache: txscript.SigCache, hash_cache: txscript.HashCache):
    # First determine if segwit is active according to the scriptFlags. If
    # it isn't then we don't need to interact with the HashCache.
    segwit_active = flags.has_flag(txscript.ScriptFlag.ScriptVerifyWitness)

    # If the hashcache doesn't yet has the sighash midstate for this
    # transaction, then we'll compute them now so we can re-use them
    # amongst all worker validation goroutines.
    if segwit_active and tx.get_msg_tx().has_witness() and not hash_cache.contain_hashes(tx.hash()):
        hash_cache.add_sig_hashes(tx.get_msg_tx())

    cached_hashes = txscript.TxSigHashes()
    if segwit_active and tx.get_msg_tx().has_witness():
        # The same pointer to the transaction's sighash midstate will
        # be re-used amongst all validation goroutines. By
        # pre-computing the sighash here instead of during validation,
        # we ensure the sighashes
        # are only computed once.
        cached_hashes = hash_cache.get_sig_hashes(tx.hash())

    # Collect all of the transaction inputs and required information for
    # validation.
    tx_ins = tx.get_msg_tx().tx_ins
    tx_val_items = []

    for tx_in_index, tx_in in enumerate(tx_ins):

        # Skip coinbase
        if tx_in.previous_out_point.index == pyutil.MaxUint32:
            continue

        tx_vi = TxValidateItem(
            tx_in_index=tx_in_index,
            tx_in=tx_in,
            tx=tx,
            sig_hashes=cached_hashes
        )
        tx_val_items.append(tx_vi)

    # Validate all of the inputs.
    validator = TxValidator(utxo_view=utxo_view, flags=flags, sig_cache=sig_cache, hash_cache=hash_cache)
    return validator.validate(tx_val_items)


def check_block_scripts(block: btcutil.Block, utxo_view: UtxoViewpoint,
                        script_flags: txscript.ScriptFlags,
                        sig_cache: txscript.SigCache, hash_cache: txscript.HashCache):
    # First determine if segwit is active according to the scriptFlags. If
    # it isn't then we don't need to interact with the HashCache.
    segwit_active = script_flags.has_flag(txscript.ScriptFlag.ScriptVerifyWitness)

    # num_inputs = 0
    # for tx in block.get_transactions():

    tx_val_items = []

    for tx in block.get_transactions():
        hash = tx.hash()

        # If the HashCache is present, and it doesn't yet contain the
        # partial sighashes for this transaction, then we add the
        # sighashes for the transaction. This allows us to take
        # advantage of the potential speed savings due to the new
        # digest algorithm (BIP0143).
        if segwit_active and tx.has_witness() and hash_cache is not None \
                and not hash_cache.contain_hashes(hash):
            hash_cache.add_sig_hashes(tx.get_msg_tx())

        cached_hashes = txscript.TxSigHashes()
        if segwit_active and tx.has_witness():
            if hash_cache is not None:
                cached_hashes = hash_cache.get_sig_hashes(hash)
            else:
                cached_hashes = txscript.TxSigHashes.from_msg_tx(tx)

        tx_ins = tx.get_msg_tx().tx_ins

        for tx_in_index, tx_in in enumerate(tx_ins):

            # Skip coinbase
            if tx_in.previous_out_point.index == pyutil.MaxUint32:
                continue

            tx_vi = TxValidateItem(
                tx_in_index=tx_in_index,
                tx_in=tx_in,
                tx=tx,
                sig_hashes=cached_hashes
            )
            tx_val_items.append(tx_vi)

    # Validate all of the inputs.
    validator = TxValidator(utxo_view=utxo_view, flags=script_flags, sig_cache=sig_cache, hash_cache=hash_cache)
    start = int(time.time())
    validator.validate(tx_val_items)
    elapsed = int(time.time()) - start
    _logger.info("block %s took %s to verify" % (block.hash(), elapsed))

    # If the HashCache is present, once we have validated the block, we no
    # longer need the cached hashes for these transactions, so we purge
    # them from the cache.
    if segwit_active and hash_cache is not None:
        for tx in block.get_transactions():
            if tx.get_msg_tx().has_witness():
                hash_cache.purge_sig_hashes(tx.hash())
    return
