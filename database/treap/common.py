# nodeFieldsSize is the size the fields of each node takes excluding
# the contents of the key and value.  It assumes 64-bit pointers so
# technically it is smaller on 32-bit platforms, but overestimating the
# size in that case is acceptable since it avoids the need to import
# unsafe.  It consists of 24-bytes for each key and value + 8 bytes for
# each of the priority, left, and right fields (24*2 + 8*3).
nodeFieldsSize = 72  # TOCHECK , why not 8*3 = 24?


class TreapNode:
    def __init__(self, key, value, priority, left=None, right=None):
        self.key = key
        self.value = value
        self.priority = priority
        self.left = left
        self.right = right

    def __repr__(self):
        return "TreapNode(key=%s, value=%s, priority=%s)" % (self.key, self.value, self.priority)

    def node_size(self):
        return nodeFieldsSize + len(self.key) + len(self.value)


class ParentStack(list):
    def at(self, n):
        if n < 0:
            return None

        index = len(self) - 1 - n
        if index < 0:
            return None

        if index > len(self) - 1:
            raise IndexError

        return self[index]

    def push(self, x):
        self.append(x)
        return

    def pop(self, index=None):
        if len(self) > 0:
            if index is None:
                return super(ParentStack, self).pop()
            else:
                return super(ParentStack, self).pop(index)
        else:
            return None

