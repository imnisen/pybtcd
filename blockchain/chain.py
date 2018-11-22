import chainhash
import chaincfg
import wire
import btcutil
import database
import txscript
import pyutil
from .chainio import *


# orphanBlock represents a block that we don't yet have the parent for.  It
# is a normal block plus an expiration time to prevent caching the orphan
# forever.
class OrphanBlock:
    def __init__(self, block, expiration):
        self.block = block
        self.expiration = expiration


# BestState houses information about the current best block and other info
# related to the state of the main chain as it exists from the point of view of
# the current best block.
#
# The BestSnapshot method can be used to obtain access to this information
# in a concurrent safe manner and the data will not be changed out from under
# the caller when chain state changes occur as the function name implies.
# However, the returned snapshot must be treated as immutable since it is
# shared by all callers.
class BestState:
    def __init__(self, hash, height, bits, block_size, block_weight, num_txns, total_txns, media_time):
        """

        :param chainhash.Hash hash:
        :param int32 height:
        :param uint32 bits:
        :param uint64 block_size:
        :param uint64 block_weight:
        :param uint64 num_txns:
        :param uint64 total_txns:
        :param time.Time media_time:
        """
        self.hash = hash  # The hash of the block.
        self.height = height  # The height of the block.
        self.bits = bits  # The difficulty bits of the block.
        self.block_size = block_size  # The size of the block.
        self.block_weight = block_weight  # The weight of the block.
        self.num_txns = num_txns  # The number of txns in the block.
        self.total_txns = total_txns  # The total number of txns in the chain.
        self.media_time = media_time  # Median time as per CalcPastMedianTime.


# SequenceLock represents the converted relative lock-time in seconds, and
# absolute block-height for a transaction input's relative lock-times.
# According to SequenceLock, after the referenced input has been confirmed
# within a block, a transaction spending that input can be included into a
# block either after 'seconds' (according to past median time), or once the
# 'BlockHeight' has been reached.
class SequenceLock:
    def __init__(self, seconds: int, block_height: int):
        """

        :param int64 seconds:
        :param int32 block_height:
        """
        self.seconds = seconds
        self.block_height = block_height


# This is a interface
# IndexManager provides a generic interface that the is called when blocks are
# connected and disconnected to and from the tip of the main chain for the
# purpose of supporting optional indexes.
class IndexManager:
    # TODO
    # Init is invoked during chain initialize in order to allow the index
    # manager to initialize itself and any indexes it is managing.  The
    # channel parameter specifies a channel the caller can close to signal
    # that the process should be interrupted.  It can be nil if that
    # behavior is not desired.
    def __init__(self):
        pass

    # ConnectBlock is invoked when a new block has been connected to the
    # main chain. The set of output spent within a block is also passed in
    # so indexers can access the previous output scripts input spent if
    # required.
    def connect_block(self):
        pass

    # DisconnectBlock is invoked when a block has been disconnected from
    # the main chain. The set of outputs scripts that were spent within
    # this block is also returned so indexers can clean up the prior index
    # state for this block.
    def disconnect_block(self):
        pass


# Config is a descriptor which specifies the blockchain instance configuration.
class Config:
    def __init__(self, db, interrupt, chain_params, checkpoints, time_source, sig_cache, index_manager, hash_cache):
        """

        :param database.DB db:
        :param <-chan struct{} interrupt:
        :param *chaincfg.Params chain_params:
        :param []chaincfg.Checkpoint checkpoints:
        :param MedianTimeSource time_source:
        :param *txscript.SigCache sig_cache:
        :param IndexManager index_manager:
        :param *txscript.HashCache hash_cache:
        """
        # DB defines the database which houses the blocks and will be used to
        # store all metadata created by this package such as the utxo set.
        #
        # This field is required.
        self.db = db

        # Interrupt specifies a channel the caller can close to signal that
        # long running operations, such as catching up indexes or performing
        # database migrations, should be interrupted.
        #
        # This field can be nil if the caller does not desire the behavior.
        self.interrupt = interrupt

        # ChainParams identifies which chain parameters the chain is associated
        # with.
        #
        # This field is required.
        self.chain_params = chain_params

        # Checkpoints hold caller-defined checkpoints that should be added to
        # the default checkpoints in ChainParams.  Checkpoints must be sorted
        # by height.
        #
        # This field can be nil if the caller does not wish to specify any
        # checkpoints.
        self.checkpoints = checkpoints

        # TimeSource defines the median time source to use for things such as
        # block processing and determining whether or not the chain is current.
        #
        # The caller is expected to keep a reference to the time source as well
        # and add time samples from other peers on the network so the local
        # time is adjusted to be in agreement with other peers.
        self.time_source = time_source

        # SigCache defines a signature cache to use when when validating
        # signatures.  This is typically most useful when individual
        # transactions are already being validated prior to their inclusion in
        # a block such as what is usually done via a transaction memory pool.
        #
        # This field can be nil if the caller is not interested in using a
        # signature cache.
        self.sig_cache = sig_cache

        # IndexManager defines an index manager to use when initializing the
        # chain and connecting and disconnecting blocks.
        #
        # This field can be nil if the caller does not wish to make use of an
        # index manager.
        self.index_manager = index_manager

        # HashCache defines a transaction hash mid-state cache to use when
        # validating transactions. This cache has the potential to greatly
        # speed up transaction validation as re-using the pre-calculated
        # mid-state eliminates the O(N^2) validation complexity due to the
        # SigHashAll flag.
        #
        # This field can be nil if the caller is not interested in using a
        # signature cache.
        self.hash_cache = hash_cache


