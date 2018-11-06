import database.treap as treap
from .leveldb_iterator import Iterator

class LdbTreapIter(treap.Iterator, Iterator):
    def __init__(self, tx, released=None, t=None, root=None, node=None, parent_stack=None, is_new=None, seek_key=None, start_key=None,
                 limit_key=None):
        super(LdbTreapIter).__init__(t=t,
                                     root=root,
                                     node=node,
                                     parent_stack=parent_stack,
                                     is_new=is_new,
                                     seek_key=seek_key,
                                     start_key=start_key,
                                     limit_key=None)
        self.tx = tx
        self.released = released or False

    def release(self):
        if not self.released:
            self.tx.remove_active_iter(super(self))  # TOCHECK TODO
            self.released = True


def new_ldb_treap_iter(tx, start, limit):
    iter = tx.pending_keys.iterator(start, limit)
    tx.add_active_iter(iter)
    return LdbTreapIter()  # TODO MARK How to make instance here