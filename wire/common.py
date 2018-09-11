from chainhash import *


# MaxVarIntPayload is the maximum payload size for a variable length integer.
MaxVarIntPayload = 9

# TOADD add the fast dispatch. see origin binaryFreeList



BigEndian = "big"
LittleEndian = "little"


def read_element(s, element):
    pass


def read_elements(s, elements):
    pass


def write_element(s, element):
    pass


def write_elements(s, elements):
    pass


def read_var_int(s, pver):
    pass


def write_var_int(s, pver, val):
    pass


def var_int_serialize_size(val):
    pass


def read_var_string(s, pver):
    pass


def write_var_string(s, pver, string):
    pass


def read_var_bytes(s, pver, max_allowed, filed_name):
    pass


def write_var_byes(s, pver):
    pass


def _random_uint64():
    pass


def random_uint64():
    pass
