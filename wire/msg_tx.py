from .common import *

# MaxTxInSequenceNum is the maximum sequence number the sequence field
# of a transaction input can be.
MaxTxInSequenceNum = 0xffffffff

# minTxInPayload is the minimum payload size for a transaction input.
# PreviousOutPoint.Hash + PreviousOutPoint.Index 4 bytes + Varint for
# SignatureScript length 1 byte + Sequence 4 bytes.
minTxInPayload = 9 + HashSize

# MinTxOutPayload is the minimum payload size for a transaction output.
# Value 8 bytes + Varint for PkScript length 1 byte.
MinTxOutPayload = 9

# maxTxInPerMessage is the maximum number of transactions inputs that
# a transaction which fits into a message could possibly have.
maxTxInPerMessage = (MaxMessagePayload / minTxInPayload) + 1

# maxTxOutPerMessage is the maximum number of transactions outputs that
# a transaction which fits into a message could possibly have.
maxTxOutPerMessage = (MaxMessagePayload / MinTxOutPayload) + 1

# witnessMarkerBytes are a pair of bytes specific to the witness encoding. If
# this sequence is encoutered, then it indicates a transaction has iwtness
# data. The first byte is an always 0x00 marker byte, which allows decoders to
# distinguish a serialized transaction with witnesses from a regular (legacy)
# one. The second byte is the Flag field, which at the moment is always 0x01,
# but may be extended in the future to accommodate auxiliary non-committed
# fields.
witessMarkerBytes = bytes([0x00, 0x01])

# maxWitnessItemsPerInput is the maximum number of witness items to
# be read for the witness data for a single TxIn. This number is
# derived using a possble lower bound for the encoding of a witness
# item: 1 byte for length + 1 byte for the witness item itself, or two
# bytes. This value is then divided by the currently allowed maximum
# "cost" for a transaction.
maxWitnessItemsPerInput = 500000

# maxWitnessItemSize is the maximum allowed size for an item within
# an input's witness data. This number is derived from the fact that
# for script validation, each pushed item onto the stack must be less
# than 10k bytes.
maxWitnessItemSize = 11000


# TOCHANGE move to msgblock
# MaxBlockPayload is the maximum bytes a block message can be in bytes.
# After Segregated Witness, the max block payload has been raised to 4MB.
MaxBlockPayload = 4000000

class OutPoint:
    def __init__(self, hash: Hash, index: int):
        """

        :param chainhash.Hash hash:
        :param uint32 index:
        """
        self.hash = hash
        self.index = index

    def __str__(self):
        return self.hash.to_str() + str(self.index)

    def copy(self):
        return OutPoint(hash=self.hash, index=self.index)


class TxIn:
    def __init__(self, previous_out_point, signature_script, witness=None, sequence=MaxTxInSequenceNum):
        """

        :param OutPoint previous_out_point:
        :param []byte signature_script:
        :param TxWitness witness:
        :param uint32 sequence:
        """
        self.previous_out_point = previous_out_point
        self.signature_script = signature_script
        self.witness = witness or TxWitness()  # TOCHECK , I can't find this in bitcoin protocol wiki
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


