import wire
import btcutil
import txscript
from .utxo_viewpoint import *


class TxValidateItem:
    def __init__(self, tx_in_index:int, tx_in: wire.TxIn,
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
        self.validate_chan = None  # TODO
        self.quit_chan = None
        self.result_chan = None




def check_block_scripts(*args):
    pass
