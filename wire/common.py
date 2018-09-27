import logging
import random
from .message import *
from .error import *

_logger = logging.Logger(__name__)

# MaxVarIntPayload is the maximum payload size for a variable length integer.
MaxVarIntPayload = 9

# TOADD add the fast dispatch. see origin binaryFreeList



BigEndian = "big"
LittleEndian = "little"

# message.py
# MaxMessagePayload is the maximum bytes a message can be regardless of other
# individual limits imposed by messages themselves.
MaxMessagePayload = (1024 * 1024 * 32)  # 32MB

# some math constant
MaxInt8 = (1 << 7) - 1
MinInt8 = (-1 << 7)
MaxInt16 = (1 << 15) - 1
MinInt16 = (-1 << 15)
MaxInt32 = (1 << 31) - 1
MinInt32 = (-1 << 31)
MaxInt64 = (1 << 63) - 1
MinInt64 = (-1 << 63)
MaxUint8 = (1 << 8) - 1
MaxUint16 = (1 << 16) - 1
MaxUint32 = (1 << 32) - 1
MaxUint64 = (1 << 64) - 1


def read_variable_bytes(s, bytes_len):
    return s.read(bytes_len)


def read_variable_bytes_as_integer(s, bytes_len, byteorder=LittleEndian):
    x = int.from_bytes(s.read(bytes_len), byteorder=byteorder)
    return x


def write_variable_bytes_from_integer(s, bytes_len, val, byteorder=LittleEndian):
    s.write(val.to_bytes(bytes_len, byteorder=byteorder))  # TOCHECK


def read_element(s, element_type):
    # The origin method accepts element,and dispatch how to read by the type of element,
    # after that, it change the value of element passed as params
    # However, as in python, I can't pass address and change value it point to
    # so, this methd will return value it reads.

    # On the other hand, since I cannot distinguish uint32 or int32 value in python,
    # SO I can only pass it's type with string formar and do dispatch on string

    # Notice, the return value is not exactly the same as element_type required,
    # since python is weak typed
    # So, the next operation after read_element may also need it's element_type

    if element_type == "int32":
        return read_variable_bytes_as_integer(s, 4, LittleEndian)
    elif element_type == "uint32":
        return read_variable_bytes_as_integer(s, 4, LittleEndian)
    elif element_type == "int64":
        return read_variable_bytes_as_integer(s, 8, LittleEndian)
    elif element_type == "uint64":
        return read_variable_bytes_as_integer(s, 8, LittleEndian)
    elif element_type == "bool":
        rv = read_variable_bytes_as_integer(s, 1)
        if rv == 0x00:
            return False
        else:
            return True
    elif element_type == "uint32Time":
        # Notice, here don't like origin, I just return the int, not the type timestamp
        return read_variable_bytes_as_integer(s, 4, LittleEndian)
    elif element_type == "int64Time":
        # Notice, here don't like origin, I just return the int, not the type timestamp
        return read_variable_bytes_as_integer(s, 8, LittleEndian)
    elif element_type == "[4]byte":  # TOCHANGE, this is a golang mark, maybe more common?
        return read_variable_bytes(s, 4)
    elif element_type == "[CommandSize]uint8":  # TOCHANGE, this is a golang mark, maybe more common?
        return read_variable_bytes(s, CommandSize)
    elif element_type == "[16]byte":
        return read_variable_bytes(s, 16)
    # elif element_type == "ipv6":
    #     b = read_variable_bytes(s, 16)
    #     # convert to ipaddress.ipv6
    #     return ipaddress.ip_address(b)
    elif element_type == "chainhash.Hash":
        return Hash(read_variable_bytes(s, HashSize))
    elif element_type == "ServiceFlag":
        return ServiceFlag.from_int(read_variable_bytes_as_integer(s, 8, LittleEndian))
    elif element_type == "services":
        return Services(ServiceFlag.from_int(read_variable_bytes_as_integer(s, 8, LittleEndian)))
    elif element_type == "InvType":
        return InvType.from_int(read_variable_bytes_as_integer(s, 4, LittleEndian))
    elif element_type == "BitcoinNet":
        return BitcoinNet.from_int(read_variable_bytes_as_integer(s, 4, LittleEndian))

    # elif element_type == "BloomUpdateType":
    #     pass

    # elif element_type == "RejectCode":
    #     pass
    else:
        _logger.info("Notice,in read_element, I don't know what to do here.")
        return s.read()


# def read_elements(s, elements):
#     pass


