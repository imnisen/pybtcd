MaxInt8 = 1 << 7 - 1
MinInt8 = -1 << 7
MaxInt16 = 1 << 15 - 1
MinInt16 = -1 << 15
MaxInt32 = 1 << 31 - 1
MinInt32 = -1 << 31
MaxInt64 = 1 << 63 - 1
MinInt64 = -1 << 63
MaxUint8 = 1 << 8 - 1
MaxUint16 = 1 << 16 - 1
MaxUint32 = 1 << 32 - 1
MaxUint64 = 1 << 64 - 1


def read_variable_bytes_as_integer(s, v):
    return int.from_bytes(s.read(v), byteorder="little")


def write_variable_bytes_from_integer(s, v, val):
    return s.write(val.to_bytes(v, byteorder="little"))  # TOCHECK


class MessageErr(Exception):
    pass


class NonCanonicalVarIntErr(MessageErr):
    pass

class MessageLengthTooLongErr(MessageErr):
    pass


# var_int refer to https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer

def read_var_int(s, pver: int) -> int:
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
        rv = read_variable_bytes_as_integer(s, 4)
        min = 0xfd
        if rv < min:
            raise NonCanonicalVarIntErr()
    else:
        rv = discriminant

    return rv


def write_var_int(s, pver, val):
    if val < 0xfd:
        write_variable_bytes_from_integer(s, 1, val)
    elif val <= MaxInt16:
        write_variable_bytes_from_integer(s, 1, 0xfd)
        write_variable_bytes_from_integer(s, 2, val)
    elif val <= MaxInt32:
        write_variable_bytes_from_integer(s, 1, 0xf)
        write_variable_bytes_from_integer(s, 4, val)
    else:
        write_variable_bytes_from_integer(s, 1, 0xf)
        write_variable_bytes_from_integer(s, 8, val)
    return


def var_int_serialize_size(val: int) -> int:
    if val < 0xfd:
        size = 1
    elif val <= MaxInt16:
        size = 3
    elif val <= MaxInt32:
        size = 5
    else:
        size = 9
    return size

# message.py
# MaxMessagePayload is the maximum bytes a message can be regardless of other
# individual limits imposed by messages themselves.
MaxMessagePayload = (1024 * 1024 * 32) # 32MB

# when deal with length of string, always count on string bytes length
def read_var_string(s, pver):
    count = read_var_int(s, pver)

    if count > MaxMessagePayload:
        raise MessageLengthTooLongErr()

    buf = s.read(count)  # TOCHECK if here we can read count of bytes
    return buf.decode()

def write_var_string(s, pver, string):
    string_byte = string.encode()
    write_var_int(s, pver, len(string_byte))
    s.write(string_byte)
    return