# BlockChain provides functions for working with the bitcoin block chain.
# It includes functionality such as rejecting duplicate blocks, ensuring blocks
# follow all rules, orphan handling, checkpoint handling, and best chain
# selection with reorganization.
class BlockChain:
    def __init__(self,
                 checkpoints=None,
                 checkpoints_by_height=None,
                 db=None,
                 chain_params=None,
                 time_source=None,
                 sig_cache=None,
                 index_manager=None,
                 hash_cache=None,

                 min_retarget_timespan=None,
                 max_retarget_timespan=None,
                 blocks_per_retarget=None,

                 chain_lock=None,

                 index=None,
                 best_chain=None,

                 orphan_lock=None,
                 orphans=None,
                 prev_orphans=None,
                 oldest_orphan=None,

                 next_checkpoint=None,
                 checkpoint_node=None,

                 state_lock=None,
                 state_snapshot=None,

                 warning_caches=None,
                 deployment_caches=None,

                 unknown_rules_warned=None,
                 unknown_version_warned=None,

                 notifications_lock=None,
                 notifications=None,
                 ):
        """
        :param []chaincfg.Checkpoint checkpoints:
        :param map[int32]*chaincfg.Checkpoint checkpoints_by_height:
        :param database.DB db:
        :param *chaincfg.Params chain_params:
        :param MedianTimeSource time_source:
        :param *txscript.SigCache sig_cache:
        :param IndexManager index_manager:
        :param *txscript.HashCache hash_cache:

        :param int64 min_retarget_timespan:
        :param int64 max_retarget_timespan:
        :param int32 blocks_per_retarget:

        :param pyutil.RWLock chain_lock:

        :param *blockIndex index:
        :param *chainView best_chainin:

        :param pyutil.RWLock orphan_lock:
        :param map[chainhash.Hash]*orphanBlock orphans:
        :param map[chainhash.Hash][]*orphanBlock prev_orphans:
        :param *orphanBlock oldest_orphan:

        :param *chaincfg.Checkpointnext_checkpoint:
        :param *blockNode checkpoint_node:

        :param pyutil.RWLockRWLock state_lock:
        :param *BestState stateSnapshot:

        :param []thresholdStateCache warning_caches:
        :param []thresholdStateCache deployment_caches:

        :param bool unknown_rules_warned:
        :param bool unknown_version_warned:

        :param pyutil.RWLockRWLOCK notifications_lock:
        :param []NotificationCallback notifications:


        """

        # The following fields are set when the instance is created and can't
        # be changed afterwards, so there is no need to protect them with a
        # separate mutex.
        self.checkpoints = checkpoints
        self.checkpoints_by_height = checkpoints_by_height
        self.db = db
        self.chain_params = chain_params
        self.time_source = time_source
        self.sig_cache = sig_cache
        self.index_manager = index_manager
        self.hash_cache = hash_cache

        # The following fields are calculated based upon the provided chain
        # parameters.  They are also set when the instance is created and
        # can't be changed afterwards, so there is no need to protect them with
        # a separate mutex.
        self.min_retarget_timespan = min_retarget_timespan  # target timespan / adjustment factor
        self.max_retarget_timespan = max_retarget_timespan  # target timespan * adjustment factor
        self.blocks_per_retarget = blocks_per_retarget  # target timespan / target time per block

        # chainLock protects concurrent access to the vast majority of the
        # fields in this struct below this point.
        self.chain_lock = chain_lock or pyutil.RWLock()

        # These fields are related to the memory block index.  They both have
        # their own locks, however they are often also protected by the chain
        # lock to help prevent logic races when blocks are being processed.
        #
        # index houses the entire block index in memory.  The block index is
        # a tree-shaped structure.
        #
        # bestChain tracks the current active chain by making use of an
        # efficient chain view into the block index.
        self.index = index
        self.best_chain = best_chain

        # These fields are related to handling of orphan blocks.  They are
        # protected by a combination of the chain lock and the orphan lock.
        self.orphan_lock = orphan_lock or pyutil.RWLock()
        self.orphans = orphans
        self.prev_orphans = prev_orphans
        self.oldest_orphan = oldest_orphan

        # These fields are related to checkpoint handling.  They are protected
        # by the chain lock.
        self.next_checkpoint = next_checkpoint
        self.checkpoint_node = checkpoint_node

        # The state is used as a fairly efficient way to cache information
        # about the current best chain state that is returned to callers when
        # requested.  It operates on the principle of MVCC such that any time a
        # new block becomes the best block, the state pointer is replaced with
        # a new struct and the old state is left untouched.  In this way,
        # multiple callers can be pointing to different best chain states.
        # This is acceptable for most callers because the state is only being
        # queried at a specific point in time.
        #
        # In addition, some of the fields are stored in the database so the
        # chain state can be quickly reconstructed on load.
        self.state_lock = state_lock or pyutil.RWLock()
        self.state_snapshot = state_snapshot

        # The following caches are used to efficiently keep track of the
        # current deployment threshold state of each rule change deployment.
        #
        # This information is stored in the database so it can be quickly
        # reconstructed on load.
        #
        # warningCaches caches the current deployment threshold state for blocks
        # in each of the **possible** deployments.  This is used in order to
        # detect when new unrecognized rule changes are being voted on and/or
        # have been activated such as will be the case when older versions of
        # the software are being used
        #
        # deploymentCaches caches the current deployment threshold state for
        # blocks in each of the actively defined deployments.
        self.warning_caches = warning_caches
        self.deployment_caches = deployment_caches

        # The following fields are used to determine if certain warnings have
        # already been shown.
        #
        # unknownRulesWarned refers to warnings due to unknown rules being
        # activated.
        #
        # unknownVersionsWarned refers to warnings due to unknown versions
        # being mined.
        self.unknown_rules_warned = unknown_rules_warned
        self.unknown_version_warned = unknown_version_warned

        # The notifications field stores a slice of callbacks to be executed on
        # certain blockchain events.
        self.notifications_lock = notifications_lock or pyutil.RWLock()
        self.notifications = notifications

    # blockExists determines whether a block with the given hash exists either in
    # the main chain or any side chains.
    #
    # This function is safe for concurrent access.
    def _block_exists(self, hash: chainhash.Hash) -> bool:
        # Check block index first (could be main chain or side chain blocks).
        if self.index.have_block(hash):
            return True

        # Check in the database
        exists = False

        def f(db_tx: database.Tx):
            nonlocal exists
            exists = db_tx.has_block(hash)

            if not exists:
                return

            # Ignore side chain blocks in the database.  This is necessary
            # because there is not currently any record of the associated
            # block index data such as its block height, so it's not yet
            # possible to efficiently load the block and do anything useful
            # with it.
            #
            # Ultimately the entire block index should be serialized
            # instead of only the current main chain so it can be consulted
            # directly.
            try:
                db_fetch_height_by_hash(db_tx, hash)
            except NotInMainChainErr as e:
                exists = False
                return

        self.db.view(f)

        return exists

    # HaveBlock returns whether or not the chain instance has the block represented
    # by the passed hash.  This includes checking the various places a block can
    # be like part of the main chain, on a side chain, or in the orphan pool.
    #
    # This function is safe for concurrent access.
    def have_block(self, hash: chainhash.Hash) -> bool:
        return self._block_exists(hash) or self.is_known_orphan(hash)

    # IsKnownOrphan returns whether the passed hash is currently a known orphan.
    # Keep in mind that only a limited number of orphans are held onto for a
    # limited amount of time, so this function must not be used as an absolute
    # way to test if a block is an orphan block.  A full block (as opposed to just
    # its hash) must be passed to ProcessBlock for that purpose.  However, calling
    # ProcessBlock with an orphan that already exists results in an error, so this
    # function provides a mechanism for a caller to intelligently detect *recent*
    # duplicate orphans and react accordingly.
    #
    # This function is safe for concurrent access.
    def is_known_orphan(self, hash: chainhash.Hash) -> bool:
        # Protect concurrent access.  Using a read lock only so multiple
        # readers can query without blocking each other.
        self.orphan_lock.r_lock()
        exists = hash in self.orphans
        self.orphan_lock.r_unlock()
        return exists

    # GetOrphanRoot returns the head of the chain for the provided hash from the
    # map of orphan blocks.
    #
    # This function is safe for concurrent access.
    def get_orphan_root(self, hash: chainhash.Hash):
        self.orphan_lock.r_lock()  # TOCHANGE use `with`
        try:
            orphan_root = hash
            prev_hash = hash
            while prev_hash in self.orphans:
                orphan = self.orphans[prev_hash]
                orphan_root = prev_hash
                prev_hash = orphan.block.msg_block().header.prev_block
            return orphan_root
        finally:
            self.orphan_lock.r_unlock()

    # removeOrphanBlock removes the passed orphan block from the orphan pool and
    # previous orphan index.
    def remove_orphan_block(self, orphan: OrphanBlock):
        self.orphan_lock.lock()
        try:
            # Remove the orphan block from the orphan pool.
            orphan_hash = orphan.block.hash()
            del self.orphans[orphan_hash]

            # Remove the reference from the previous orphan index too.  An indexing
            # for loop is intentionally used over a range here as range does not
            # reevaluate the slice on each iteration nor does it adjust the index
            # for the modified slice.
            prev_hash = orphan.block.msg_block().header.prev_block
            orphans = self.prev_orphans[prev_hash]

            orphans = [x for x in orphans if x.block.hash() != orphan_hash]
            self.prev_orphans[prev_hash] = orphans

            # Remove the map entry altogether if there are no longer any orphans
            # which depend on the parent hash.
            if len(self.prev_orphans[prev_hash]) == 0:
                del self.prev_orphans[prev_hash]

            return
        finally:
            self.orphan_lock.unlock()

    # addOrphanBlock adds the passed block (which is already determined to be
    # an orphan prior calling this function) to the orphan pool.  It lazily cleans
    # up any expired blocks so a separate cleanup poller doesn't need to be run.
    # It also imposes a maximum limit on the number of outstanding orphan
    # blocks and will remove the oldest received orphan block if the limit is
    # exceeded.
    def add_orphan_block(self):
        pass

    # CalcSequenceLock computes a relative lock-time SequenceLock for the passed
    # transaction using the passed UtxoViewpoint to obtain the past median time
    # for blocks in which the referenced inputs of the transactions were included
    # within. The generated SequenceLock lock can be used in conjunction with a
    # block height, and adjusted median block time to determine if all the inputs
    # referenced within a transaction have reached sufficient maturity allowing
    # the candidate transaction to be included in a block.
    #
    # This function is safe for concurrent access.
    def calc_sequence_lock(self, tx, utxo, mempool):
        pass

    def _calc_sequence_lock(self, node, tx, utxo, mempool):
        pass

    # getReorganizeNodes finds the fork point between the main chain and the passed
    # node and returns a list of block nodes that would need to be detached from
    # the main chain and a list of block nodes that would need to be attached to
    # the fork point (which will be the end of the main chain after detaching the
    # returned list of block nodes) in order to reorganize the chain such that the
    # passed node is the new end of the main chain.  The lists will be empty if the
    # passed node is not on a side chain.
    #
    # This function may modify node statuses in the block index without flushing.
    #
    # This function MUST be called with the chain state lock held (for reads).
    def get_reorganize_nodes(self, node):
        pass

    # connectBlock handles connecting the passed node/block to the end of the main
    # (best) chain.
    #
    # This passed utxo view must have all referenced txos the block spends marked
    # as spent and all of the new txos the block creates added to it.  In addition,
    # the passed stxos slice must be populated with all of the information for the
    # spent txos.  This approach is used because the connection validation that
    # must happen prior to calling this function requires the same details, so
    # it would be inefficient to repeat it.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def connect_block(self, node, block, view, stxos):
        pass

    # disconnectBlock handles disconnecting the passed node/block from the end of
    # the main (best) chain.
    #
    # This function MUST be called with the chain state lock held (for writes)
    def disconnect_block(self, node, block, view):
        pass

    # countSpentOutputs returns the number of utxos the passed block spends.
    def count_spent_outputs(self, block):
        pass

    # reorganizeChain reorganizes the block chain by disconnecting the nodes in the
    # detachNodes list and connecting the nodes in the attach list.  It expects
    # that the lists are already in the correct order and are in sync with the
    # end of the current best chain.  Specifically, nodes that are being
    # disconnected must be in reverse order (think of popping them off the end of
    # the chain) and nodes the are being attached must be in forwards order
    # (think pushing them onto the end of the chain).
    #
    # This function may modify node statuses in the block index without flushing.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def reorganize_chain(self, detach_nodes, attach_nodes):
        pass

    # connectBestChain handles connecting the passed block to the chain while
    # respecting proper chain selection according to the chain with the most
    # proof of work.  In the typical case, the new block simply extends the main
    # chain.  However, it may also be extending (or creating) a side chain (fork)
    # which may or may not end up becoming the main chain depending on which fork
    # cumulatively has the most proof of work.  It returns whether or not the block
    # ended up on the main chain (either due to extending the main chain or causing
    # a reorganization to become the main chain).
    #
    # The flags modify the behavior of this function as follows:
    #  - BFFastAdd: Avoids several expensive transaction validation operations.
    #    This is useful when using checkpoints.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def connect_best_chain(self, node, block, flags):
        pass

    # isCurrent returns whether or not the chain believes it is current.  Several
    # factors are used to guess, but the key factors that allow the chain to
    # believe it is current are:
    #  - Latest block height is after the latest checkpoint (if enabled)
    #  - Latest block has a timestamp newer than 24 hours ago
    #
    # This function MUST be called with the chain state lock held (for reads).
    def _is_current(self):
        pass

    # IsCurrent returns whether or not the chain believes it is current.  Several
    # factors are used to guess, but the key factors that allow the chain to
    # believe it is current are:
    #  - Latest block height is after the latest checkpoint (if enabled)
    #  - Latest block has a timestamp newer than 24 hours ago
    #
    # This function is safe for concurrent access.
    def is_current(self):
        pass

    # BestSnapshot returns information about the current best chain block and
    # related state as of the current point in time.  The returned instance must be
    # treated as immutable since it is shared by all callers.
    #
    # This function is safe for concurrent access.
    def best_snapshot(self):
        pass

    # HeaderByHash returns the block header identified by the given hash or an
    # error if it doesn't exist. Note that this will return headers from both the
    # main and side chains.
    def header_by_hash(self, hash):
        pass

    # MainChainHasBlock returns whether or not the block with the given hash is in
    # the main chain.
    #
    # This function is safe for concurrent access.
    def main_chain_hash_block(self, hash):
        pass

    # BlockLocatorFromHash returns a block locator for the passed block hash.
    # See BlockLocator for details on the algorithm used to create a block locator.
    #
    # In addition to the general algorithm referenced above, this function will
    # return the block locator for the latest known tip of the main (best) chain if
    # the passed hash is not currently known.
    #
    # This function is safe for concurrent access.
    def block_locator_from_hash(self, hash):
        pass

    # LatestBlockLocator returns a block locator for the latest known tip of the
    # main (best) chain.
    #
    # This function is safe for concurrent access.
    def lastest_block_locator(self):
        pass

    # BlockHeightByHash returns the height of the block with the given hash in the
    # main chain.
    #
    # This function is safe for concurrent access.
    def block_height_by_hash(self, hash):
        pass

    # BlockHashByHeight returns the hash of the block at the given height in the
    # main chain.
    #
    # This function is safe for concurrent access.
    def block_hash_by_height(self, block_height):
        pass

    # HeightRange returns a range of block hashes for the given start and end
    # heights.  It is inclusive of the start height and exclusive of the end
    # height.  The end height will be limited to the current main chain height.
    #
    # This function is safe for concurrent access.
    def height_range(self, start_height, end_height):
        pass

    # HeightToHashRange returns a range of block hashes for the given start height
    # and end hash, inclusive on both ends.  The hashes are for all blocks that are
    # ancestors of endHash with height greater than or equal to startHeight.  The
    # end hash must belong to a block that is known to be valid.
    #
    # This function is safe for concurrent access.
    def height_to_hash_range(self, start_height, end_height, max_results):
        pass

    # IntervalBlockHashes returns hashes for all blocks that are ancestors of
    # endHash where the block height is a positive multiple of interval.
    #
    # This function is safe for concurrent access.
    def interval_block_hashes(self, end_hash, interval):
        pass

        # TODO


def lock_time_to_sequence(is_seconds: bool, locktime: int):
    pass
