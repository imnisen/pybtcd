import hashlib


def sha1(x):
    return hashlib.sha1(x).digest()


def sha256(x):
    return hashlib.sha256(x).digest()


def ripemd160(x):
    return hashlib.new('ripemd160', x).digest()

def hash160(x):
    return ripemd160(sha256(x))
