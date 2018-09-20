from .common import *


class OutPoint:
    def __init__(self, a_hash: Hash, index: int):
        self.hash = a_hash
        self.index = index

    def __str__(self):
        pass


class TxIn:
    def __init__(self, previous_out_point, signature_script, witness, sequence):
        self.previous_out_point = previous_out_point
        self.signature_script = signature_script
        self.witness = witness  # TOCHECK , I can't find this in bitcoin protocol wiki
        self.sequence = sequence

    def serialize_size(self):
        pass


class TxWitness:
    def __init__(self, data):
        self._data = data

    def serialize_size(self):
        pass


class TxOut:
    def __init__(self, value, pk_script):
        self.value = value
        self.pk_script = pk_script


class MsgTx(Message):
    def __init__(self, version, tx_in, tx_out, lock_time):
        self.version = version
        self.tx_in = tx_in
        self.tx_out = tx_out
        self.lock_time = lock_time

    def btc_decode(self, s, pver, message_encoding):
        raise NotImplementedError

    def btc_encode(self, s, pver, message_encoding):
        raise NotImplementedError

    def command(self) -> str:
        raise NotImplementedError

    def max_payload_length(self, pver: int) -> int:
        raise NotImplementedError

    def add_tx_in(self, ti):
        pass

    def add_tx_out(self, to):
        pass

    def tx_hash(self):
        pass

    def witness_hash(self):
        pass

    def copy(self):
        pass

    def deserialize(self, r):
        pass

    def deserialize_no_witness(self):
        pass

    def hash_witness(self):
        pass

    def serialize(self):
        pass

    def serialize_no_witness(self):
        pass

    def base_size(self):
        pass

    def serialize_size(self):
        pass

    def serialize_size_stripped(self):
        pass

    def pk_script_locs(self):
        pass
