def read_variable_bytes_as_integer(s, v):
    return int.from_bytes(s.read(v), byteorder="little")

class MessageErr(Exception):
    pass
class NonCanonicalVarIntErr(MessageErr):
    pass

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

