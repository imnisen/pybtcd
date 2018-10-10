def list_equal(l1, l2):
    if len(l1) == len(l2):
        for i in range(len(l1)):
            if l1[i] != l2[i]:
                return False
        return True
    else:
        return False


# we can alse use binascii.hexlify(a).decode() to binay->hex string,
# but can't control holder
# In  : format_bytes(a, "0x", "02x", "")
# Out : '0x0102
def format_bytes(data, prefix="", holder="%x", separator=""):
    format_string = "{:s}" % holder
    return prefix + separator.join(format_string.format(x) for x in data)
