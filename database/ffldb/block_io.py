import os
from database.error import *
import pyutil
from collections import deque
import chainhash
from .utils import *
import wire
import io

import logging

_logger = logging.getLogger(__name__)

# ************************************************
#   Some constants
# ************************************************

# The Bitcoin protocol encodes block height as int32, so max number of
# blocks is 2^31.  Max block size per the protocol is 32MiB per block.
# So the theoretical max at the time this comment was written is 64PiB
# (pebibytes).  With files @ 512MiB each, this would require a maximum
# of 134,217,728 files.  Thus, choose 9 digits of precision for the
# filenames.  An additional benefit is 9 digits provides 10^9 files @
# 512MiB each for a total of ~476.84PiB (roughly 7.4 times the current
# theoretical max), so there is room for the max block size to grow in
# the future.
blockFilenameTemplate = "%09d.fdb"

# maxOpenFiles is the max number of open files to maintain in the
# open blocks cache.  Note that this does not include the current
# write file, so there will typically be one more than this value open.
maxOpenFiles = 25

# maxBlockFileSize is the maximum size for each file used to store
# blocks.
#
# NOTE: The current code uses uint32 for all offsets, so this value
# must be less than 2^32 (4 GiB).  This is also why it's a typed
# constant.
maxBlockFileSize = 512 * 1024 * 1024  # 512 Mi

# byteOrder is the preferred byte order used through the database and
# block files.  Sometimes big endian will be used to allow ordered byte
# sortable integer values.
byteOrder = "little"


# Make the api better to use
class LRUList(deque):
    def move_tp_front(self, ele):
        self.remove(ele)
        self.appendleft(ele)


# blockLocation identifies a particular block file and location.
class BlockLocation:
    def __init__(self, block_file_num=None, file_offset=None, block_len=None):
        """
        
        :param uint32 block_file_num:
        :param uint32 file_offset:
        :param uint32 block_len:
        """
        self.block_file_num = block_file_num or 0
        self.file_offset = file_offset or 0
        self.block_len = block_len or 0

    # serializeBlockLoc returns the serialization of the passed block location.
    # This is data to be stored into the block index metadata for each block.
    def serialize(self):
        # The serialized block location format is:
        #
        #  [0:4]  Block file (4 bytes)
        #  [4:8]  File offset (4 bytes)
        #  [8:12] Block length (4 bytes)
        s = io.BytesIO()
        s.write(self.block_file_num.to_bytes(4, byteOrder))
        s.write(self.file_offset.to_bytes(4, byteOrder))
        s.write(self.block_len.to_bytes(4, byteOrder))
        return s.getvalue()

    # deserializeBlockLoc deserializes the passed serialized block location
    # information.  This is data stored into the block index metadata for each
    # block.  The serialized data passed to this function MUST be at least
    # blockLocSize bytes or it will panic.  The error check is avoided here because
    # this information will always be coming from the block index which includes a
    # checksum to detect corruption.  Thus it is safe to use this unchecked here
    def deserialize(self, serialized_data: bytes):
        # The serialized block location format is:
        #
        #  [0:4]  Block file (4 bytes)
        #  [4:8]  File offset (4 bytes)
        #  [8:12] Block length (4 bytes)
        self.block_file_num = int.from_bytes(serialized_data[0:4], byteOrder)
        self.file_offset = int.from_bytes(serialized_data[4:8], byteOrder)
        self.block_len = int.from_bytes(serialized_data[8:12], byteOrder)
        return self


def block_file_path(db_path: str, file_num: int) -> str:
    file_name = blockFilenameTemplate % file_num
    return os.path.join(db_path, file_name)


# Filer class

class FilerErr(Exception):
    pass


