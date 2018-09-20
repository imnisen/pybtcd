from .common import *

# MaxTxInSequenceNum is the maximum sequence number the sequence field
# of a transaction input can be.
MaxTxInSequenceNum = 0xffffffff


class OutPoint:
    def __init__(self, a_hash: Hash, index: int):
        self.hash = a_hash
        self.index = index

    def __str__(self):
        return self.hash.to_str() + str(self.index)

    def copy(self):
        return OutPoint(a_hash=self.hash, index=self.index)


class TxIn:
    def __init__(self, previous_out_point, signature_script, witness, sequence=MaxTxInSequenceNum):
        """

        :param OutPoint previous_out_point:
        :param []byte signature_script:
        :param TxWitness witness:
        :param uint32 sequence:
        """
        self.previous_out_point = previous_out_point
        self.signature_script = signature_script
        self.witness = witness  # TOCHECK , I can't find this in bitcoin protocol wiki
        self.sequence = sequence

    def serialize_size(self):
        # Outpoint Hash 32 bytes + Outpoint Index 4 bytes  -> outpoint
        # + serialized varint size for the length of SignatureScript -> signature script
        # + Sequence 4 bytes -> sequence

        # TOCHECK why not count self.witness?
        return 40 + var_int_serialize_size(len(self.signature_script)) + len(self.signature_script)

    def copy(self):
        return TxIn(previous_out_point=self.previous_out_point.copy(),
                    signature_script=self.signature_script[:],
                    witness=self.witness.copy(),
                    sequence=self.sequence)


# TOCHECK
class TxWitness:
    def __init__(self, data):
        """data is a list of list of bytes
        :param [][]byte uint32 data:
        """
        self._data = data

    def serialize_size(self):
        n = var_int_serialize_size(len(self._data))
        for d in self._data:
            n += var_int_serialize_size(len(d))
            n += len(d)
        return n

    def copy(self):
        new_data = []
        for d in self._data:
            new_data.append(d[:])
        return TxWitness(data=new_data)


class TxOut:
    def __init__(self, value, pk_script):
        """

        :param int64 value:
        :param []byte pk_script:
        """
        self.value = value
        self.pk_script = pk_script

    def serialize_size(self):
        # Value 8 bytes + serialized varint size for the length of PkScript +
        # PkScript bytes.
        return 8 + var_int_serialize_size(len(self.pk_script)) + len(self.pk_script)

    def copy(self):
        return TxOut(value=self.value,
                     pk_script=self.pk_script[:])


class MsgTx(Message):
    def __init__(self, version, tx_ins=None, tx_outs=None, lock_time=None):
        """

        :param uint32 version:
        :param TxIn[] tx_ins:
        :param Txout[] tx_outs:
        :param uint32 lock_time:
        """
        self.version = version
        self.tx_ins = tx_ins or []
        self.tx_outs = tx_outs or []
        self.lock_time = lock_time

    def btc_decode(self, s, pver, message_encoding):
        # self.version = read_element(s, "uint32")
        # TODO
        pass

    def btc_encode(self, s, pver, message_encoding):
        raise NotImplementedError

    def command(self) -> str:
        raise NotImplementedError

    def max_payload_length(self, pver: int) -> int:
        raise NotImplementedError

    def add_tx_in(self, ti):
        self.tx_ins.append(ti)

    def add_tx_out(self, to):
        self.tx_outs.append(to)

    def tx_hash(self):
        # TODO
        pass

    def witness_hash(self):
        pass

    def copy(self):

        # copy tx_ins
        new_tx_ins = []
        for old_tx_in in self.tx_ins:
            new_tx_ins.append(old_tx_in.copy())

        # copy tx_outs
        new_tx_outs = []
        for old_tx_out in self.tx_outs:
            new_tx_ins.append(old_tx_out.copy())

        return MsgTx(version=self.version, lock_time=self.lock_time,
                     tx_ins=new_tx_ins, tx_outs=new_tx_outs)

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
