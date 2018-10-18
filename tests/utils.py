import io


# For TestVarIntWireErrors test, same as golang newFixedWriter, newFixedReader
class FixedBytesErr(Exception):
    pass


class FixedBytesInitErr(FixedBytesErr):
    pass


class FixedBytesUnexpectedEOFErr(FixedBytesErr):
    pass


class FixedBytesShortWriteErr(FixedBytesErr):
    pass


class FixedBytesNotSupportedErr(FixedBytesErr):
    pass


class FixedBytesReader:
    def __init__(self, max, buf):
        if max < 0:
            raise FixedBytesInitErr

        self.max = max
        self._data = io.BytesIO(buf)
        self._buf_len = len(buf)

    def read(self, size: int) -> bytes:
        # Limit the case, maybe we can let size<0, and decide what to do
        if size < 0:
            print(size)
            raise FixedBytesErr('size must greater than 0')

        result = bytearray()
        while True:
            if size == 0:
                break

            if self.max == 0:
                raise FixedBytesUnexpectedEOFErr

            result += self._data.read(1)
            self.max -= 1
            size -= 1

        return bytes(result)

    def seek(self, offset=0, whence=0):
        if offset != 0:
            raise FixedBytesNotSupportedErr

        if whence == 2 and self.max < self._buf_len:
            self._data.seek(self.max, 0)
        else:
            self._data.seek(offset, whence)

    def tell(self):
        return self._data.tell()


class FixedBytesWriter:
    def __init__(self, max):
        if max < 0:
            raise FixedBytesInitErr
        self.max = max
        self._data = io.BytesIO()

    def write(self, val: bytes):

        val_len = len(val)
        i = 0
        while True:
            if i > val_len - 1:
                break
            if self.max == 0:
                raise FixedBytesShortWriteErr

            self._data.write(val[i].to_bytes(1, byteorder="little"))
            i += 1
            self.max -= 1
        return


def list_equal(l1, l2):
    if len(l1) == len(l2):
        for i in range(len(l1)):
            if l1[i] != l2[i]:
                return False
        return True
    else:
        return False


###################
# Some debug utils
###################

def debug_check_bytes(b1, b2):
    print("-------Debug output-------")
    if len(b1) != len(b2):
        print("len is not equal, one is {}, another is {}".format(len(b1), len(b2)))
        return

    for i in range(len(b1)):
        print("{}, {},  equal?:{}".format(hex(b1[i]), hex(b2[i]), b1[i] == b2[i]))
    print("-------EOF-------")
    return