class Filer:
    def __init__(self, fo):
        self.__file = fo

    def check_valid(self):
        if self.__file is None:
            raise FilerErr

    def reader_at(self, l: int, off: int) -> int:
        self.check_valid()

        if off < 0:
            raise FilerErr("negative offset")

        if l <= 0:
            raise FilerErr("read length not positive")

        before = self.__file.seek(off)
        content = self.__file.read(l)
        after = self.__file.tell()

        if len(content) != l:
            raise FilerErr("cannot read full length")

        if after - before != l:
            raise FilerErr("read off not match")

        return content

    def writer_at(self, b: bytes, off: int) -> int:
        self.check_valid()

        if off < 0:
            raise FilerErr("negative offset")

        before = self.__file.seek(off)
        write_len = self.__file.write(b)
        after = self.__file.tell()

        if write_len != len(b):
            raise FilerErr("cannot write full b")

        if after - before != len(b):
            raise FilerErr("write off not match")

        return write_len

    def close(self):
        self.check_valid()
        try:
            self.__file.close()
        except:
            pass

    def truncate(self, size: int):
        self.check_valid()
        self.__file.truncate(size)

    def sync(self):
        self.check_valid()
        self.__file.flush()


# lockableFile represents a block file on disk that has been opened for either
# read or read/write access.  It also contains a read-write mutex to support
# multiple concurrent readers.
class LockableFile:
    def __init__(self, lock=None, file=None):
        """

        :param pyutil.RWLock lock:
        :param Filer file:
        """
        self._lock = lock or pyutil.RWLock()
        self.file = file

    def lock(self):
        self._lock.writer_acquire()

    def unlock(self):
        self._lock.writer_release()

    def r_lock(self):
        self._lock.reader_acquire()

    def r_unlock(self):
        self._lock.reader_release()


# writeCursor represents the current file and offset of the block file on disk
# for performing all writes. It also contains a read-write mutex to support
# multiple concurrent readers which can reuse the file handle.
class WriterCursor:
    def __init__(self, cur_file, cur_file_num=None, cur_offset=None, lock=None):
        """

        :param pyutil.RWLOCK lock:
        :param LockableFile cur_file:
        :param int cur_file_num:
        :param int cur_offset:
        """
        self._lock = lock or pyutil.RWLock()

        # curFile is the current block file that will be appended to when
        # writing new blocks.
        self.cur_file = cur_file

        # curFileNum is the current block file number and is used to allow
        # readers to use the same open file handle.
        self.cur_file_num = cur_file_num or 0

        # curOffset is the offset in the current write block file where the
        # next new block will be written.
        self.cur_offset = cur_offset or 0

    def lock(self):
        self._lock.lock()

    def unlock(self):
        self._lock.unlock()

    def r_lock(self):
        self._lock.r_lock()

    def r_unlock(self):
        self._lock.r_unlock()


