import btcutil
import blockchain


# TODO
def get_tx_virtual_size(tx: btcutil.Tx):
    pass


# TODO
def check_transaction_standard(tx: btcutil.Tx,
                               height: int,
                               median_time_past: int,
                               min_relay_tx_fee: btcutil.Amount,
                               max_tx_version: int):
    pass


# TODO
def check_inputs_stand(tx: btcutil.Tx, utxo_view: blockchain.UtxoViewpoint):
    pass


# TODO
def calc_min_required_tx_relay_fee(serialized_size: int, min_relay_tx_fee: btcutil.Amount) -> int:
    pass
