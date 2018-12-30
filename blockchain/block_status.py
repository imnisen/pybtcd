from enum import Flag


# blockStatus is a bit field representing the validation state of the block.
class BlockStatus(Flag):
    # statusDataStored indicates that the block's payload is stored on disk.
    statusDataStored = 1 << 0

    # statusValid indicates that the block has been fully validated.
    statusValid = 1 << 1

    # statusValidateFailed indicates that the block has failed validation.
    statusValidateFailed = 1 << 2

    # statusInvalidAncestor indicates that one of the block's ancestors has
    # has failed validation, thus the block is also invalid.
    statusInvalidAncestor = 1 << 3

    # statusNone indicates that the block has no validation state flags set.
    #
    # NOTE: This must be defined last in order to avoid influencing iota.
    statusNone = 0

    # HaveData returns whether the full block data is stored in the database. This
    # will return false for a block node where only the header is downloaded or
    # kept.
    def have_data(self) -> bool:
        return self & BlockStatus.statusDataStored != BlockStatus(0)

    # KnownValid returns whether the block is known to be valid. This will return
    # false for a valid block that has not been fully validated yet.
    def known_valid(self) -> bool:
        return self & BlockStatus.statusValid != BlockStatus(0)

    # KnownInvalid returns whether the block is known to be invalid. This may be
    # because the block itself failed validation or any of its ancestors is
    # invalid. This will return false for invalid blocks that have not been proven
    # invalid yet.
    def known_invalid(self) -> bool:
        return self & (BlockStatus.statusValidateFailed | BlockStatus.statusInvalidAncestor) != BlockStatus(0)

    def to_bytes(self):
        return self.value.to_bytes(1, "little")