# blockStore houses information used to handle reading and writing blocks (and
# part of blocks) into flat files with support for multiple concurrent readers.
class BlockStore:
    def __init__(self, network, base_path, max_block_file_size,
                 obf_mutex=None, lru_mutex=None, open_blocks_lru=None, file_num_to_lru_elem=None, open_block_files=None,
                 write_cursor=None,
                 open_file_func=None, open_write_file_func=None, delete_file_func=None):
        """

        :param wire.BitcoinNet  network:
        :param string           base_path:
        :param maxBlockFileSize max_block_file_size:
        :param RWLock           obf_mutex:
        :param Lock             lru_mutex:
        :param LRUList            open_blocks_lru:
        :param map[uint32]*list.Element  file_num_to_lru_elem:
        :param map[uint32]*LockableFile  open_block_files:
        :param WriterCursor              write_cursor:
        :param func(fileNum uint32) (*lockableFile, error) open_file_func:
        :param func(fileNum uint32) (filer, error)         open_write_file_func:
        :param func(fileNum uint32) error                   delete_file_func:
        """

        # network is the specific network to use in the flat files for each
        # block.
        self.network = network

        # basePath is the base path used for the flat block files and metadata.
        self.base_path = base_path

        # maxBlockFileSize is the maximum size for each file used to store
        # blocks.  It is defined on the store so the whitebox tests can
        # override the value.
        self.max_block_file_size = max_block_file_size

        # The following fields are related to the flat files which hold the
        # actual blocks.   The number of open files is limited by maxOpenFiles.
        #
        # obfMutex protects concurrent access to the openBlockFiles map.  It is
        # a RWMutex so multiple readers can simultaneously access open files.
        #
        # openBlockFiles houses the open file handles for existing block files
        # which have been opened read-only along with an individual RWMutex.
        # This scheme allows multiple concurrent readers to the same file while
        # preventing the file from being closed out from under them.
        #
        # lruMutex protects concurrent access to the least recently used list
        # and lookup map.
        #
        # openBlocksLRU tracks how the open files are refenced by pushing the
        # most recently used files to the front of the list thereby trickling
        # the least recently used files to end of the list.  When a file needs
        # to be closed due to exceeding the the max number of allowed open
        # files, the one at the end of the list is closed.
        #
        # fileNumToLRUElem is a mapping between a specific block file number
        # and the associated list element on the least recently used list.
        #
        # Thus, with the combination of these fields, the database supports
        # concurrent non-blocking reads across multiple and individual files
        # along with intelligently limiting the number of open file handles by
        # closing the least recently used files as needed.
        #
        # NOTE: The locking order used throughout is well-defined and MUST be
        # followed.  Failure to do so could lead to deadlocks.  In particular,
        # the locking order is as follows:
        #   1) obfMutex
        #   2) lruMutex
        #   3) writeCursor mutex
        #   4) specific file mutexes
        #
        # None of the mutexes are required to be locked at the same time, and
        # often aren't.  However, if they are to be locked simultaneously, they
        # MUST be locked in the order previously specified.
        #
        # Due to the high performance and multi-read concurrency requirements,
        # write locks should only be held for the minimum time necessary.
        self.obf_mutex = obf_mutex or pyutil.RWLock()
        self.lru_mutex = lru_mutex or pyutil.Lock()
        self.open_blocks_lru = open_blocks_lru or LRUList()
        self.file_num_to_lru_elem = file_num_to_lru_elem or {}
        self.open_block_files = open_block_files or {}

        # writeCursor houses the state for the current file and location that
        # new blocks are written to.
        self.write_cursor = write_cursor

        # These functions are set to openFile, openWriteFile, and deleteFile by
        # default, but are exposed here to allow the whitebox tests to replace
        # them when working with mock files.
        self.open_file_func = open_file_func
        self.open_write_file_func = open_write_file_func
        self.delete_file_func = delete_file_func

    # scanBlockFiles searches the database directory for all flat block files to
    # find the end of the most recent file.  This position is considered the
    # current write cursor which is also stored in the metadata.  Thus, it is used
    # to detect unexpected shutdowns in the middle of writes so the block files
    # can be reconciled.
    @staticmethod
    def scan_block_files(db_path: str):
        last_file = -1
        file_len = 0
        i = 0
        while True:

            file_path = block_file_path(db_path, i)
            try:
                st = os.stat(file_path)
            except Exception:
                break

            last_file = i
            file_len = st.st_size

            i += 1

        _logger.info("Scan found latest block file #%d with length %d" % (last_file, file_len))
        return last_file, file_len

    # newBlockStore returns a new block store with the current block file number
    # and offset set and all fields initialized.
    @classmethod
    def new_from_path_network(cls, base_path: str, network: wire.BitcoinNet) -> 'BlockStore':
        # Look for the end of the latest block to file to determine what the
        # write cursor position is from the viewpoing of the block files on
        # disk.
        file_num, file_off = cls.scan_block_files(base_path)
        if file_num == -1:
            file_num = 0
            file_off = 0

        store = cls(
            network=network,
            base_path=base_path,
            max_block_file_size=maxBlockFileSize,
            open_block_files={},
            open_blocks_lru=LRUList(),
            file_num_to_lru_elem={},
            write_cursor=WriterCursor(
                cur_file=LockableFile(),
                cur_file_num=file_num,
                cur_offset=file_off
            ),
        )
        store.open_file_func = store.open_file
        store.open_write_file_func = store.open_write_file
        store.delete_file_func = store.delete_file
        return store

    # openWriteFile returns a file handle for the passed flat file number in
    # read/write mode.  The file will be created if needed.  It is typically used
    # for the current file that will have all new data appended.  Unlike openFile,
    # this function does not keep track of the open file and it is not subject to
    # the maxOpenFiles limit.
    def open_write_file(self, file_num: int):
        # The current block file needs to be read-write so it is possible to
        # append to it.  Also, it shouldn't be part of the least recently used
        # file.
        file_path = block_file_path(self.base_path, file_num)
        try:
            fo = open(file_path, 'a+b')
            # fd = os.open(file_path, os.O_RDWR | os.O_CREAT | os.O_, mode=0o666)
        except Exception as e:
            msg = "failed to open file %s: %s" % (file_path, e)
            raise DBError(ErrorCode.ErrDriverSpecific, msg, err=e)

        return Filer(fo)

    # openFile returns a read-only file handle for the passed flat file number.
    # The function also keeps track of the open files, performs least recently
    # used tracking, and limits the number of open files to maxOpenFiles by closing
    # the least recently used file as needed.
    #
    # This function MUST be called with the overall files mutex (s.obfMutex) locked
    # for WRITES.
    def open_file(self, file_num: int):
        # Open the appropriate file as read-only.
        file_path = block_file_path(self.base_path, file_num)
        try:
            fo = open(file_path, 'r+b')
            # fd = os.open(file_path)  # TOCHECK the permission right?
        except Exception as e:
            raise DBError(ErrorCode.ErrDriverSpecific, str(e), e)

        block_file = LockableFile(file=Filer(fo))

        # Close the least recently used file if the file exceeds the max
        # allowed open files.  This is not done until after the file open in
        # case the file fails to open, there is no need to close any files.
        #
        # A write lock is required on the LRU list here to protect against
        # modifications happening as already open files are read from and
        # shuffled to the front of the list.
        #
        # Also, add the file that was just opened to the front of the least
        # recently used list to indicate it is the most recently used file and
        # therefore should be closed last.
        self.lru_mutex.acquire()
        lru_list = self.open_blocks_lru

        # TOCHANGE change the lru list operations more LRU style
        if len(lru_list) >= maxOpenFiles:
            lru_file_num = lru_list.pop()
            old_block_file = self.open_block_files[lru_file_num]

            # Close the old file under the write lock for the file in case
            # any readers are currently reading from it so it's not closed
            # out from under them.
            old_block_file.lock.writer_acquire()
            old_block_file.file.close()
            old_block_file.lock.writer_release()

            del self.open_block_files[lru_file_num]
            del self.file_num_to_lru_elem[lru_file_num]

        lru_list.appendleft(file_num)
        self.file_num_to_lru_elem[file_num] = file_num  # stange here, right?
        self.lru_mutex.release()

        # Store a reference to it in the open block files map.
        self.open_block_files[file_num] = block_file
        return block_file

    # deleteFile removes the block file for the passed flat file number.  The file
    # must already be closed and it is the responsibility of the caller to do any
    # other state cleanup necessary.
    def delete_file(self, file_num: int):
        file_path = block_file_path(self.base_path, file_num)
        try:
            os.remove(file_path)
        except Exception as e:
            raise DBError(ErrorCode.ErrDriverSpecific, str(e), e)

        return

    # blockFile attempts to return an existing file handle for the passed flat file
    # number if it is already open as well as marking it as most recently used.  It
    # will also open the file when it's not already open subject to the rules
    # described in openFile.
    #
    # NOTE: The returned block file will already have the read lock acquired and
    # the caller MUST call .RUnlock() to release it once it has finished all read
    # operations.  This is necessary because otherwise it would be possible for a
    # separate goroutine to close the file after it is returned from here, but
    # before the caller has acquired a read lock.
    def block_file(self, file_num: int):
        # When the requested block file is open for writes, return it.
        wc = self.write_cursor
        wc.r_lock()
        if file_num == wc.cur_file_num and wc.cur_file.file is not None:
            obf = wc.cur_file
            obf.r_lock()
            wc.r_unlock()
            return obf

        wc.r_unlock()

        # Try to return an open file under the overall files read lock.
        self.obf_mutex.reader_acquire()
        if file_num in self.open_block_files:
            obf = self.open_block_files[file_num]
            self.lru_mutex.acquire()
            self.open_blocks_lru.move_to_front(self.file_num_to_lru_elem[file_num])
            self.lru_mutex.release()

            obf.r_lock()
            self.obf_mutex.reader_release()
            return obf

        self.obf_mutex.reader_release()

        # Since the file isn't open already, need to check the open block files
        # map again under write lock in case multiple readers got here and a
        # separate one is already opening the file.
        self.obf_mutex.writer_acquire()
        if file_num in self.open_block_files:
            obf = self.open_block_files[file_num]
            obf.r_lock()
            self.obf_mutex.writer_release()
            return obf

        # The file isn't open, so open it while potentially closing the least
        # recently used one as needed.
        try:
            obf = self.open_file_func(file_num)
        except Exception as e:
            self.obf_mutex.writer_release()
            raise e

        obf.r_lock()
        self.obf_mutex.writer_release()
        return obf

    # writeData is a helper function for writeBlock which writes the provided data
    # at the current write offset and updates the write cursor accordingly.  The
    # field name parameter is only used when there is an error to provide a nicer
    # error message.
    #
    # The write cursor will be advanced the number of bytes actually written in the
    # event of failure.
    #
    # NOTE: This function MUST be called with the write cursor current file lock
    # held and must only be called during a write transaction so it is effectively
    # locked for writes.  Also, the write cursor current file must NOT be nil.
    def write_data(self, data: bytes, field_name: str):
        wc = self.write_cursor
        try:
            n = wc.cur_file.file.writer_at(data, wc.cur_offset)  # TOCHECK no write_at
            wc.cur_offset += n
        except Exception as e:
            msg = "failed to write %s to file %d at offset %s: %s" % (
                field_name, wc.cur_file_num, wc.cur_offset, str(e))
            raise DBError(ErrorCode.ErrDriverSpecific, msg, e)

        return

    # writeBlock appends the specified raw block bytes to the store's write cursor
    # location and increments it accordingly.  When the block would exceed the max
    # file size for the current flat file, this function will close the current
    # file, create the next file, update the write cursor, and write the block to
    # the new file.
    #
    # The write cursor will also be advanced the number of bytes actually written
    # in the event of failure.
    #
    # Format: <network><block length><serialized block><checksum>
    def write_block(self, raw_block: bytes):
        # Compute how many bytes will be written.
        # 4 bytes each for block network + 4 bytes for block length +
        # length of raw block + 4 bytes for checksum.
        block_len = len(raw_block)
        full_len = block_len + 12

        # Move to the next block file if adding the new block would exceed the
        # max allowed size for the current block file.  Also detect overflow
        # to be paranoid, even though it isn't possible currently, numbers
        # might change in the future to make it possible.
        #
        # NOTE: The writeCursor.offset field isn't protected by the mutex
        # since it's only read/changed during this function which can only be
        # called during a write transaction, of which there can be only one at
        # a time.
        wc = self.write_cursor
        final_offset = wc.cur_offset + full_len
        if final_offset < wc.cur_offset or final_offset > self.max_block_file_size:
            # This is done under the write cursor lock since the curFileNum
            # field is accessed elsewhere by readers.
            #
            # Close the current write file to force a read-only reopen
            # with LRU tracking.  The close is done under the write lock
            # for the file to prevent it from being closed out from under
            # any readers currently reading from it.
            wc.lock()

            wc.cur_file.lock()
            if wc.cur_file.file is not None:
                try:
                    wc.cur_file.file.close()
                except:
                    pass
                wc.cur_file.file = None

            wc.cur_file.unlock()

            # Start writes into next file.
            wc.cur_file_num += 1
            wc.cur_offset = 0

            wc.unlock()

        # All writes are done under the write lock for the file to ensure any
        # readers are finished and blocked first.
        wc.cur_file.lock()
        try:
            # Open the current file if needed.  This will typically only be the
            # case when moving to the next file to write to or on initial database
            # load.  However, it might also be the case if rollbacks happened after
            # file writes started during a transaction commit.
            if wc.cur_file.file is None:
                file = self.open_write_file_func(wc.cur_file_num)
                wc.cur_file.file = file

            # Bitcoin network.
            orig_offset = wc.cur_offset
            network_bytes = self.network.to_bytes_as_uint32("little")
            self.write_data(network_bytes, field_name="network")

            # Block length.
            block_len_bytes = block_len.to_bytes(4, byteorder="little")
            self.write_data(block_len_bytes, field_name="block length")

            # Serialized block.
            self.write_data(raw_block, field_name="block")

            # Castagnoli CRC-32 as a checksum of all the previous.
            checksum_bytes = crc32_Castagnoli(network_bytes +
                                              block_len_bytes +
                                              raw_block).to_bytes(4,
                                                                  byteorder="big")  # TODO check the int -> bytes right?
            self.write_data(checksum_bytes, field_name="checksum")

            loc = BlockLocation(
                block_file_num=wc.cur_file_num,
                file_offset=orig_offset,
                block_len=full_len
            )
            return loc

        finally:
            wc.cur_file.unlock()

    # readBlock reads the specified block record and returns the serialized block.
    # It ensures the integrity of the block data by checking that the serialized
    # network matches the current network associated with the block store and
    # comparing the calculated checksum against the one stored in the flat file.
    # This function also automatically handles all file management such as opening
    # and closing files as necessary to stay within the maximum allowed open files
    # limit.
    #
    # Returns ErrDriverSpecific if the data fails to read for any reason and
    # ErrCorruption if the checksum of the read data doesn't match the checksum
    # read from the file.
    #
    # Format: <network><block length><serialized block><checksum>

    def read_block(self, hash: chainhash.Hash, loc: BlockLocation):
        # Get the referenced block file handle opening the file as needed.  The
        # function also handles closing files as needed to avoid going over the
        # max allowed open files.
        block_file = self.block_file(loc.block_file_num)

        try:
            need_length = loc.block_len
            serialized_data = block_file.file.reader_at(need_length, loc.file_offset)
        except Exception as e:
            msg = "failed to read block %s from file %d, offset %d: %s" % (hash, loc.block_file_num, loc.file_offset, e)
            raise DBError(ErrorCode.ErrDriverSpecific, msg, e)
        finally:
            block_file.r_unlock()

        # Calculate the checksum of the read data and ensure it matches the
        # serialized checksum.  This will detect any data corruption in the
        # flat file without having to do much more expensive merkle root
        # calculations on the loaded block.
        serialized_checksum = int.from_bytes(serialized_data[-4:], "big")
        calculated_checksum = crc32_Castagnoli(serialized_data[:-4])
        if serialized_checksum != calculated_checksum:
            msg = "block data for block %s checksum does not match - got %x, want %x" % (hash,
                                                                                         calculated_checksum,
                                                                                         serialized_checksum)
            raise DBError(ErrorCode.ErrCorruption, msg)

        # The network associated with the block must match the current active
        # network, otherwise somebody probably put the block files for the
        # wrong network in the directory.
        serialized_net = int.from_bytes(serialized_data[:4], "little")
        if serialized_net != self.network.to_int():
            msg = "block data for block %s is for the wrong network - got %d, want %d" % (
                hash, serialized_net, self.network.to_int())
            raise DBError(ErrorCode.ErrDriverSpecific, msg)

            # The raw block excludes the network, length of the block, and
            # checksum.
        return serialized_data[8: -4]

    # readBlockRegion reads the specified amount of data at the provided offset for
    # a given block location.  The offset is relative to the start of the
    # serialized block (as opposed to the beginning of the block record).  This
    # function automatically handles all file management such as opening and
    # closing files as necessary to stay within the maximum allowed open files
    # limit.
    #
    # Returns ErrDriverSpecific if the data fails to read for any reason.
    def read_block_region(self, loc: BlockLocation, offset: int, num_bytes: int):
        # Get the referenced block file handle opening the file as needed.  The
        # function also handles closing files as needed to avoid going over the
        # max allowed open files.
        block_file = self.block_file(loc.block_file_num)

        # Regions are offsets into the actual block, however the serialized
        # data for a block includes an initial 4 bytes for network + 4 bytes
        # for block length.  Thus, add 8 bytes to adjust.
        read_offset = loc.file_offset + 8 + offset
        try:
            need_length = num_bytes
            serialized_data = block_file.file.reader_at(need_length, read_offset)
        except Exception as e:
            msg = "failed to read region from block file %d, offset %d, len %d: %s" % (
                loc.block_file_num, read_offset, num_bytes, e)
            raise DBError(ErrorCode.ErrDriverSpecific, msg, e)
        finally:
            block_file.r_unlock()

        return serialized_data

    # syncBlocks performs a file system sync on the flat file associated with the
    # store's current write cursor.  It is safe to call even when there is not a
    # current write file in which case it will have no effect.
    #
    # This is used when flushing cached metadata updates to disk to ensure all the
    # block data is fully written before updating the metadata.  This ensures the
    # metadata and block data can be properly reconciled in failure scenarios.
    def sync_blocks(self):
        wc = self.write_cursor
        wc.r_lock()

        # TOCHANGE fucking the defer pattern, try make a better one
        try:
            # Nothing to do if there is no current file associated with the write
            # cursor.
            wc.cur_file.r_lock()
            try:
                if wc.cur_file.file is None:
                    return

                try:
                    wc.cur_file.file.sync()  # TOCHECK no sync() now
                except Exception as e:
                    msg = "failed to sync file %d: %s" % (wc.cur_file_num, e)
                    raise DBError(ErrorCode.ErrDriverSpecific, msg, e)

            finally:
                wc.cur_file.r_unlock()


        finally:
            wc.r_unlock()

        return

    # handleRollback rolls the block files on disk back to the provided file number
    # and offset.  This involves potentially deleting and truncating the files that
    # were partially written.
    #
    # There are effectively two scenarios to consider here:
    #   1) Transient write failures from which recovery is possible
    #   2) More permanent failures such as hard disk death and/or removal
    #
    # In either case, the write cursor will be repositioned to the old block file
    # offset regardless of any other errors that occur while attempting to undo
    # writes.
    #
    # For the first scenario, this will lead to any data which failed to be undone
    # being overwritten and thus behaves as desired as the system continues to run.
    #
    # For the second scenario, the metadata which stores the current write cursor
    # position within the block files will not have been updated yet and thus if
    # the system eventually recovers (perhaps the hard drive is reconnected), it
    # will also lead to any data which failed to be undone being overwritten and
    # thus behaves as desired.
    #
    # Therefore, any errors are simply logged at a warning level rather than being
    # returned since there is nothing more that could be done about it anyways.
    def handle_rollback(self, old_block_file_num: int, old_block_offset: int):
        # Grab the write cursor mutex since it is modified throughout this
        # function.
        wc = self.write_cursor
        wc.lock()
        try:
            # Nothing to do if the rollback point is the same as the current write
            # cursor.
            if wc.cur_file_num == old_block_file_num and wc.cur_offset == old_block_offset:
                return

                # Regardless of any failures that happen below, reposition the write
                # cursor to the old block file and offset.
            try:
                _logger.debug("ROLLBACK: Rolling back to file %d, offset %d" % (old_block_file_num, old_block_offset))

                # Close the current write file if it needs to be deleted.  Then delete
                # all files that are newer than the provided rollback file while
                # also moving the write cursor file backwards accordingly.
                if wc.cur_file_num > old_block_file_num:
                    wc.cur_file.lock()
                    if wc.cur_file.file is not None:
                        try:
                            wc.cur_file.file.close()
                        except:
                            pass
                        wc.cur_file.file = None

                    wc.cur_file.unlock()

                while wc.cur_file_num > old_block_file_num:
                    try:
                        self.delete_file_func(wc.cur_file_num)
                    except Exception as e:
                        _logger.warning(
                            "ROLLBACK: Failed to delete block file number %d: %s" % (wc.cur_file_num, repr(e)))
                        return

                    wc.cur_file_num -= 1

                # Open the file for the current write cursor if needed
                wc.cur_file.lock()
                if wc.cur_file.file is None:
                    try:
                        obf = self.open_write_file_func(wc.cur_file_num)
                    except Exception as e:
                        wc.cur_file.unlock()
                        _logger.warning("ROLLBACK: %s" % repr(e))
                        return
                    wc.cur_file.file = obf

                # Truncate the to the provided rollback offset.
                try:
                    wc.cur_file.file.truncate(old_block_offset)
                except Exception as e:
                    wc.cur_file.unlock()
                    _logger.warning("ROLLBACK: Failed to truncate file %d: %s" % (wc.cur_file_num, repr(e)))
                    return

                # Sync the file to disk
                try:
                    wc.cur_file.file.sync()
                except Exception as e:
                    wc.cur_file.unlock()
                    _logger.warning("ROLLBACK: Failed to sync file %d: %s" % (wc.cur_file_num, repr(e)))
                    return
                wc.cur_file.unlock()

            finally:
                wc.cur_file_num = old_block_file_num
                wc.cur_offset = old_block_offset

        finally:
            wc.unlock()
