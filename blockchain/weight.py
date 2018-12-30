from .utxo_viewpoint import *


# GetBlockWeight computes the value of the weight metric for a given block.
# Currently the weight metric is simply the sum of the block's serialized size
# without any witness data scaled proportionally by the WitnessScaleFactor,
# and the block's serialized size including any witness data.
def get_block_weight(blk: btcutil.Block) -> int:
    msg_block = blk.get_msg_block()
    base_size = msg_block.serialize_size_stripped()
    total_size = msg_block.serialize_size()

    # (baseSize * 3) + totalSize
    return (base_size * (WitnessScaleFactor - 1)) + total_size


# GetTransactionWeight computes the value of the weight metric for a given
# transaction. Currently the weight metric is simply the sum of the
# transactions's serialized size without any witness data scaled
# proportionally by the WitnessScaleFactor, and the transaction's serialized
# size including any witness data.
def get_transaction_weight(tx: btcutil.Tx) -> int:
    msg_tx = tx.get_msg_tx()

    base_size = msg_tx.serialize_size_stripped()
    total_size = msg_tx.serialize_size()

    # (baseSize * 3) + totalSize
    return (base_size * (WitnessScaleFactor - 1)) + total_size


# CountSigOps returns the number of signature operations for all transaction
# input and output scripts in the provided transaction.  This uses the
# quicker, but imprecise, signature operation counting mechanism from
# txscript.
def count_sig_ops(tx: btcutil.Tx) -> int:
    msg_tx = tx.get_msg_tx()

    # Accumulate the number of signature operations in all transaction
    # inputs
    total_sig_ops = 0
    for tx_in in msg_tx.tx_ins:
        num_sig_ops = txscript.get_sig_op_count(tx_in.signature_script)
        total_sig_ops += num_sig_ops

    # Accumulate the number of signature operations in all transaction
    # outputs.
    for tx_out in msg_tx.tx_outs:
        num_sig_ops = txscript.get_sig_op_count(tx_out.pk_script)
        total_sig_ops += num_sig_ops

    return total_sig_ops


# CountP2SHSigOps returns the number of signature operations for all input
# transactions which are of the pay-to-script-hash type.  This uses the
# precise, signature operation counting mechanism from the script engine which
# requires access to the input transaction scripts.
def count_p2sh_sig_ops(tx: btcutil.Tx, is_coin_base_tx_p: bool, utxo_view: UtxoViewpoint) -> int:
    # Coinbase transactions have no interesting inputs.
    if is_coin_base_tx_p:
        return 0

    # Accumulate the number of signature operations in all transaction
    # inputs.
    msg_tx = tx.get_msg_tx()
    total_sig_ops = 0

    for i, tx_in in enumerate(msg_tx.tx_ins):

        # Ensure the referenced input transaction is available.
        utxo = utxo_view.lookup_entry(tx_in.previous_out_point)
        if utxo is None or utxo.is_spent():
            msg = ("output %s referenced from " +
                   "transaction %s:%d either does not exist or " +
                   "has already been spent") % (tx_in.previous_out_point, tx.hash(), i)
            raise RuleError(ErrorCode.ErrMissingTxOut, msg)

        # We're only interested in pay-to-script-hash types, so skip
        # this input if it's not one.
        pk_script = utxo.get_pk_script()
        if not txscript.is_pay_to_script_hash(pk_script):
            continue

        # Count the precise number of signature operations in the
        # referenced public key script.
        sig_script = tx_in.signature_script
        num_sig_ops = txscript.get_precise_sig_op_count(sig_script, pk_script, bip16=True)

        # We could potentially overflow the accumulator so check for
        # overflow.
        # In python no need
        total_sig_ops += num_sig_ops

    return total_sig_ops


# GetSigOpCost returns the unified sig op cost for the passed transaction
# respecting current active soft-forks which modified sig op cost counting.
# The unified sig op cost for a transaction is computed as the sum of: the
# legacy sig op count scaled according to the WitnessScaleFactor, the sig op
# count for all p2sh inputs scaled by the WitnessScaleFactor, and finally the
# unscaled sig op count for any inputs spending witness programs.
def get_sig_op_cost(tx: btcutil.Tx, is_coin_base_p: bool, utxo_view: UtxoViewpoint,
                    bip16_p: bool, seg_wit_p: bool) -> int:
    num_sig_ops = count_sig_ops(tx) * WitnessScaleFactor
    if bip16_p:
        num_p2sh_sig_ops = count_p2sh_sig_ops(tx, is_coin_base_p, utxo_view)
        num_sig_ops += num_p2sh_sig_ops * WitnessScaleFactor

    if seg_wit_p and not is_coin_base_p:
        msg_tx = tx.get_msg_tx()
        for i, tx_in in enumerate(msg_tx.tx_ins):
            # Ensure the referenced output is available and hasn't
            # already been spent.
            utxo = utxo_view.lookup_entry(tx_in.previous_out_point)
            if utxo is None or utxo.is_spent():
                msg = ("output %s referenced from " +
                       "transaction %s:%d either does not " +
                       "exist or has already been spent") % (
                          tx_in.previous_out_point, tx.hash(), i
                      )

                raise RuleError(ErrorCode.ErrMissingTxOut, msg)

            witness = tx_in.witness
            sig_script = tx_in.signature_script
            pk_script = utxo.pk_script
            num_sig_ops += txscript.get_witness_sig_op_count(sig_script, pk_script, witness)
    return num_sig_ops
