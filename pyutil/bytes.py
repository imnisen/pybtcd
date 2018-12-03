def bytes_has_prefix(b: bytes, prefix: bytes) -> bool:
    if len(b) >= len(prefix) and b[0:len(prefix)] == prefix:
        return True
    return False
