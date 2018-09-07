import copy

# HashSize of array used to store hashes.  See Hash.
HashSize = 32

# MaxHashStringSize is the maximum length of a Hash hash string.
MaxHashStringSize = HashSize * 2


# TOCHANGE ErrHashStrSize describes an error that indicates the caller specified a hash
# string that has too many characters.
class Err(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class HashStrSizeErr(Err):
    def __init__(self, msg=None):
        if not msg:
            msg = "max hash string length is %{} bytes".format(MaxHashStringSize)
        super(HashStrSizeErr, self).__init__(msg=msg)


class Hash:
    def __init__(self, data):
        if type(data) is bytes:
            self._data = None
            self.set_bytes(data)
        elif type(data) is str:
            self._data = self.str_decode(data)

    def __str__(self):
        """Hash -> string"""
        for i in range(0, HashSize / 2):
            self._data[i], self._data[HashSize - 1 - i] = self._data[HashSize - 1 - i], self._data[i]
        return self._data.hex()

    def clone_bytes(self) -> bytes:
        """Return copy bytes of self"""
        return copy.deepcopy(self._data)

    def set_bytes(self, new_hash: bytes) -> None:
        """Change bytes of Hash"""
        nhlen = len(new_hash)
        if nhlen != HashSize:
            raise Err("invalid hash length of {}, want {}".format(nhlen, HashSize))
        self._data = copy.deepcopy(new_hash)

    def is_equal(self, target: 'Hash') -> bool:
        """Compare to Hash content is the same"""
        # TOCHANGE maybe we can just use '==' to pass these check
        if not self._data and not target._data:
            return True
        if not self._data or target._data:
            return False

        # TOCHECK can we use '==' to check two bytes equailty
        return self._data == target._data

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return self._data

    @staticmethod
    def str_decode(src):
        if len(src) > MaxHashStringSize:
            raise HashStrSizeErr

        if len(src) % 2 != 0:
            src = '0' + src

        # TOCHECK check if the reversed_hash correct here. make sure it's len is HashSize
        # TOCLEAN Please refer to origin
        reversed_hash = bytes.fromhex(src)

        for i in range(0, HashSize / 2):
            reversed_hash[i], reversed_hash[HashSize - 1 - i] = reversed_hash[HashSize - 1 - i], reversed_hash[i]
        return reversed_hash


# NewHash returns a new Hash from a byte slice.  An error is returned if
# the number of bytes passed in is not HashSize.
# def new_hash(hash: bytes) -> Hash:
#     return Hash(hash=hash)


# NewHashFromStr creates a Hash from a hash string.  The string should be
# the hexadecimal string of a byte-reversed hash, but any missing characters
# result in zero padding at the end of the Hash.
# def new_hash_from_str(src: str) -> Hash:
#     return decode(str)



# Decode decodes the byte-reversed hexadecimal string encoding of a Hash to Hash
# TOCLEAN here change the behavior to return Hash, not by side effect as the origin
# def decode(src: str) -> Hash:
#     return Hash(reversed_hash)
