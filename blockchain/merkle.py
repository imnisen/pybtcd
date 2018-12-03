import math
import chainhash
import pyutil
import txscript
import btcutil
from .validate import *
from .error import *

# CoinbaseWitnessDataLen is the required length of the only element within
# the coinbase's witness data if the coinbase transaction contains a
# witness commitment.
CoinbaseWitnessDataLen = 32

# CoinbaseWitnessPkScriptLength is the length of the public key script
# containing an OP_RETURN, the WitnessMagicBytes, and the witness
# commitment itself. In order to be a valid candidate for the output
# containing the witness commitment
CoinbaseWitnessPkScriptLength = 38

# WitnessMagicBytes is the prefix marker within the public key script
# of a coinbase output to indicate that this output holds the witness
# commitment for a block.
WitnessMagicBytes = bytes([
    txscript.OP_RETURN,
    txscript.OP_DATA_36,
    0xaa,
    0x21,
    0xa9,
    0xed,
])


# nextPowerOfTwo returns the next highest power of two from a given number if
# it is not already a power of two.  This is a helper function used during the
# calculation of a merkle tree.
def next_power_of_two(n: int) -> int:
    # Return the number if it's already a power of 2.
    if n & (n - 1) == 0:
        return n

    # Figure out and return the next power of two.
    exponent = int(math.log(n, 2)) + 1
    return 1 << exponent


# HashMerkleBranches takes two hashes, treated as the left and right tree
# nodes, and returns the hash of their concatenation.  This is a helper
# function used to aid in the generation of a merkle tree.
def hash_merkle_branches(left: chainhash.Hash, right: chainhash.Hash) -> chainhash.Hash:
    return chainhash.double_hash_h(left.to_bytes() + right.to_bytes())


# BuildMerkleTreeStore creates a merkle tree from a slice of transactions,
# stores it using a linear array, and returns a slice of the backing array.  A
# linear array was chosen as opposed to an actual tree structure since it uses
# about half as much memory.  The following describes a merkle tree and how it
# is stored in a linear array.
#
# A merkle tree is a tree in which every non-leaf node is the hash of its
# children nodes.  A diagram depicting how this works for bitcoin transactions
# where h(x) is a double sha256 follows:
#
#             root = h1234 = h(h12 + h34)
#            /                           \
#      h12 = h(h1 + h2)            h34 = h(h3 + h4)
#       /            \              /            \
#    h1 = h(tx1)  h2 = h(tx2)    h3 = h(tx3)  h4 = h(tx4)
#
# The above stored as a linear array is as follows:
#
#     [h1 h2 h3 h4 h12 h34 root]
#
# As the above shows, the merkle root is always the last element in the array.
#
# The number of inputs is not always a power of two which results in a
# balanced tree structure as above.  In that case, parent nodes with no
# children are also zero and parent nodes with only a single left node
# are calculated by concatenating the left node with itself before hashing.
# Since this function uses nodes that are pointers to the hashes, empty nodes
# will be nil.
#
# The additional bool parameter indicates if we are generating the merkle tree
# using witness transaction id's rather than regular transaction id's. This
# also presents an additional case wherein the wtxid of the coinbase transaction
# is the zeroHash.
def build_merkle_tree_store(transactions: [btcutil.Tx], witness: bool) -> [chainhash.Hash]:
    next_pot = next_power_of_two(len(transactions))
    array_size = 2 * next_pot - 1  ## like 2^4+ 2^3 + 2^2 + 2^1 + 2^0 =  2^ 5 -1 = 2 * (4) - 1
    merkles = [None] * array_size

    # Create the base transaction hashes and populate the array with them.
    for i, tx in enumerate(transactions):
        if witness:
            if i != 0:
                merkles[i] = tx.witness_hash()
            else:
                merkles[i] = chainhash.Hash()
        else:
            merkles[i] = tx.hash()

    # Start the array offset after the last transaction and adjusted to the
    # next power of two.
    offset = next_pot
    for i in range(0, array_size - 1, 2):
        if merkles[i] is None:
            merkles[offset] = None
        elif merkles[i + 1] is None:
            merkles[offset] = hash_merkle_branches(merkles[i], merkles[i])
        else:
            merkles[offset] = hash_merkle_branches(merkles[i], merkles[i + 1])
        offset += 1
    return merkles


