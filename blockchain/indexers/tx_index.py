import database
import chainhash

# TODO
def db_fetch_block_id_by_hash(db_tx: database.Tx, hash:chainhash.Hash) -> int:
    pass

def db_fetch_block_hash_by_serialized_id(db_tx: database.Tx, serialized_id: bytes) -> chainhash.Hash:
    pass