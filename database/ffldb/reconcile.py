from .utils import *

# writeLocKeyName is the key used to store the current write file
# location.
writeLocKeyName = b"ffldb-writeloc"  # TODO need move


# The serialized write cursor location format is:
#
#  [0:4]  Block file (4 bytes)
#  [4:8]  File offset (4 bytes)
#  [8:12] Castagnoli CRC-32 checksum (4 bytes)

# serializeWriteRow serialize the current block file and offset where new
# will be written into a format suitable for storage into the metadata.
def serialize_write_row(cur_block_file_num: int, cur_file_offset: int):
    block_file_bytes = cur_block_file_num.to_bytes(4, "little")
    file_offset_bytes = cur_file_offset.to_bytes(4, "little")
    checksum_bytes = crc32_Castagnoli(block_file_bytes + file_offset_bytes).to_bytes(4,
                                                                                     byteorder="big")  # TODO check the int -> bytes right?
    return block_file_bytes + file_offset_bytes + checksum_bytes


# deserializeWriteRow deserializes the write cursor location stored in the
# metadata.  Returns ErrCorruption if the checksum of the entry doesn't match.
def deserialize_write_row(write_row: bytes):
    # Ensure the checksum matches.  The checksum is at the end.
    got_checksum = crc32_Castagnoli(write_row[:8])
    want_checksum = int.from_bytes(write_row[8:12], "big")
    if got_checksum != want_checksum:
        msg = "metadata for write cursor does not match the expected checksum - got %d, want %d" % (
            got_checksum, want_checksum)
        raise DBError(ErrorCode.ErrCorruption, msg)

    file_num = int.from_bytes(write_row[0:4], "little")
    file_offset = int.from_bytes(write_row[4:8], "little")
    return file_num, file_offset


# reconcileDB reconciles the metadata with the flat block files on disk.
def reconcile_db(pdb):
    cur_file_num, cur_offset = 0, 0

    def f(tx):
        nonlocal cur_file_num, cur_offset

        write_row = tx.metadata().get(writeLocKeyName)
        if write_row is None:
            msg = "write cursor does not exist"
            raise DBError(ErrorCode.ErrCorruption, msg)

        cur_file_num, cur_offset = deserialize_write_row(write_row)

    pdb.view(f)

    # When the write cursor position found by scanning the block files on
    # disk is AFTER the position the metadata believes to be true, truncate
    # the files on disk to match the metadata.  This can be a fairly common
    # occurrence in unclean shutdown scenarios while the block files are in
    # the middle of being written.  Since the metadata isn't updated until
    # after the block data is written, this is effectively just a rollback
    # to the known good point before the unclean shutdown.
    wc = pdb.store.write_cursor
    if wc.cur_file_num > cur_file_num or (wc.cur_file_num == cur_file_num and wc.cur_offset > cur_offset):
        # TOADD loginfo
        # TOADD logdebug
        pdb.store.handle_rollback(cur_file_num, cur_offset)
        # TOADD loginfo

        # When the write cursor position found by scanning the block files on
    # disk is BEFORE the position the metadata believes to be true, return
    # a corruption error.  Since sync is called after each block is written
    # and before the metadata is updated, this should only happen in the
    # case of missing, deleted, or truncated block files, which generally
    # is not an easily recoverable scenario.  In the future, it might be
    # possible to rescan and rebuild the metadata from the block files,
    # however, that would need to happen with coordination from a higher
    # layer since it could invalidate other metadata.
    if wc.cur_file_num < cur_file_num or (wc.cur_file_num == cur_file_num and wc.cur_offset < cur_offset):
        # TOADD log warn
        msg = "metadata claims file %d, offset %d, but block data is at file %d, offset %d" % (cur_file_num, cur_offset,
                                                                                               wc.cur_file_num, wc,
                                                                                               cur_offset)
        raise DBError(ErrorCode.ErrCorruption, msg)

    return pdb
