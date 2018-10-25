from enum import Flag, auto
import chainhash


# ThresholdState define the various threshold states used when voting on
# consensus changes.
class ThresholdState(Flag):
    # ThresholdDefined is the first state for each deployment and is the
    # state for the genesis block has by definition for all deployments.
    ThresholdDefined = 0

    # ThresholdStarted is the state for a deployment once its start time
    # has been reached.
    ThresholdStarted = auto()

    # ThresholdLockedIn is the state for a deployment during the retarget
    # period which is after the ThresholdStarted state period and the
    # number of blocks that have voted for the deployment equal or exceed
    # the required number of votes for the deployment.
    ThresholdLockedIn = auto()

    # ThresholdActive is the state for a deployment for all blocks after a
    # retarget period in which the deployment was in the ThresholdLockedIn
    # state.
    ThresholdActive = auto()

    # ThresholdFailed is the state for a deployment once its expiration
    # time has been reached and it did not reach the ThresholdLockedIn
    # state.
    ThresholdFailed = auto()

    # numThresholdsStates is the maximum number of threshold states used in
    # tests.
    numThresholdsStates = auto()

    def __str__(self):
        if self == ThresholdState.numThresholdsStates:
            return "Unknown ThresholdState %s" % self
        else:
            return str(self.name)


# thresholdStateCache provides a type to cache the threshold states of each
# threshold window for a set of IDs.
class ThresholdStateCache:
    def __init__(self, entries):
        """

        :param map[chainhash.Hash]ThresholdState entries:
        """
        self.entries = entries

    # Lookup returns the threshold state associated with the given hash along with
    # a boolean that indicates whether or not it is valid.
    def loop_up(self, hash: chainhash.Hash):
        return self.entries.get(hash)

    # Update updates the cache to contain the provided hash to threshold state
    # mapping.
    def update(self, hash: chainhash.Hash, state: ThresholdState):
        self.entries[hash] = state
        return


    # TODO TOADD some method to add to blockchain class

# An interface
# thresholdConditionChecker provides a generic interface that is invoked to
# determine when a consensus rule change threshold should be changed.
class ThresholdConditionChecker:
    # BeginTime returns the unix timestamp for the median block time after
    # which voting on a rule change starts (at the next window).
    def begin_time(self) -> int:
        pass

    # EndTime returns the unix timestamp for the median block time after
    # which an attempted rule change fails if it has not already been
    # locked in or activated.
    def end_time(self):
        pass

    # RuleChangeActivationThreshold is the number of blocks for which the
    # condition must be true in order to lock in a rule change.
    def rule_change_activation_threshold(self):
        pass

    # MinerConfirmationWindow is the number of blocks in each threshold
    # state retarget window.
    def miner_confirmation_window(self):
        pass

    # Condition returns whether or not the rule change activation condition
    # has been met.  This typically involves checking whether or not the
    # bit associated with the condition is set, but can be more complex as
    # needed.
    def condition(self, node) -> bool:
        pass