def write_element(s, element_type, element):
    if element_type == "int32":
        write_variable_bytes_from_integer(s, 4, element, LittleEndian)
    elif element_type == "uint32":
        write_variable_bytes_from_integer(s, 4, element, LittleEndian)
    elif element_type == "int64":
        write_variable_bytes_from_integer(s, 8, element, LittleEndian)
    elif element_type == "uint64":
        write_variable_bytes_from_integer(s, 8, element, LittleEndian)
    elif element_type == "bool":
        if element:
            write_variable_bytes_from_integer(s, 1, 0x01)
        else:
            write_variable_bytes_from_integer(s, 1, 0x00)
    elif element_type == "uint32Time":
        # Notice, here don't like origin, I just return the int, not the type timestamp
        return write_variable_bytes_from_integer(s, 4, element, LittleEndian)
    elif element_type == "int64Time":
        # Notice, here don't like origin, I just return the int, not the type timestamp
        return write_variable_bytes_from_integer(s, 8, element, LittleEndian)

    elif element_type == "[4]byte":  # TOCHANGE, this is a golang mark, maybe more common?
        s.write(element)
    elif element_type == "[CommandSize]uint8":  # TOCHANGE, this is a golang mark, maybe more common?
        s.write(element)
    elif element_type == "[16]byte":
        s.write(element)
    # elif element_type == "ipv6":
    #     # convert ipv6 -> 16 bytes
    #     s.write(element.packed)
    elif element_type == "chainhash.Hash":
        s.write(element.to_bytes())
    elif element_type == "ServiceFlag":
        write_variable_bytes_from_integer(s, 8, element.value[0], LittleEndian)
    elif element_type == "services":
        write_variable_bytes_from_integer(s, 8, element.value, LittleEndian)
    elif element_type == "InvType":
        write_variable_bytes_from_integer(s, 4, element.value[0], LittleEndian)
    elif element_type == "BitcoinNet":
        write_variable_bytes_from_integer(s, 4, element.value[0], LittleEndian)

    # elif element_type == "BloomUpdateType":
    #     pass

    # elif element_type == "RejectCode":
    #     pass
    else:
        _logger.info("Notice, in write_element I don't know what to do here.")
        return s.write(element)


# def write_elements(s, *elements):
#     pass


def read_var_int(s, pver):
    # read first byte from stream
    discriminant = read_variable_bytes_as_integer(s, 1)

    # Depends on first byte
    if discriminant == 0xff:
        rv = read_variable_bytes_as_integer(s, 8)
        min = 0x100000000
        if rv < min:
            raise NonCanonicalVarIntErr()
    elif discriminant == 0xfe:
        rv = read_variable_bytes_as_integer(s, 4)
        min = 0x10000
        if rv < min:
            raise NonCanonicalVarIntErr()
    elif discriminant == 0xfd:
        rv = read_variable_bytes_as_integer(s, 2)
        min = 0xfd
        if rv < min:
            raise NonCanonicalVarIntErr()
    else:
        rv = discriminant

    return rv


def write_var_int(s, pver, val):
    if val < 0xfd:
        write_variable_bytes_from_integer(s, 1, val)
    elif val <= MaxUint16:
        write_variable_bytes_from_integer(s, 1, 0xfd)
        write_variable_bytes_from_integer(s, 2, val)
    elif val <= MaxUint32:
        write_variable_bytes_from_integer(s, 1, 0xfe)
        write_variable_bytes_from_integer(s, 4, val)
    else:
        write_variable_bytes_from_integer(s, 1, 0xff)
        write_variable_bytes_from_integer(s, 8, val)
    return


def var_int_serialize_size(val: int) -> int:
    if val < 0xfd:
        size = 1
    elif val <= MaxUint16:
        size = 3
    elif val <= MaxUint32:
        size = 5
    else:
        size = 9
    return size


# when deal with length of string, always count on string bytes length
def read_var_string(s, pver):
    count = read_var_int(s, pver)

    if count > MaxMessagePayload:
        raise MessageLengthTooLongErr

    buf = s.read(count)  # TOCHECK if here we can read count of bytes
    return buf.decode()


def write_var_string(s, pver, string):
    string_byte = string.encode()
    write_var_int(s, pver, len(string_byte))
    s.write(string_byte)
    return


def read_var_bytes(s, pver, max_allowed, filed_name):
    count = read_var_int(s, pver)
    if count > max_allowed:
        raise BytesTooLargeErr(
            "{} is larger than the max allowed size [count {}, max {}".format(filed_name, count, max_allowed))
    buf = s.read(count)
    return buf


def write_var_bytes(s, pver, some_bytes):
    write_var_int(s, pver, len(some_bytes))
    s.write(some_bytes)
    return


def random_uint64():
    # TOCHECK, since int has no type in python, leave a note here and decide what to do next
    return random.getrandbits(64)
