from .common import *


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
