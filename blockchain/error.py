from enum import Enum


# DeploymentError identifies an error that indicates a deployment ID was
# specified that does not exist.
class DeploymentError(Exception):
    def __init__(self, msg=None, err=None, extra=None):
        """

        :param str msg:
        :param Exception err:
        :param extra:
        """

        self.msg = msg or ""
        self.err = err
        self.extra = extra

    def __repr__(self):
        return "DeploymentError(msg={})".format(self.msg or "\"\"")

    def __str__(self):
        return "DeploymentError(msg={})".format(self.msg or "\"\"")

    def __hash__(self):
        return hash(str(self.msg))


# AssertError identifies an error that indicates an internal code consistency
# issue and should be treated as a critical and unrecoverable error.
class AssertError(Exception):
    def __init__(self, msg=None, err=None, extra=None):
        """

        :param str msg:
        :param Exception err:
        :param extra:
        """

        self.msg = msg or ""
        self.err = err
        self.extra = extra

    def __repr__(self):
        return "AssertError(msg={})".format(self.msg or "\"\"")

    def __str__(self):
        return "AssertError(msg={})".format(self.msg or "\"\"")

    def __hash__(self):
        return hash(str(self.msg))


# ErrorCode identifies a kind of error.
class ErrorCode(Enum):
    # ErrDuplicateBlock indicates a block with the same hash already
    # exists.
    ErrDuplicateBlock = 0

    # ErrBlockTooBig indicates the serialized block size exceeds the
    # maximum allowed size.
    ErrBlockTooBig = 1

    # ErrBlockWeightTooHigh indicates that the block's computed weight
    # metric exceeds the maximum allowed value.
    ErrBlockWeightTooHigh = 2

    # ErrBlockVersionTooOld indicates the block version is too old and is
    # no longer accepted since the majority of the network has upgraded
    # to a newer version.
    ErrBlockVersionTooOld = 3

    # ErrInvalidTime indicates the time in the passed block has a precision
    # that is more than one second.  The chain consensus rules require
    # timestamps to have a maximum precision of one second.
    ErrInvalidTime = 4

    # ErrTimeTooOld indicates the time is either before the median time of
    # the last several blocks per the chain consensus rules or prior to the
    # most recent checkpoint.
    ErrTimeTooOld = 5

    # ErrTimeTooNew indicates the time is too far in the future as compared
    # the current time.
    ErrTimeTooNew = 6

    # ErrDifficultyTooLow indicates the difficulty for the block is lower
    # than the difficulty required by the most recent checkpoint.
    ErrDifficultyTooLow = 7

    # ErrUnexpectedDifficulty indicates specified bits do not align with
    # the expected value either because it doesn't match the calculated
    # valued based on difficulty regarted rules or it is out of the valid
    # range.
    ErrUnexpectedDifficulty = 8

    # ErrHighHash indicates the block does not hash to a value which is
    # lower than the required target difficultly.
    ErrHighHash = 9

    # ErrBadMerkleRoot indicates the calculated merkle root does not match
    # the expected value.
    ErrBadMerkleRoot = 10

    # ErrBadCheckpoint indicates a block that is expected to be at a
    # checkpoint height does not match the expected one.
    ErrBadCheckpoint = 11

    # ErrForkTooOld indicates a block is attempting to fork the block chain
    # before the most recent checkpoint.
    ErrForkTooOld = 12

    # ErrCheckpointTimeTooOld indicates a block has a timestamp before the
    # most recent checkpoint.
    ErrCheckpointTimeTooOld = 13

    # ErrNoTransactions indicates the block does not have a least one
    # transaction.  A valid block must have at least the coinbase
    # transaction.
    ErrNoTransactions = 14

    # ErrNoTxInputs indicates a transaction does not have any inputs.  A
    # valid transaction must have at least one input.
    ErrNoTxInputs = 15

    # ErrNoTxOutputs indicates a transaction does not have any outputs.  A
    # valid transaction must have at least one output.
    ErrNoTxOutputs = 16

    # ErrTxTooBig indicates a transaction exceeds the maximum allowed size
    # when serialized.
    ErrTxTooBig = 17

    # ErrBadTxOutValue indicates an output value for a transaction is
    # invalid in some way such as being out of range.
    ErrBadTxOutValue = 18

    # ErrDuplicateTxInputs indicates a transaction references the same
    # input more than once.
    ErrDuplicateTxInputs = 19

    # ErrBadTxInput indicates a transaction input is invalid in some way
    # such as referencing a previous transaction outpoint which is out of
    # range or not referencing one at all.
    ErrBadTxInput = 20

    # ErrMissingTxOut indicates a transaction output referenced by an input
    # either does not exist or has already been spent.
    ErrMissingTxOut = 21

    # ErrUnfinalizedTx indicates a transaction has not been finalized.
    # A valid block may only contain finalized transactions.
    ErrUnfinalizedTx = 22

    # ErrDuplicateTx indicates a block contains an identical transaction
    # (or at least two transactions which hash to the same value).  A
    # valid block may only contain unique transactions.
    ErrDuplicateTx = 23

    # ErrOverwriteTx indicates a block contains a transaction that has
    # the same hash as a previous transaction which has not been fully
    # spent.
    ErrOverwriteTx = 24

    # ErrImmatureSpend indicates a transaction is attempting to spend a
    # coinbase that has not yet reached the required maturity.
    ErrImmatureSpend = 25

    # ErrSpendTooHigh indicates a transaction is attempting to spend more
    # value than the sum of all of its inputs.
    ErrSpendTooHigh = 26

    # ErrBadFees indicates the total fees for a block are invalid due to
    # exceeding the maximum possible value.
    ErrBadFees = 27

    # ErrTooManySigOps indicates the total number of signature operations
    # for a transaction or block exceed the maximum allowed limits.
    ErrTooManySigOps = 28

    # ErrFirstTxNotCoinbase indicates the first transaction in a block
    # is not a coinbase transaction.
    ErrFirstTxNotCoinbase = 29

    # ErrMultipleCoinbases indicates a block contains more than one
    # coinbase transaction.
    ErrMultipleCoinbases = 30

    # ErrBadCoinbaseScriptLen indicates the length of the signature script
    # for a coinbase transaction is not within the valid range.
    ErrBadCoinbaseScriptLen = 31

    # ErrBadCoinbaseValue indicates the amount of a coinbase value does
    # not match the expected value of the subsidy plus the sum of all fees.
    ErrBadCoinbaseValue = 32

    # ErrMissingCoinbaseHeight indicates the coinbase transaction for a
    # block does not start with the serialized block block height as
    # required for version 2 and higher blocks.
    ErrMissingCoinbaseHeight = 33

    # ErrBadCoinbaseHeight indicates the serialized block height in the
    # coinbase transaction for version 2 and higher blocks does not match
    # the expected value.
    ErrBadCoinbaseHeight = 34

    # ErrScriptMalformed indicates a transaction script is malformed in
    # some way.  For example, it might be longer than the maximum allowed
    # length or fail to parse.
    ErrScriptMalformed = 35

    # ErrScriptValidation indicates the result of executing transaction
    # script failed.  The error covers any failure when executing scripts
    # such signature verification failures and execution past the end of
    # the stack.
    ErrScriptValidation = 36

    # ErrUnexpectedWitness indicates that a block includes transactions
    # with witness data, but doesn't also have a witness commitment within
    # the coinbase transaction.
    ErrUnexpectedWitness = 37

    # ErrInvalidWitnessCommitment indicates that a block's witness
    # commitment is not well formed.
    ErrInvalidWitnessCommitment = 38

    # ErrWitnessCommitmentMismatch indicates that the witness commitment
    # included in the block's coinbase transaction doesn't match the
    # manually computed witness commitment.
    ErrWitnessCommitmentMismatch = 39

    # ErrPreviousBlockUnknown indicates that the previous block is not known.
    ErrPreviousBlockUnknown = 40

    # ErrInvalidAncestorBlock indicates that an ancestor of this block has
    # already failed validation.
    ErrInvalidAncestorBlock = 41

    # ErrPrevBlockNotBest indicates that the block's previous block is not the
    # current chain tip. This is not a block validation rule, but is required
    # for block proposals submitted via getblocktemplate RPC.
    ErrPrevBlockNotBest = 42

    def __str__(self):
        return errorCodeStrings[self]