# TxWitness : a txwitness is a list of witness for one tx input
# it's format:  varint + [(varint + bytes), ...]
class TxWitness:
    def __init__(self, data=None):
        """data is a list of list of bytes
        :param [][]byte uint32 data:
        """
        self._data = data or []

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

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return self._data


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
        :param uint32 lock_time:w
        """
        self.version = version
        self.tx_ins = tx_ins or []
        self.tx_outs = tx_outs or []
        self.lock_time = lock_time

    def btc_decode(self, s, pver, message_encoding):
        # read version
        self.version = read_element(s, "uint32")

        count = read_var_int(s, pver)

        # handle witness marker and flag
        flag = b''
        if count == 0 and message_encoding == WitnessEncoding:
            flag = read_variable_bytes(s, 1)
            if flag != b'\x01':
                raise WitnessTxFlagByteMsgErr

            count = read_var_int(s, pver)

        # check tx_inputs count
        if count > maxTxInPerMessage:
            raise MaxTxInPerMessageMsgErr

        # read tx_inputs
        self.tx_ins = []
        for i in range(count):
            self.tx_ins[i] = read_tx_in(s, pver, self.version)

        # check tx_outputs count
        count = read_var_int(s, pver)
        if count > maxTxOutPerMessage:
            raise MaxTxOutPerMessageMsgErr

        # read tx_outputs
        self.tx_outs = []
        for i in range(count):
            self.tx_outs[i] = read_tx_out(s, pver, self.version)

        # read tx_witness
        if flag != b'' and message_encoding == WitnessEncoding:
            for i in range(len(self.tx_ins)):
                self.tx_ins[i].witness = read_tx_witness(s, pver, self.version)

        # read lock_time
        self.lock_time = read_element(s, "uint32")

        # TOCHECK there are many optimize in the origin, consider need here.
        return

    def btc_encode(self, s, pver, message_encoding):
        # write version
        write_element(s, "uint32", self.version)

        do_witness = message_encoding == WitnessEncoding and self.hash_witness()

        # if witness mode, write bytes 0x00, 0x01
        if do_witness:
            s.write(witessMarkerBytes)

        # write count of tx_ins
        count = len(self.tx_ins)
        write_var_int(s, pver, count)

        # write list of tx_ins
        for tx_in in self.tx_ins:
            write_tx_in(s, pver, self.version, tx_in)

        # write count of tx_outs
        count = len(self.tx_outs)
        write_var_int(s, pver, count)

        # write list of tx_outs
        for tx_out in self.tx_outs:
            write_tx_out(s, pver, self.version, tx_out)

        # write witness
        if do_witness:
            for tx_in in self.tx_ins:
                write_tx_witness(s, pver, self.version, tx_in.witness)

        # write lock time
        write_element(s, "uint32", self.lock_time)
        return

    def command(self) -> str:
        return Commands.CmdTx

    def max_payload_length(self, pver: int) -> int:
        return MaxBlockPayload

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


def read_out_point(s, pver, version):
    hash = read_element(s, "chainhash.Hash")
    index = read_element(s, "uint32")
    return OutPoint(hash=hash, index=index)


def write_out_point(s, pver, version, op: OutPoint):
    write_element(s, "chainhash.Hash", op.hash)
    write_element(s, "uint32", op.index)
    return


def read_tx_in(s, pver, version):
    previous_out_point = read_out_point(s, pver, version)
    signature_script = read_script(s, pver, MaxMessagePayload, "transaction input signature script")
    sequence = read_element(s, "uint32")

    return TxIn(previous_out_point=previous_out_point,
                signature_script=signature_script,
                sequence=sequence)


def write_tx_in(s, pver, version, ti: TxIn):
    write_out_point(s, pver, version, ti.previous_out_point)
    write_script(s, pver, ti.signature_script)
    write_element(s, "uint32", ti.sequence)
    return


def read_tx_out(s, pver, version):
    value = read_element(s, "int64")
    pk_script = read_script(s, pver, MaxMessagePayload, "transaction output public key script")
    return TxOut(value=value, pk_script=pk_script)


def write_tx_out(s, pver, version, to: TxOut):
    write_element(s, "int64", to.value)
    write_script(s, pver, to.pk_script)
    return


def read_script(s, pver, max_allowed, field_name):
    count = read_var_int(s, pver)

    if count > max_allowed:
        raise ReadScriptTooLongMsgErr(field_name)

    return read_variable_bytes(s, count)


def write_script(s, pver, script_bytes):
    write_var_bytes(s, pver, script_bytes)
    return


# witness :  varint  [(varint + bytes), ...]
def read_tx_witness(s, pver, version):
    count = read_var_int(s, pver)

    if count > maxWitnessItemsPerInput:
        raise MaxWitnessItemsPerInputMsgErr

    data = []
    for _ in range(count):
        data.append(read_script(s, pver, maxWitnessItemSize, "script witness item"))
    return TxWitness(data=data)


def write_tx_witness(s, pver, version, wit: TxWitness):
    write_var_int(s, pver, len(wit))
    for item in wit:
        write_var_bytes(s, pver, item)
    return
