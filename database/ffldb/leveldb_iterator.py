from functools import wraps


# This is interface
class Iterator:
    def first(self) -> bool:
        pass

    def last(self) -> bool:
        pass

    def seek(self, key: bytes) -> bool:
        pass

    def next(self) -> bool:
        pass

    def prev(self) -> bool:
        pass

    def key(self) -> bytes:
        pass

    def value(self) -> bytes:
        pass

    def release(self):
        pass

    def release_setter(self):
        pass

    def valid(self) -> bool:
        pass

    def error(self):
        pass


class Dir(int):
    pass


dirReleased = Dir(-1)
dirSOI = Dir(0)
dirEOI = Dir(1)
dirBackward = Dir(2)
dirForward = Dir(3)


# Some errors
class ErrIterReleased(Exception):
    pass


def assert_key(key: bytes or None) -> bytes:
    if key is None:
        raise Exception("leveldb_iterator: None key")
    return key


def byte_compare(a: bytes or None, b: bytes or None):
    if a is None and b is None:
        return 0

    if a is None and b is not None:
        return -1

    if a is not None and b is None:
        return 1

    if a is not None and b is not None:
        if a > b:
            return 1
        elif a == b:
            return 0
        else:
            return -1


# decoretor to convert execption return as false
def exception_return_as_false(fn):
    @wraps(fn)
    def inner_fn(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except:
            self.err = True  # TOchange strange here
            return False

    return inner_fn


# Merged Iter
class MergedIterator:
    def __init__(self, iters: [Iterator], keys: [bytes], index: int = None, dir: Dir = None, err=None):
        self.iters = iters
        self.keys = keys
        self.index = index or 0
        self.dir = dir or dirSOI

        self.err = err

    def valid(self) -> bool:
        return self.err is None and self.dir > dirEOI

    @exception_return_as_false
    def first(self) -> bool:
        if self.err is not None:
            return False
        elif self.dir == dirReleased:
            self.err = ErrIterReleased
            return False

        for x, iter in enumerate(self.iters):
            if iter.first():
                self.keys[x] = assert_key(iter.key())
            else:
                self.keys[x] = None

        self.dir = dirSOI
        return self._next()

    @exception_return_as_false
    def last(self) -> bool:
        if self.err is not None:
            return False
        elif self.dir == dirReleased:
            self.err = ErrIterReleased
            return False

        for x, iter in enumerate(self.iters):
            if iter.last():
                self.keys[x] = assert_key(iter.key())
            else:
                self.keys[x] = None

        self.dir = dirEOI
        return self._prev()

    @exception_return_as_false
    def seek(self, key) -> bool:
        if self.err is not None:
            return False
        elif self.dir == dirReleased:
            self.err = ErrIterReleased
            return False

        for x, iter in enumerate(self.iters):
            if iter.seek(key):
                self.keys[x] = assert_key(iter.key())
            else:
                self.keys[x] = None

        self.dir = dirSOI
        return self._next()

    def _next(self) -> bool:

        key = None

        if self.dir == dirForward:
            key = self.keys[self.index]

        for x, tkey in enumerate(self.keys):
            if tkey is not None and byte_compare(tkey, key) < 0:
                key = tkey
                self.index = x

        if key is None:
            self.dir = dirEOI
            return False
        self.dir = dirForward
        return True

    @exception_return_as_false
    def next(self):
        if self.dir == dirEOI or self.err is not None:
            return False
        elif self.dir == dirReleased:
            self.err = ErrIterReleased
            return False

        if self.dir == dirSOI:
            return self.first()
        elif self.dir == dirBackward:
            key = self.keys[self.index]  # TOCHECK
            if not self.seek(key):
                return False
            return self.next()

        x = self.index
        iter = self.iters[x]
        if iter.next():
            self.keys[x] = assert_key(iter.key())
        else:
            self.keys[x] = None

        return self._next()

    def _prev(self) -> bool:

        key = None

        if self.dir == dirBackward:
            key = self.keys[self.index]

        for x, tkey in enumerate(self.keys):
            if tkey is not None and byte_compare(tkey, key) > 0:
                key = tkey
                self.index = x

        if key is None:
            self.dir = dirEOI
            return False
        self.dir = dirBackward
        return True

    @exception_return_as_false
    def prev(self):
        if self.dir == dirEOI or self.err is not None:
            return False
        elif self.dir == dirReleased:
            self.err = ErrIterReleased
            return False

        if self.dir == dirSOI:
            return self.last()
        elif self.dir == dirForward:
            key = self.keys[self.index]  # TOCHECK

            for x, iter in self.iters:
                if x == self.index:
                    continue
                seek = iter.seek(key)
                if seek and iter.prev or (not seek and self.last()):
                    self.keys[x] = assert_key(iter.key())
                else:
                    self.keys[x] = None

        x = self.index
        iter = self.iters[x]
        if iter.prev():
            self.keys[x] = assert_key(iter.key())
        else:
            self.keys[x] = None

        return self._prev()

    def key(self):
        if self.err is not None or self.dir <= dirEOI:
            return None

        return self.keys[self.index]

    def value(self):
        if self.err is not None or self.dir <= dirEOI:
            return None

        return self.iters[self.index].value()

    def release(self):
        if self.dir != dirReleased:
            self.dir = dirReleased
            for iter in self.iters:
                iter.release()
            self.iters = []
            self.keys = []

            # TODO release releaser

        return

    def set_releaser(self):
        pass


def new_merged_iterator(iters):
    return MergedIterator(
        iters=iters,
        keys=[None] * len(iters)
    )
