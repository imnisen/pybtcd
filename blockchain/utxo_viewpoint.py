

# UtxoViewpoint represents a view into the set of unspent transaction outputs
# from a specific point of view in the chain.  For example, it could be for
# the end of the main chain, some point in the history of the main chain, or
# down a side chain.
#
# The unspent outputs are needed by other transactions for things such as
# script validation and double spend prevention.
class UtxoViewpoint:
    def __init__(self, entries, best_hash):
        self.entries = entries
        self.best_hash = best_hash
