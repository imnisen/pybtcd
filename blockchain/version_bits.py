import pyutil
from .threshold_state import *

# vbLegacyBlockVersion is the highest legacy block version before the
# version bits scheme became active.
vbLegacyBlockVersion = 4

# vbTopBits defines the bits to set in the version to signal that the
# version bits scheme is being used.
vbTopBits = 0x20000000

# vbTopMask is the bitmask to use to determine whether or not the
# version bits scheme is in use.
vbTopMask = 0xe0000000

# vbNumBits is the total number of bits available for use with the
# version bits scheme.
vbNumBits = 29

# unknownVerNumToCheck is the number of previous blocks to consider
# when checking for a threshold of unknown block versions for the
# purposes of warning the user.
unknownVerNumToCheck = 100

# unknownVerWarnNum is the threshold of previous blocks that have an
# unknown version to use for the purposes of warning the user.
unknownVerWarnNum = unknownVerNumToCheck / 2


# bitConditionChecker provides a thresholdConditionChecker which can be used to
# test whether or not a specific bit is set when it's not supposed to be
# according to the expected version based on the known deployments and the
# current state of the chain.  This is useful for detecting and warning about
# unknown rule activations.
class BitConditionChecker(ThresholdConditionChecker):
    def __init__(self, bit, chain):
        """

        :param int bit:
        :param chain:
        """
        self.bit = bit
        self.chain = chain

    # BeginTime returns the unix timestamp for the median block time after which
    # voting on a rule change starts (at the next window).
    #
    # Since this implementation checks for unknown rules, it returns 0 so the rule
    # is always treated as active.
    #
    # This is part of the thresholdConditionChecker interface implementation.
    def begin_time(self) -> int:
        return 0

    # EndTime returns the unix timestamp for the median block time after which an
    # attempted rule change fails if it has not already been locked in or
    # activated.
    #
    # Since this implementation checks for unknown rules, it returns the maximum
    # possible timestamp so the rule is always treated as active.
    #
    # This is part of the thresholdConditionChecker interface implementation.
    def end_time(self) -> int:
        return pyutil.MaxUint64

    # RuleChangeActivationThreshold is the number of blocks for which the condition
    # must be true in order to lock in a rule change.
    #
    # This implementation returns the value defined by the chain params the checker
    # is associated with.
    #
    # This is part of the thresholdConditionChecker interface implementation.
    def rule_change_activation_threshold(self) -> int:
        return self.chain.chain_params.rule_change_activation_threshold

    # MinerConfirmationWindow is the number of blocks in each threshold state
    # retarget window.
    #
    # This implementation returns the value defined by the chain params the checker
    # is associated with.
    #
    # This is part of the thresholdConditionChecker interface implementation.
    def miner_confirmation_window(self) -> int:
        return self.chain.chain_params.miner_confirmation_window

    # Condition returns true when the specific bit associated with the checker is
    # set and it's not supposed to be according to the expected version based on
    # the known deployments and the current state of the chain.
    #
    # This function MUST be called with the chain state lock held (for writes).
    #
    # This is part of the thresholdConditionChecker interface implementation.
    def condition(self, node):
        condition_mask = 1 << self.bit

        version = node.version

        if version & vbTopMask != vbTopBits:
            return False

        if version & condition_mask == 0:
            return False

        expected_version = self.chain._calc_next_block_version(node.parent)

        return expected_version & condition_mask == 0
