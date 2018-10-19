import io
from .common import *
from chainhash.hashfuncs import *

# MaxTxInSequenceNum is the maximum sequence number the sequence field
# of a transaction input can be.
MaxTxInSequenceNum = 0xffffffff


# SequenceLockTimeDisabled is a flag that if set on a transaction
# input's sequence number, the sequence number will not be interpreted
# as a relative locktime.
SequenceLockTimeDisabled = 1 << 31


# SequenceLockTimeIsSeconds is a flag that if set on a transaction
# input's sequence number, the relative locktime has units of 512
# seconds.
SequenceLockTimeIsSeconds = 1 << 22

# SequenceLockTimeMask is a mask that extracts the relative locktime
# when masked against the transaction input sequence number.
SequenceLockTimeMask = 0x0000ffff

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

# minTxPayload is the minimum payload size for a transaction.  Note
# that any realistically usable transaction must have at least one
# input or output, but that is a rule enforced at a higher layer, so
# it is intentionally not included here.
# Version 4 bytes + Varint number of transaction inputs 1 byte + Varint
# number of transaction outputs 1 byte + LockTime 4 bytes + min input
# payload + min output payload.
minTxPayload = 10


class OutPoint:
    def __init__(self, hash: Hash, index: int):
        """

        :param chainhash.Hash hash:
        :param uint32 index:
        """
        self.hash = hash
        self.index = index

    def __str__(self):
        return self.hash.to_str() + ":" + str(self.index)

    def copy(self):
        return OutPoint(hash=self.hash, index=self.index)

    def __eq__(self, other):
        return self.hash == other.hash and self.index == other.index


class TxIn:
    def __init__(self, previous_out_point, signature_script=None, witness=None, sequence=MaxTxInSequenceNum):
        """

        :param OutPoint previous_out_point:
        :param []byte signature_script:
        :param TxWitness witness:
        :param uint32 sequence:
        """
        self.previous_out_point = previous_out_point
        self.signature_script = signature_script or bytes()
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

    def __eq__(self, other):
        return self.previous_out_point == other.previous_out_point and \
               self.previous_out_point == other.previous_out_point and \
               self.signature_script == other.signature_script and \
               self.witness == other.witness and \
               self.sequence == other.sequence


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
        return iter(self._data)

    def __eq__(self, other):
        return self._data == other._data

    def __getitem__(self, index):
        return self._data[index]


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

    def __eq__(self, other):
        return self.value == other.value and \
               self.pk_script == other.pk_script