errorCodeStrings = {
    ErrorCode.ErrDuplicateBlock: "ErrDuplicateBlock",
    ErrorCode.ErrBlockTooBig: "ErrBlockTooBig",
    ErrorCode.ErrBlockVersionTooOld: "ErrBlockVersionTooOld",
    ErrorCode.ErrBlockWeightTooHigh: "ErrBlockWeightTooHigh",
    ErrorCode.ErrInvalidTime: "ErrInvalidTime",
    ErrorCode.ErrTimeTooOld: "ErrTimeTooOld",
    ErrorCode.ErrTimeTooNew: "ErrTimeTooNew",
    ErrorCode.ErrDifficultyTooLow: "ErrDifficultyTooLow",
    ErrorCode.ErrUnexpectedDifficulty: "ErrUnexpectedDifficulty",
    ErrorCode.ErrHighHash: "ErrHighHash",
    ErrorCode.ErrBadMerkleRoot: "ErrBadMerkleRoot",
    ErrorCode.ErrBadCheckpoint: "ErrBadCheckpoint",
    ErrorCode.ErrForkTooOld: "ErrForkTooOld",
    ErrorCode.ErrCheckpointTimeTooOld: "ErrCheckpointTimeTooOld",
    ErrorCode.ErrNoTransactions: "ErrNoTransactions",
    ErrorCode.ErrNoTxInputs: "ErrNoTxInputs",
    ErrorCode.ErrNoTxOutputs: "ErrNoTxOutputs",
    ErrorCode.ErrTxTooBig: "ErrTxTooBig",
    ErrorCode.ErrBadTxOutValue: "ErrBadTxOutValue",
    ErrorCode.ErrDuplicateTxInputs: "ErrDuplicateTxInputs",
    ErrorCode.ErrBadTxInput: "ErrBadTxInput",
    ErrorCode.ErrMissingTxOut: "ErrMissingTxOut",
    ErrorCode.ErrUnfinalizedTx: "ErrUnfinalizedTx",
    ErrorCode.ErrDuplicateTx: "ErrDuplicateTx",
    ErrorCode.ErrOverwriteTx: "ErrOverwriteTx",
    ErrorCode.ErrImmatureSpend: "ErrImmatureSpend",
    ErrorCode.ErrSpendTooHigh: "ErrSpendTooHigh",
    ErrorCode.ErrBadFees: "ErrBadFees",
    ErrorCode.ErrTooManySigOps: "ErrTooManySigOps",
    ErrorCode.ErrFirstTxNotCoinbase: "ErrFirstTxNotCoinbase",
    ErrorCode.ErrMultipleCoinbases: "ErrMultipleCoinbases",
    ErrorCode.ErrBadCoinbaseScriptLen: "ErrBadCoinbaseScriptLen",
    ErrorCode.ErrBadCoinbaseValue: "ErrBadCoinbaseValue",
    ErrorCode.ErrMissingCoinbaseHeight: "ErrMissingCoinbaseHeight",
    ErrorCode.ErrBadCoinbaseHeight: "ErrBadCoinbaseHeight",
    ErrorCode.ErrScriptMalformed: "ErrScriptMalformed",
    ErrorCode.ErrScriptValidation: "ErrScriptValidation",
    ErrorCode.ErrUnexpectedWitness: "ErrUnexpectedWitness",
    ErrorCode.ErrInvalidWitnessCommitment: "ErrInvalidWitnessCommitment",
    ErrorCode.ErrWitnessCommitmentMismatch: "ErrWitnessCommitmentMismatch",
    ErrorCode.ErrPreviousBlockUnknown: "ErrPreviousBlockUnknown",
    ErrorCode.ErrInvalidAncestorBlock: "ErrInvalidAncestorBlock",
    ErrorCode.ErrPrevBlockNotBest: "ErrPrevBlockNotBest",
}


