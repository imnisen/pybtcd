def byte_compare(b1, b2: bytes) -> int:
    if b1 > b2:
        return 1
    elif b1 == b2:
        return 0
    else:
        return -1
