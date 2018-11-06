# import database.treap as treap
# from .leveldb_iterator import Iterator


class LdbTreapIter(object):
    def __init__(self, iter, tx, released=None):
        self.__iter = iter
        self.tx = tx
        self.released = released or False

    def release(self):
        if not self.released:
            self.tx.remove_active_iter(self.__iter)  # TOCHECK TODO
            self.released = True

    def __getattr__(self, attr):
        return getattr(self.__iter, attr)

        # def __setattr__(self, attr, val):
        #     if attr == '_LdbTreapIter__iter':
        #         object.__setattr__(self, attr, val)
        #     return setattr(self.__iter, attr, val)


def new_ldb_treap_iter(tx, start, limit):
    iter = tx.pending_keys.iterator(start, limit)
    tx.add_active_iter(iter)
    return LdbTreapIter(iter=iter, tx=tx)