class RuleError(Exception):
    def __init__(self, c, desc=None, err=None):
        """

        :param ErrorCode c:
        :param str desc:
        """

        self.c = c
        self.desc = desc or ""
        self.err = err

    def __eq__(self, other):
        return self.c == other.c and self.desc == other.desc

    def __repr__(self):
        return "RuleError(ErrorCode={}, desc={})".format(str(self.c), self.desc or "\"\"")

    def __str__(self):
        return "RuleError(ErrorCode={}, desc={})".format(str(self.c), self.desc or "\"\"")

    def __hash__(self):
        return hash(str(self.c) + str(self.desc))


# errDeserialize signifies that a problem was encountered when deserializing
# data.
class DeserializeError(Exception):
    def __init__(self, msg=None, err=None, extra=None):
        """

        :param str msg:
        :param Exception err:
        :param extra:
        """

        self.msg = msg or ""
        self.err = err
        self.extra = extra

    def __repr__(self):
        return "DeserializeError(msg={})".format(self.msg or "\"\"")

    def __str__(self):
        return "DeserializeError(msg={})".format(self.msg or "\"\"")

    def __hash__(self):
        return hash(str(self.msg))


class NormalError(Exception):
    def __init__(self, msg=None, err=None, extra=None):
        """

        :param str msg:
        :param Exception err:
        :param extra:
        """

        self.msg = msg or ""
        self.err = err
        self.extra = extra

    def __repr__(self):
        return "NormalError(msg={})".format(self.msg or "\"\"")

    def __str__(self):
        return "NormalError(msg={})".format(self.msg or "\"\"")

    def __hash__(self):
        return hash(str(self.msg))


class InterruptRequestedError(Exception):
    def __init__(self, msg=None, err=None, extra=None):
        """

        :param str msg:
        :param Exception err:
        :param extra:
        """

        self.msg = msg or "interrupt requested"
        self.err = err
        self.extra = extra

    def __repr__(self):
        return "InterruptRequestedError(msg={})".format(self.msg or "\"\"")

    def __str__(self):
        return "InterruptRequestedError(msg={})".format(self.msg or "\"\"")

    def __hash__(self):
        return hash(str(self.msg))