# ExtractWitnessCommitment attempts to locate, and return the witness
# commitment for a block. The witness commitment is of the form:
# SHA256(witness root || witness nonce). The function additionally returns a
# boolean indicating if the witness root was located within any of the txOut's
# in the passed transaction. The witness commitment is stored as the data push
# for an OP_RETURN with special magic bytes to aide in location.
def extract_witness_commitment(tx: btcutil.Tx) -> (bytes or None, bool):
    # The witness commitment *must* be located within one of the coinbase
    # transaction's outputs.
    if not is_coin_base(tx):
        return None, False

    msg_tx = tx.get_msg_tx()
    for tx_out in reversed(msg_tx.tx_outs):
        # The public key script that contains the witness commitment
        # must shared a prefix with the WitnessMagicBytes, and be at
        # least 38 bytes.
        pk_script = tx_out.pk_script
        if len(pk_script) >= CoinbaseWitnessPkScriptLength and \
                pyutil.bytes_has_prefix(pk_script, WitnessMagicBytes):
            # The witness commitment itself is a 32-byte hash
            # directly after the WitnessMagicBytes. The remaining
            # bytes beyond the 38th byte currently have no consensus
            # meaning.
            start = len(WitnessMagicBytes)
            end = CoinbaseWitnessPkScriptLength
            return tx_out[start:end], True
    return None, False


# TODO TOCONSIDER the computational process
# ValidateWitnessCommitment validates the witness commitment (if any) found
# within the coinbase transaction of the passed block.
def validate_witness_commitment(blk: btcutil.Block):
    # If the block doesn't have any transactions at all, then we won't be
    # able to extract a commitment from the non-existent coinbase
    # transaction. So we exit early here.
    if len(blk.get_transactions()) == 0:
        msg = "cannot validate witness commitment of block without transactions"
        raise RuleError(ErrorCode.ErrNoTransactions, msg)

    coin_base_tx = blk.get_transactions()[0]
    if len(coin_base_tx.get_msg_tx().tx_ins) == 0:
        msg = "transaction has no inputs"
        raise RuleError(ErrorCode.ErrNoTxInputs, msg)

    witness_commitment, witness_found = extract_witness_commitment(coin_base_tx)

    # If we can't find a witness commitment in any of the coinbase's
    # outputs, then the block MUST NOT contain any transactions with
    # witness data.
    if not witness_found:
        for tx in blk.get_transactions():
            msg_tx = tx.get_msg_tx()
            if msg_tx.has_witness():
                msg = "block contains transaction with witness data, yet no witness commitment present"
                raise RuleError(ErrorCode.ErrUnexpectedWitness, msg)

        return

    # At this point the block contains a witness commitment, so the
    # coinbase transaction MUST have exactly one witness element within
    # its witness data and that element must be exactly
    # CoinbaseWitnessDataLen bytes.
    coinbase_witness = coin_base_tx.get_msg_tx().tx_in[0].witness
    if len(coinbase_witness) != 1:
        msg = "the coinbase transaction has %d items in its witness stack when only one is allowed" % len(
            coinbase_witness)
        raise RuleError(ErrorCode.ErrInvalidWitnessCommitment, msg)

    witness_nonce = coinbase_witness[0]
    if len(witness_nonce) != CoinbaseWitnessDataLen:
        msg = "the coinbase transaction witness nonce has %d bytes when it must be %d bytes" % (
          len(witness_nonce), CoinbaseWitnessDataLen)
        raise RuleError(ErrorCode.ErrInvalidWitnessCommitment, msg)

    # Finally, with the preliminary checks out of the way, we can check if
    # the extracted witnessCommitment is equal to:
    # SHA256(witnessMerkleRoot || witnessNonce). Where witnessNonce is the
    # coinbase transaction's only witness item.
    witness_merkle_tree = build_merkle_tree_store(blk.get_transactions(), witness=True)
    witness_merkle_root = witness_merkle_tree[-1]

    witness_preimage = witness_merkle_root + witness_nonce  # TOCHECK the type
    computed_commitment = chainhash.double_hash_b(witness_preimage)
    if computed_commitment != witness_commitment:
        msg = "witness commitment does not match: computed %s, coinbase includes %s" % (
          computed_commitment, witness_commitment)
        raise RuleError(ErrorCode.ErrWitnessCommitmentMismatch, msg)

    return
