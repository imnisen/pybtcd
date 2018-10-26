class TreapNode:
    def __init__(self, key, value=None, priority=None, parent=None, left=None, right=None):
        self.key = key
        self.value = value
        self.priority = priority
        self.parent = parent
        self.left = left
        self.right = right

    def __repr__(self):
        return str((self.key, self.value, self.priority))





