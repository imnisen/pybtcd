import chainhash
import btcutil
import txscript

# CheckpointConfirmations is the number of blocks before the end of the current
# best block chain that a good checkpoint candidate must be.
CheckpointConfirmations = 2016


def new_hash_from_str(hex_str: str) -> chainhash.Hash:
    try:
        hash = chainhash.Hash(str)
    except Exception:
        hash = chainhash.Hash()

    return hash


# isNonstandardTransaction determines whether a transaction contains any
# scripts which are not one of the standard types.
def is_nonstandard_transaction(tx: btcutil.Tx) -> bool:
    # Check all of the output public key scripts for non-standard scripts.
    for tx_out in tx.get_msg_tx().tx_outs:
        script_class = txscript.get_script_class(tx_out.pk_script)
        if script_class == txscript.ScriptClass.NonStandardTy:
            return True
    return False