class MsgTx(Message):
    def __init__(self, version=None, tx_ins=None, tx_outs=None, lock_time=None):
        """

        :param uint32 version:
        :param TxIn[] tx_ins:
        :param Txout[] tx_outs:
        :param uint32 lock_time:w
        """
        self.version = version or 0
        self.tx_ins = tx_ins or []
        self.tx_outs = tx_outs or []
        self.lock_time = lock_time or 0

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
            self.tx_ins.append(read_tx_in(s, pver, self.version))

        # check tx_outputs count
        count = read_var_int(s, pver)
        if count > maxTxOutPerMessage:
            raise MaxTxOutPerMessageMsgErr

        # read tx_outputs
        self.tx_outs = []
        for i in range(count):
            self.tx_outs.append(read_tx_out(s, pver, self.version))

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

        do_witness = message_encoding == WitnessEncoding and self.has_witness()

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

    # TxHash generates the Hash for the transaction.
    def tx_hash(self):
        s = io.BytesIO()
        self.serialize_no_witness(s)
        return double_hash_h(s.getvalue())  # TOCHECK why hint str here

    def witness_hash(self):
        if self.has_witness():
            s = io.BytesIO()
            self.serialize(s)
            return double_hash_h(s.getvalue())  # TOCHECK why hint str here
        return self.tx_hash()

    def copy(self):

        # copy tx_ins
        new_tx_ins = []
        for old_tx_in in self.tx_ins:
            new_tx_ins.append(old_tx_in.copy())

        # copy tx_outs
        new_tx_outs = []
        for old_tx_out in self.tx_outs:
            new_tx_outs.append(old_tx_out.copy())

        return MsgTx(version=self.version, lock_time=self.lock_time,
                     tx_ins=new_tx_ins, tx_outs=new_tx_outs)

    # Deserialize decodes a transaction from r into the receiver using a format
    # that is suitable for long-term storage such as a database while respecting
    # the Version field in the transaction.  This function differs from BtcDecode
    # in that BtcDecode decodes from the bitcoin wire protocol as it was sent
    # across the network.  The wire encoding can technically differ depending on
    # the protocol version and doesn't even really need to match the format of a
    # stored transaction at all.  As of the time this comment was written, the
    # encoded transaction is the same in both instances, but there is a distinct
    # difference and separating the two allows the API to be flexible enough to
    # deal with changes.
    def deserialize(self, s):
        # At the current time, there is no difference between the wire encoding
        # at protocol version 0 and the stable long-term storage format.  As
        # a result, make use of BtcDecode.
        return self.btc_decode(s, pver=0, message_encoding=WitnessEncoding)

    # DeserializeNoWitness decodes a transaction from r into the receiver, where
    # the transaction encoding format within r MUST NOT utilize the new
    # serialization format created to encode transaction bearing witness data
    # within inputs.
    def deserialize_no_witness(self, s):
        return self.btc_decode(s, pver=0, message_encoding=BaseEncoding)

    # HasWitness returns false if none of the inputs within the transaction
    # contain witness data, true false otherwise.
    def has_witness(self):
        for tx_in in self.tx_ins:
            if len(tx_in.witness) != 0:
                return True
        return False

    # Serialize encodes the transaction to w using a format that suitable for
    # long-term storage such as a database while respecting the Version field in
    # the transaction.  This function differs from BtcEncode in that BtcEncode
    # encodes the transaction to the bitcoin wire protocol in order to be sent
    # across the network.  The wire encoding can technically differ depending on
    # the protocol version and doesn't even really need to match the format of a
    # stored transaction at all.  As of the time this comment was written, the
    # encoded transaction is the same in both instances, but there is a distinct
    # difference and separating the two allows the API to be flexible enough to
    # deal with changes.
    def serialize(self, s):
        # At the current time, there is no difference between the wire encoding
        # at protocol version 0 and the stable long-term storage format.  As
        # a result, make use of BtcEncode.
        #
        # Passing a encoding type of WitnessEncoding to BtcEncode for MsgTx
        # indicates that the transaction's witnesses (if any) should be
        # serialized according to the new serialization structure defined in
        # BIP0144.

        return self.btc_encode(s, pver=0, message_encoding=WitnessEncoding)

    # SerializeNoWitness encodes the transaction to w in an identical manner to
    # Serialize, however even if the source transaction has inputs with witness
    # data, the old serialization format will still be used.
    def serialize_no_witness(self, s):
        return self.btc_encode(s, pver=0, message_encoding=BaseEncoding)

    # baseSize returns the serialized size of the transaction without accounting
    # for any witness data.
    def base_size(self):
        # Version 4 bytes + LockTime 4 bytes + Serialized varint size for the
        # number of transaction inputs and outputs.

        n = 8 + var_int_serialize_size(len(self.tx_ins)) + var_int_serialize_size(len(self.tx_outs))

        for tx_in in self.tx_ins:
            n += tx_in.serialize_size()

        for tx_out in self.tx_outs:
            n += tx_out.serialize_size()
        return n

    # SerializeSize returns the number of bytes it would take to serialize the
    # the transaction.
    def serialize_size(self):
        n = self.base_size()

        if self.has_witness():

            # count marker + flag
            n += 2

            for tx_in in self.tx_ins:
                n += tx_in.witness.serialize_size()
        return n

    # SerializeSizeStripped returns the number of bytes it would take to serialize
    # the transaction, excluding any included witness data.
    def serialize_size_stripped(self):
        return self.base_size()

    # PkScriptLocs returns a slice containing the start of each public key script
    # within the raw serialized transaction.  The caller can easily obtain the
    # length of each script by using len on the script available via the
    # appropriate transaction output entry.
    def pk_script_locs(self):
        if len(self.tx_outs) == 0:
            return []

        # The starting offset in the serialized transaction of the first
        # transaction output is:
        #
        # Version 4 bytes + serialized varint size for the number of
        # transaction inputs and outputs + serialized size of each transaction
        # input.
        n = 4 + var_int_serialize_size(len(self.tx_ins)) + var_int_serialize_size(len(self.tx_outs))

        if len(self.tx_ins) > 0 and len(self.tx_ins[0].witness) > 0:
            n += 2

        for tx_in in self.tx_ins:
            n += tx_in.serialize_size()

        pk_script_locs = []
        for tx_out in self.tx_outs:
            # The offset of the script in the transaction output is:
            #
            # Value 8 bytes + serialized varint size for the length of
            # PkScript.
            n += 8 + var_int_serialize_size(len(tx_out.pk_script))
            pk_script_locs.append(n)
            n += len(tx_out.pk_script)
        return pk_script_locs

    def __eq__(self, other):
        if self.version == other.version and self.lock_time == other.lock_time and \
                        len(self.tx_ins) == len(other.tx_ins) and len(self.tx_outs) == len(other.tx_outs):
            for i in range(len(self.tx_ins)):
                if self.tx_ins[i] != other.tx_ins[i]:
                    return False

            for i in range(len(self.tx_outs)):
                if self.tx_outs[i] != other.tx_outs[i]:
                    return False

            return True
        else:
            return False


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
