# BehaviorFlags is a bitmask defining tweaks to the normal behavior when
# performing chain processing and consensus rules checks.
class BehaviorFlags(int):
    pass


# BFFastAdd may be set to indicate that several checks can be avoided
# for the block since it is already known to fit into the chain due to
# already proving it correct links into the chain up to a known
# checkpoint.  This is primarily used for headers-first mode.
BFFastAdd = BehaviorFlags(1 << 0)

# BFNoPoWCheck may be set to indicate the proof of work check which
# ensures a block hashes to a value less than the required target will
# not be performed.
BFNoPoWCheck = BehaviorFlags(1 << 1)

# BFNone is a convenience value to specifically indicate no flags.
BFNone = BehaviorFlags(0)
