import chainhash
import database
from btcec.utils import int_to_bytes, bytes_to_int

# byteOrder is the preferred byte order used for serializing numeric
# fields for storage in the database.
byteOrder = "little"

# chainStateKeyName is the name of the db key used to store the best
# chain state.
chainStateKeyName = b"chainstate"


# -----------------------------------------------------------------------------
# The best chain state consists of the best block hash and height, the total
# number of transactions up to and including those in the best block, and the
# accumulated work sum up to and including the best block.
#
# The serialized format is:
#
#   <block hash><block height><total txns><work sum length><work sum>
#
#   Field             Type             Size
#   block hash        chainhash.Hash   chainhash.HashSize
#   block height      uint32           4 bytes
#   total txns        uint64           8 bytes
#   work sum length   uint32           4 bytes
#   work sum          big.Int          work sum length
# -----------------------------------------------------------------------------

# bestChainState represents the data to be stored the database for the current
# best chain state.
class BestChainState:
    def __init__(self, hash: chainhash.Hash, height: int, total_txns: int, work_sum: int):
        """

        :param chainhash.Hash hash:
        :param int height:
        :param int total_txns:
        :param int work_sum:
        """
        self.hash = hash
        self.height = height
        self.total_txns = total_txns
        self.work_sum = work_sum


# serializeBestChainState returns the serialization of the passed block best
# chain state.  This is data to be stored in the chain state bucket.
def serialize_best_chain_state(state: BestChainState):
    work_sum_bytes = int_to_bytes(state.work_sum)  # TOCHECK
    return state.hash.to_bytes() + state.height.to_bytes(4, byteOrder) + state.total_txns.to_bytes(8, byteOrder) + \
           len(work_sum_bytes).to_bytes(4, byteOrder) + work_sum_bytes


# deserializeBestChainState deserializes the passed serialized best chain
# state.  This is data stored in the chain state bucket and is updated after
# every block is connected or disconnected form the main chain.
# block.
def deserialize_best_chain_state(serialized_data: bytes) -> BestChainState:
    if len(serialized_data) < chainhash.HashSize + 16:
        raise database.DBError(c=database.ErrorCode.ErrCorruption, desc="corrupt best chain state")

    the_hash = chainhash.Hash(serialized_data[0: chainhash.HashSize])

    offset = chainhash.HashSize
    height = int.from_bytes(serialized_data[offset: offset + 4], byteOrder)

    offset += 4
    total_txns = int.from_bytes(serialized_data[offset: offset + 8], byteOrder)

    offset += 8
    work_sum_bytes_len = int.from_bytes(serialized_data[offset: offset + 4], byteOrder)

    offset += 4
    if len(serialized_data[offset:]) < work_sum_bytes_len:
        raise database.DBError(c=database.ErrorCode.ErrCorruption, desc="corrupt best chain state")

    work_sum_bytes = serialized_data[offset:offset + work_sum_bytes_len]
    work_sum = bytes_to_int(work_sum_bytes)
    return BestChainState(hash=the_hash, height=height, total_txns=total_txns, work_sum=work_sum)


def db_put_best_state(db_tx: database.Tx, snapshot, work_sum: int):
    """

    :param database.Tx db_tx:
    :param BestState snapshot:
    :param int work_sum:
    :return:
    """
    # Serialize the current best chain state.
    serialized_data = serialize_best_chain_state(
        BestChainState(
            hash=snapshot.hash,
            height=snapshot.height,
            total_txns=snapshot.total_txns,
            work_sum=work_sum
        ))
    #  Store the current best chain state into the database.
    return db_tx.metadata().put(chainStateKeyName, serialized_data)


