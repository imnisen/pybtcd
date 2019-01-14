import wire
import blockchain
import btcutil

# UnminedHeight is the height used for the "block" height field of the
# contextual transaction information provided in a transaction store
# when it has not yet been mined into a block.
UnminedHeight = 0x7fffffff


class Policy:
    def __init__(self, block_min_weight: int, block_max_weight: int,
                 block_min_size: int, block_max_size: int,
                 block_priority_size: int, tx_min_free_fee):
        """

        :param uint32 block_min_weight:
        :param uint32 block_max_weight:
        :param uint32 block_min_size:
        :param uint32 block_max_size:
        :param uint32 block_priority_size:
        :param btcutil.Amount tx_min_free_fee:
        """
        # BlockMinWeight is the minimum block weight to be used when
        # generating a block template.
        self.block_min_weight = block_min_weight

        # BlockMaxWeight is the maximum block weight to be used when
        # generating a block template.
        self.block_max_weight = block_max_weight

        # BlockMinWeight is the minimum block size to be used when generating
        # a block template.
        self.block_min_size = block_min_size

        # BlockMaxSize is the maximum block size to be used when generating a
        # block template.
        self.block_max_size = block_max_size

        # BlockPrioritySize is the size in bytes for high-priority / low-fee
        # transactions to be used when generating a block template.
        self.block_priority_size = block_priority_size

        # TxMinFreeFee is the minimum fee in Satoshi/1000 bytes that is
        # required for a transaction to be treated as free for mining purposes
        # (block template generation).
        self.tx_min_free_fee = tx_min_free_fee


# calcInputValueAge is a helper function used to calculate the input age of
# a transaction.  The input age for a txin is the number of confirmations
# since the referenced txout multiplied by its output value.  The total input
# age is the sum of this value for each txin.  Any inputs to the transaction
# which are currently in the mempool and hence not mined into a block yet,
# contribute no additional input age to the transaction.
def calc_input_value_age(tx: wire.MsgTx, utxo_view: blockchain.UtxoViewpoint, next_block_height: int) -> int:
    total_input_value_age = 0

    for tx_in in tx.tx_ins:
        # Don't attempt to accumulate the total input age if the
        # referenced transaction output doesn't exist.
        entry = utxo_view.lookup_entry(tx_in.previous_out_point)
        if entry is not None and not entry.is_spent():
            # Inputs with dependencies currently in the mempool
            # have their block height set to a special constant.
            # Their input age should computed as zero since their
            # parent hasn't made it into a block yet.

            origin_height = entry.get_block_height()
            if origin_height == UnminedHeight:
                input_age = 0
            else:
                input_age = next_block_height - origin_height

            input_value = entry.get_amount()

            total_input_value_age += input_value * input_age
    return total_input_value_age


# CalcPriority returns a transaction priority given a transaction and the sum
# of each of its input values multiplied by their age (# of confirmations).
# Thus, the final formula for the priority is:
# sum(inputValue * inputAge) / adjustedTxSize
def calc_priority(tx: wire.MsgTx, utxo_view: blockchain.UtxoViewpoint, next_block_height: int) -> float:
    # TOCONSIDER why
    # In order to encourage spending multiple old unspent transaction
    # outputs thereby reducing the total set, don't count the constant
    # overhead for each input as well as enough bytes of the signature
    # script to cover a pay-to-script-hash redemption with a compressed
    # pubkey.  This makes additional inputs free by boosting the priority
    # of the transaction accordingly.  No more incentive is given to avoid
    # encouraging gaming future transactions through the use of junk
    # outputs.  This is the same logic used in the reference
    # implementation.
    #
    # The constant overhead for a txin is 41 bytes since the previous
    # outpoint is 36 bytes + 4 bytes for the sequence + 1 byte the
    # signature script length.
    #
    # A compressed pubkey pay-to-script-hash redemption with a maximum len
    # signature is of the form:
    # [OP_DATA_73 <73-byte sig> + OP_DATA_35 + {OP_DATA_33
    # <33 byte compresed pubkey> + OP_CHECKSIG}]
    #
    # Thus 1 + 73 + 1 + 1 + 33 + 1 = 110

    overhead = 0
    for tx_in in tx.tx_ins:
        # Max inputs + size can't possibly overflow here.
        overhead += 41 + min(110, len(tx_in.signature_script))

    serialized_tx_size = tx.serialize_size()

    if overhead >= serialized_tx_size:
        return 0.0

    input_value_age = calc_input_value_age(tx, utxo_view, next_block_height)

    return input_value_age / float(serialized_tx_size - overhead)
