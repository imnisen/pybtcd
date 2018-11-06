
# This is interface
class Iterator:
    def first(self) -> bool:
        pass

    def last(self) -> bool:
        pass

    def seek(self, key:bytes) -> bool:
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