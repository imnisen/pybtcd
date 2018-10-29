
def bytes_to_uint32(b: bytes):
    if len(b) > 4:
        raise ValueError('bytes length larger than 4')
    return int.from_bytes(b, "big")

def uint32_to_bytes(i: int):
    # TOADD the range of i
    return int.to_bytes(4, "big")