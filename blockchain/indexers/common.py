import database
import btcutil
import blockchain


# NeedsInputser provides a generic interface for an indexer to specify the it
# requires the ability to look up inputs for a transaction.
class NeedsInputser:
    def need_inputs(self) -> bool:
        raise NotImplementedError


# Indexer provides a generic interface for an indexer that is managed by an
# index manager such as the Manager type provided by this package.
class Indexer:
    # Key returns the key of the index as a byte slice.
    def key(self) -> bytes:
        raise NotImplementedError

    # Name returns the human-readable name of the index.
    def name(self) -> str:
        raise NotImplementedError

    # Create is invoked when the indexer manager determines the index needs
    # to be created for the first time.
    def create(self, db_tx: database.Tx):
        raise NotImplementedError

    # Init is invoked when the index manager is first initializing the
    # index.  This differs from the Create method in that it is called on
    # every load, including the case the index was just created.
    def init(self):
        raise NotImplementedError

    # ConnectBlock is invoked when a new block has been connected to the
    # main chain. The set of output spent within a block is also passed in
    # so indexers can access the pevious output scripts input spent if
    # required.
    def connect_block(self, db_tx: database.Tx, block: btcutil.Block, stxos: [blockchain.SpentTxOut]):
        raise NotImplementedError

    # DisconnectBlock is invoked when a block has been disconnected from
    # the main chain. The set of outputs scripts that were spent within
    # this block is also returned so indexers can clean up the prior index
    # state for this block
    def disconnect_block(self, db_tx: database.Tx, block: btcutil.Block, stxos: [blockchain.SpentTxOut]):
        raise NotImplementedError


class InternalBucket:
    def get(self, key: bytes) -> bytes:
        raise NotImplementedError

    def put(self, key: bytes, value: bytes):
        raise NotImplementedError

    def delete(self, key: bytes):
        raise NotImplementedError
