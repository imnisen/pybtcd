from .common import *

# InvWitnessFlag denotes that the inventory vector type is requesting,
# or sending a version which includes witness data.
InvWitnessFlag = 1 << 30


class InvType(Enum):
    InvTypeError = (0, "ERROR")
    InvTypeTx = (1, "MSG_TX")
    InvTypeBlock = (2, "MSG_BLOCK")
    InvTypeFilteredBlock = (3, "MSG_FILTERED_BLOCK")
    InvTypeWitnessBlock = (2 | InvWitnessFlag, "MSG_WITNESS_BLOCK")
    InvTypeWitnessTx = (1 | InvWitnessFlag, "MSG_WITNESS_TX")
    InvTypeFilteredWitnessBlock = (3 | InvWitnessFlag, "MSG_FILTERED_WITNESS_BLOCK")

    def __str__(self):
        return self.value[1]

    @classmethod
    def from_string(cls, s):
        for bitcoin_net in cls:
            if bitcoin_net.value[1] == s:
                return bitcoin_net
        raise ValueError(cls.__name__ + ' has no value matching "' + s + '"')

    @classmethod
    def from_int(cls, i):
        for flagService in cls:
            if flagService.value[0] == i:
                return flagService
        raise ValueError(cls.__name__ + ' has no value matching "' + str(i) + '"')

    def __eq__(self, other):
        if type(other) is InvType:
            return self.value[0] == other.value[0]
        elif type(other) is int:
            return self.value[0] == other
        elif type(other) is str:
            return self.value[1] == other
        else:
            return False


class InvVect:
    def __init__(self, inv_type, hash):
        self.inv_type = inv_type
        self.hash = hash

    def __eq__(self, other):
        if type(other) is InvVect:
            return self.inv_type == other.inv_type and self.hash == other.hash
        return False


def read_inv_vect(s, pver):
    inv_type = InvType.from_int(read_element(s, "uint32"))
    hash = read_element(s, "chainhash.Hash")
    return InvVect(inv_type=inv_type, hash=hash)


def write_inv_vect(s, pver, iv):
    write_element(s, "uint32", iv.inv_type.value[0])
    write_element(s, "chainhash.Hash", iv.hash)
