import chainhash
import chaincfg
import wire
import btcutil
import database
import txscript
import pyutil
import time
from .chain_view import *
from .utxo_viewpoint import *
from .threshold_state import *
from .error import *
from .version_bits import *
from .weight import *
from .sequence_lock import *
from .validate import *
from .notifications import *
from .checkpoints import *
from .script_val import *

import logging

logger = logging.getLogger(__name__)

# Constants
# maxOrphanBlocks is the maximum number of orphan blocks that can be
# queued.
maxOrphanBlocks = 100


# orphanBlock represents a block that we don't yet have the parent for.  It
# is a normal block plus an expiration time to prevent caching the orphan
# forever.
class OrphanBlock:
    def __init__(self, block, expiration):
        """

        :param btcutil.Block block:
        :param int expiration:
        """
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
    def __init__(self, hash, height, bits, block_size, block_weight, num_txns, total_txns, median_time):
        """

        :param chainhash.Hash hash:
        :param int32 height:
        :param uint32 bits:
        :param uint64 block_size:
        :param uint64 block_weight:
        :param uint64 num_txns:
        :param uint64 total_txns:
        :param time.Time median_time:
        """
        self.hash = hash  # The hash of the block.
        self.height = height  # The height of the block.
        self.bits = bits  # The difficulty bits of the block.
        self.block_size = block_size  # The size of the block.
        self.block_weight = block_weight  # The weight of the block.
        self.num_txns = num_txns  # The number of txns in the block.
        self.total_txns = total_txns  # The total number of txns in the chain.
        self.median_time = median_time  # Median time as per CalcPastMedianTime.


# This is a interface
# IndexManager provides a generic interface that the is called when blocks are
# connected and disconnected to and from the tip of the main chain for the
# purpose of supporting optional indexes.
class IndexManager:
    # Init is invoked during chain initialize in order to allow the index
    # manager to initialize itself and any indexes it is managing.  The
    # channel parameter specifies a channel the caller can close to signal
    # that the process should be interrupted.  It can be nil if that
    # behavior is not desired.
    def __init__(self):
        raise NotImplementedError

    # ConnectBlock is invoked when a new block has been connected to the
    # main chain. The set of output spent within a block is also passed in
    # so indexers can access the previous output scripts input spent if
    # required.
    def connect_block(self, database_tx: database.Tx, block: btcutil.Block, utxo_viewpoint: UtxoViewpoint):
        raise NotImplementedError

    # DisconnectBlock is invoked when a block has been disconnected from
    # the main chain. The set of outputs scripts that were spent within
    # this block is also returned so indexers can clean up the prior index
    # state for this block.
    def disconnect_block(self, database_tx: database.Tx, block: btcutil.Block, utxo_viewpoint: UtxoViewpoint):
        raise NotImplementedError


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
        :param chaincfg.Params chain_params:
        :param MedianTimeSource time_source:
        :param txscript.SigCache sig_cache:
        :param IndexManager index_manager:
        :param txscript.HashCache hash_cache:

        :param int64 min_retarget_timespan:
        :param int64 max_retarget_timespan:
        :param int32 blocks_per_retarget:

        :param pyutil.RWLock chain_lock:

        :param BlockIndex index:
        :param ChainView best_chain:

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
                prev_hash = orphan.block.get_msg_block().header.prev_block
            return orphan_root
        finally:
            self.orphan_lock.r_unlock()

    # removeOrphanBlock removes the passed orphan block from the orphan pool and
    # previous orphan index.
    def _remove_orphan_block(self, orphan: OrphanBlock):
        self.orphan_lock.lock()
        try:
            # Remove the orphan block from the orphan pool.
            orphan_hash = orphan.block.hash()
            del self.orphans[orphan_hash]  # Notice, here destructive modify the orphans array

            # Remove the reference from the previous orphan index too.  An indexing
            # for loop is intentionally used over a range here as range does not
            # reevaluate the slice on each iteration nor does it adjust the index
            # for the modified slice.
            prev_hash = orphan.block.get_msg_block().header.prev_block
            orphans = self.prev_orphans[prev_hash]

            orphans = [x for x in orphans if x.block.hash() != orphan_hash]
            self.prev_orphans[prev_hash] = orphans  # # Notice, here create new orphans array and replace every time

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
    def _add_orphan_block(self, block: btcutil.Block):
        # Remove expired orphan blocks.
        for _, o_block in self.orphans.items():
            if int(time.time()) > o_block.expiration:
                self._remove_orphan_block(o_block)
                continue

            # Update the oldest orphan block pointer so it can be discarded
            # in case the orphan pool fills up.
            if self.oldest_orphan is None or o_block.expiration < self.oldest_orphan.expiration:
                self.oldest_orphan = o_block

        # Limit orphan blocks to prevent memory exhaustion.
        if len(self.orphans) + 1 > maxOrphanBlocks:
            # Remove the oldest orphan to make room for the new one.
            self._remove_orphan_block(self.oldest_orphan)
            self.oldest_orphan = None

        # Protect concurrent access.  This is intentionally done here instead
        # of near the top since removeOrphanBlock does its own locking and
        # the range iterator is not invalidated by removing map entries.
        self.orphan_lock.lock()
        try:
            # Insert the block into the orphan map with an expiration time
            # 1 hour from now.
            expiration = int(time.time()) + 3600
            o_block = OrphanBlock(block=block, expiration=expiration)
            self.orphans[block.hash()] = o_block

            # Add to previous hash lookup index for faster dependency lookups.
            prev_hash = block.get_msg_block().header.prev_block
            self.prev_orphans[prev_hash].append(o_block)
            return

        finally:
            self.orphan_lock.unlock()

    # CalcSequenceLock computes a relative lock-time SequenceLock for the passed
    # transaction using the passed UtxoViewpoint to obtain the past median time
    # for blocks in which the referenced inputs of the transactions were included
    # within. The generated SequenceLock lock can be used in conjunction with a
    # block height, and adjusted median block time to determine if all the inputs
    # referenced within a transaction have reached sufficient maturity allowing
    # the candidate transaction to be included in a block.
    #
    # This function is safe for concurrent access.
    def calc_sequence_lock(self, tx: btcutil.Tx, utxo_view: UtxoViewpoint, mempool: bool) -> SequenceLock:
        self.chain_lock.lock()
        try:
            self._calc_sequence_lock(self.best_chain.tip(), tx, utxo_view, mempool)
        finally:
            self.chain_lock.unlock()

    # calcSequenceLock computes the relative lock-times for the passed
    # transaction. See the exported version, CalcSequenceLock for further details.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _calc_sequence_lock(self, node: BlockNode, tx: btcutil.Tx, utxo_view: UtxoViewpoint, mempool: bool):
        # A value of -1 for each relative lock type represents a relative time
        # lock value that will allow a transaction to be included in a block
        # at any given height or time. This value is returned as the relative
        # lock time in the case that BIP 68 is disabled, or has not yet been
        # activated.
        sequence_lock = SequenceLock(seconds=-1, block_height=-1)

        # The sequence locks semantics are always active for transactions
        # within the mempool.
        csv_soft_fork_active = mempool

        # If we're performing block validation, then we need to query the BIP9
        # state.
        if not csv_soft_fork_active:
            # Obtain the latest BIP9 version bits state for the
            # CSV-package soft-fork deployment. The adherence of sequence
            # locks depends on the current soft-fork state.
            csv_state = self._deployment_state(node.parent, chaincfg.DeploymentCSV)
            csv_soft_fork_active = csv_state == ThresholdState.ThresholdActive

        # If the transaction's version is less than 2, and BIP 68 has not yet
        # been activated then sequence locks are disabled. Additionally,
        # sequence locks don't apply to coinbase transactions Therefore, we
        # return sequence lock values of -1 indicating that this transaction
        # can be included within a block at any given height or time.
        m_tx = tx.get_msg_tx()
        sequence_lock_active = m_tx.version >= 2 and csv_soft_fork_active
        if not sequence_lock_active or is_coin_base(tx):
            return sequence_lock

        # Grab the next height from the PoV of the passed blockNode to use for
        # inputs present in the mempool.
        next_height = node.height + 1

        for tx_in_index, tx_in in enumerate(m_tx.tx_ins):
            utxo = utxo_view.lookup_entry(tx_in.previous_out_point)
            if utxo is None:
                msg = "output %s referenced from transaction %s:%d either does not exist or has already been spent" % (
                    tx_in.previous_out_point, tx.hash(), tx_in_index)
                raise RuleError(ErrorCode.ErrMissingTxOut, msg)

            # If the input height is set to the mempool height, then we
            # assume the transaction makes it into the next block when
            # evaluating its sequence blocks.
            input_height = utxo.get_block_height()
            if input_height == 0x7fffffff:
                input_height = next_height

            # Given a sequence number, we apply the relative time lock
            # mask in order to obtain the time lock delta required before
            # this input can be spent.
            sequence_num = tx_in.sequence
            relative_lock = sequence_num & wire.SequenceLockTimeMask

            if sequence_num & wire.SequenceLockTimeDisabled == wire.SequenceLockTimeDisabled:
                # Relative time locks are disabled for this input, so we can
                # skip any further calculation.
                continue
            elif sequence_num & wire.SequenceLockTimeIsSeconds == wire.SequenceLockTimeIsSeconds:
                # This input requires a relative time lock expressed
                # in seconds before it can be spent.  Therefore, we
                # need to query for the block prior to the one in
                # which this input was included within so we can
                # compute the past median time for the block prior to
                # the one which included this referenced output.
                prev_input_height = input_height - 1
                if prev_input_height < 0:
                    prev_input_height = 0

                block_node = node.ancestor(prev_input_height)
                median_time = block_node.calc_past_median_time()

                # Time based relative time-locks as defined by BIP 68
                # have a time granularity of RelativeLockSeconds, so
                # we shift left by this amount to convert to the
                # proper relative time-lock. We also subtract one from
                # the relative lock to maintain the original lockTime
                # semantics.
                time_lock_seconds = (relative_lock << wire.SequenceLockTimeGranularity) - 1
                time_lock = median_time + time_lock_seconds
                if time_lock > sequence_lock.seconds:
                    sequence_lock.seconds = time_lock
            else:
                # The relative lock-time for this input is expressed
                # in blocks so we calculate the relative offset from
                # the input's height as its converted absolute
                # lock-time. We subtract one from the relative lock in
                # order to maintain the original lockTime semantics.
                block_height = input_height + relative_lock - 1
                if block_height > sequence_lock.block_height:
                    sequence_lock.block_height = block_height

        return sequence_lock

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
    def _get_reorganize_nodes(self, node: BlockNode):
        attach_nodes = []
        detach_nodes = []

        # Do not reorganize to a known invalid chain. Ancestors deeper than the
        # direct parent are checked below but this is a quick check before doing
        # more unnecessary work.
        if self.index.node_status(node.parent).known_invalid():
            self.index.set_status_flags(node, BlockStatus.statusInvalidAncestor)
            return detach_nodes, attach_nodes

        # Find the fork point (if any) adding each block to the list of nodes
        # to attach to the main tree.  Push them onto the list in reverse order
        # so they are attached in the appropriate order when iterating the list
        # later.
        fork_node = self.best_chain.find_fork(node)
        invalid_chain = False

        n = node
        while n is not None and n != fork_node:
            if self.index.node_status(n).known_invalid():
                invalid_chain = True
                break
            attach_nodes.append(n)

            n = n.parent
        attach_nodes.reverse()

        # If any of the node's ancestors are invalid, unwind attachNodes, marking
        # each one as invalid for future reference.
        if invalid_chain:
            for n in attach_nodes:
                self.index.set_status_flags(n, BlockStatus.statusInvalidAncestor)

            return [], []

        # Start from the end of the main chain and work backwards until the
        # common ancestor adding each block to the list of nodes to detach from
        # the main chain.
        n = self.best_chain.tip()
        while n is not None and n != fork_node:
            detach_nodes.append(n)
            n = n.parent

        return detach_nodes, attach_nodes

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
    def _connect_block(self, node: BlockNode, block: btcutil.Block,
                       view: UtxoViewpoint, stxos: [SpentTxOut]):
        # Make sure it's extending the end of the best chain.
        prev_hash = block.get_msg_block().header.prev_block
        if prev_hash != self.best_chain.tip().hash:
            raise AssertError("connectBlock must be called with a block that extends the main chain")

        # Sanity check the correct number of stxos are provided.
        if len(stxos) != self._count_spent_outputs(block):
            raise AssertError("connectBlock called with inconsistent spent transaction out information")

        # No warnings about unknown rules or versions until the chain is
        # current.
        if self._is_current():
            # Warn if any unknown new rules are either about to activate or
            # have already been activated.
            self._warn_unknown_rule_activations(node)

            # Warn if a high enough percentage of the last blocks have
            # unexpected versions.
            self._warn_unknown_versions(node)

        # Write any block status changes to DB before updating best state.
        self.index.flush_to_db()

        # Generate a new best state snapshot that will be used to update the
        # database and later memory if all database updates are successful.
        self.state_lock.r_lock()
        cur_total_txns = self.state_snapshot.total_txns
        self.state_lock.r_unlock()

        num_txns = len(block.get_msg_block().transactions)
        block_size = block.get_msg_block().serialize_size()
        block_weight = get_block_weight(block)
        state = BestState(
            hash=node.hash,  # The hash of the block.
            height=node.height,  # The height of the block.
            bits=node.bits,  # The difficulty bits of the block.
            block_size=block_size,  # The size of the block.
            block_weight=block_weight,  # The weight of the block.
            num_txns=num_txns,  # The number of txns in the block.
            total_txns=cur_total_txns + num_txns,  # The total number of txns in the chain.
            median_time=node.calc_past_median_time(),  # Median time as per CalcPastMedianTime.
        )

        # Atomically insert info into the database.
        def f(db_tx: database.Tx):
            # Update best block state.
            db_put_best_state(db_tx, state, node.work_sum)

            # Add the block hash and height to the block index which tracks
            # the main chain.
            db_put_block_index(db_tx, block.hash(), node.height)

            # Update the utxo set using the state of the utxo view.  This
            # entails removing all of the utxos spent and adding the new
            # ones created by the block.
            db_put_utxo_view(db_tx, view)

            # Update the transaction spend journal by adding a record for
            # the block that contains all txos spent by it.
            db_put_spend_journal_entry(db_tx, block.hash(), stxos)

            # Allow the index manager to call each of the currently active
            # optional indexes with the block being connected so they can
            # update themselves accordingly.
            if self.index_manager is not None:
                self.index_manager.connect_block(db_tx, block, stxos)

        self.db.update(f)

        # Prune fully spent entries and mark all entries in the view unmodified
        # now that the modifications have been committed to the database.
        view.commit()

        # This node is now the end of the best chain.
        self.best_chain.set_tip(node)

        # Update the state for the best block.  Notice how this replaces the
        # entire struct instead of updating the existing one.  This effectively
        # allows the old version to act as a snapshot which callers can use
        # freely without needing to hold a lock for the duration.  See the
        # comments on the state variable for more details.
        self.state_lock.lock()
        self.state_snapshot = state
        self.state_lock.unlock()

        # Notify the caller that the block was connected to the main chain.
        # The caller would typically want to react with actions such as
        # updating wallets.
        self.chain_lock.unlock()
        self._send_notification(NTBlockConnected, block)
        self.chain_lock.lock()
        return

    # disconnectBlock handles disconnecting the passed node/block from the end of
    # the main (best) chain.
    #
    # This function MUST be called with the chain state lock held (for writes)
    def _disconnect_block(self, node: BlockNode, block: btcutil.Block, view: UtxoViewpoint):
        # Make sure the node being disconnected is the end of the best chain.
        if node.hash != self.best_chain.tip().hash:
            raise AssertError("disconnectBlock must be called with the block at the end of the main chain")

        # Load the previous block since some details for it are needed below.
        prev_node = node.parent
        prev_block = btcutil.Block()

        def fn1(db_tx: database.Tx):
            nonlocal prev_block
            prev_block = db_fetch_block_by_node(db_tx, prev_node)

        self.db.view(fn1)

        # Write any block status changes to DB before updating best state.
        self.index.flush_to_db()

        # Generate a new best state snapshot that will be used to update the
        # database and later memory if all database updates are successful.
        self.state_lock.r_lock()
        cur_total_txns = self.state_snapshot.total_txns
        self.state_lock.r_unlock()

        num_txns = len(prev_block.get_msg_block().transactions)
        block_size = prev_block.get_msg_block().serialize_size()
        block_weight = get_block_weight(prev_block)
        new_total_txns = cur_total_txns - len(block.get_msg_block().transactions)
        median_time = prev_node.calc_past_median_time()
        state = BestState(
            hash=prev_node.hash,
            height=prev_node.heightm,
            bits=prev_node.bits,
            block_size=block_size,
            block_weight=block_weight,
            num_txns=num_txns,
            total_txns=new_total_txns,
            median_time=median_time
        )

        def fn2(db_tx: database.Tx):
            # Update best block state.
            db_put_best_state(db_tx, state,
                              node.work_sum)  # TOCHECK, TOCONSIDER why node prev_node.work_sum here?

            # Remove the block hash and height from the block index which
            # tracks the main chain.
            db_remove_block_index(db_tx, block.hash(), node.height)

            # Update the utxo set using the state of the utxo view.  This
            # entails restoring all of the utxos spent and removing the new
            # ones created by the block.
            db_put_utxo_view(db_tx, view)

            # Update the transaction spend journal by removing the record
            # that contains all txos spent by the block .
            db_remove_spend_journal_entry(db_tx, block.hash())

            # Allow the index manager to call each of the currently active
            # optional indexes with the block being disconnected so they
            # can update themselves accordingly.
            if self.index_manager is not None:
                self.index_manager.disconnect_block(db_tx, block, view)

        self.db.update(fn2)

        # Prune fully spent entries and mark all entries in the view unmodified
        # now that the modifications have been committed to the database.
        view.commit()

        # This node's parent is now the end of the best chain.
        self.best_chain.set_tip(node.parent)

        # Update the state for the best block.  Notice how this replaces the
        # entire struct instead of updating the existing one.  This effectively
        # allows the old version to act as a snapshot which callers can use
        # freely without needing to hold a lock for the duration.  See the
        # comments on the state variable for more details.
        self.state_lock.lock()
        self.state_snapshot = state
        self.state_lock.unlock()

        #  Notify the caller that the block was disconnected from the main
        # chain.  The caller would typically want to react with actions such as
        # updating wallets.
        self.chain_lock.unlock()
        self._send_notification(NTBlockDisconnected, block)
        self.chain_lock.lock()

        return

    # TOCINSIDER
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
    def _reorganize_chain(self, detach_nodes, attach_nodes):
        # All of the blocks to detach and related spend journal entries needed
        # to unspend transaction outputs in the blocks being disconnected must
        # be loaded from the database during the reorg check phase below and
        # then they are needed again when doing the actual database updates.
        # Rather than doing two loads, cache the loaded data into these slices.
        detach_blocks = []
        detach_spent_tx_outs = []
        attach_blocks = []

        # Disconnect all of the blocks back to the point of the fork.  This
        # entails loading the blocks and their associated spent txos from the
        # database and using that information to unspend all of the spent txos
        # and remove the utxos created by the blocks.

        view = UtxoViewpoint()
        view.set_best_hash(self.best_chain.tip().hash)

        for n in detach_nodes:
            block = btcutil.Block(msg_block=wire.MsgBlock())  # define a empty block

            def fn1(db_tx: database.Tx):
                nonlocal block
                block = db_fetch_block_by_node(db_tx, n)

            self.db.view(fn1)

            # Load all of the utxos referenced by the block that aren't
            # already in the view.
            view.fetch_input_utxos(self.db, block)

            # Load all of the spent txos for the block from the spend
            # journal.
            stxos = []

            def fn2(db_tx: database.Tx):
                nonlocal stxos
                stxos = db_fetch_spend_journal_entry(db_tx, block)

            self.db.view(fn2)

            # Store the loaded block and spend journal entry for later.
            detach_blocks.append(block)
            detach_spent_tx_outs.extend(stxos)

            view.disconnect_transactions(self.db, block, stxos)

        # Perform several checks to verify each block that needs to be attached
        # to the main chain can be connected without violating any rules and
        # without actually connecting the block.
        #
        # NOTE: These checks could be done directly when connecting a block,
        # however the downside to that approach is that if any of these checks
        # fail after disconnecting some blocks or attaching others, all of the
        # operations have to be rolled back to get the chain back into the
        # state it was before the rule violation (or other failure).  There are
        # at least a couple of ways accomplish that rollback, but both involve
        # tweaking the chain and/or database.  This approach catches these
        # issues before ever modifying the chain.
        validation_error = None
        for n in attach_nodes:

            # If any previous nodes in attachNodes failed validation,
            # mark this one as having an invalid ancestor.
            if validation_error is not None:
                self.index.set_status_flags(n, BlockStatus.statusInvalidAncestor)
                continue

            block = btcutil.Block(msg_block=wire.MsgBlock())  # define a empty block

            def fn1(db_tx: database.Tx):
                nonlocal block
                block = db_fetch_block_by_node(db_tx, n)

            self.db.view(fn1)

            # Store the loaded block for later.
            attach_blocks.append(block)

            # Skip checks if node has already been fully validated. Although
            # checkConnectBlock gets skipped, we still need to update the UTXO
            # view.
            if self.index.node_status(n).known_valid():
                view.fetch_input_utxos(self.db, block)

                view.connect_transactions(block, stxos=None)

                continue

            # Notice the spent txout details are not requested here and
            # thus will not be generated.  This is done because the state
            # is not being immediately written to the database, so it is
            # not needed.
            try:
                self._check_connect_block(n, block, view, stxos=None)
            except RuleError as e:
                self.index.set_status_flags(n, BlockStatus.statusValidateFailed)
                validation_error = e
                continue

            self.index.set_status_flags(n, BlockStatus.statusValid)

        if validation_error is not None:
            raise validation_error

        # Reset the view for the actual connection code below.  This is
        # required because the view was previously modified when checking if
        # the reorg would be successful and the connection code requires the
        # view to be valid from the viewpoint of each block being connected or
        # disconnected.
        view = UtxoViewpoint()
        view.set_best_hash(self.best_chain.tip().hash)

        # Disconnect block from the main chain.
        for i, n in enumerate(detach_nodes):
            block = detach_blocks[i]

            # Load all of the utxos referenced by the block that aren't
            # already in the view.
            view.fetch_input_utxos(self.db, block)

            # Update the view to unspend all of the spent txos and remove
            # the utxos created by the block.
            view.disconnect_transactions(self.db, block, detach_spent_tx_outs[i])

            # Update the database and chain state.
            self._disconnect_block(n, block, view)

        # Connect the new best chain blocks.
        for i, n in enumerate(attach_nodes):
            block = attach_blocks[i]

            # Load all of the utxos referenced by the block that aren't
            # already in the view.
            view.fetch_input_utxos(self.db, block)

            # Update the view to mark all utxos referenced by the block
            # as spent and add all transactions being created by this block
            # to it.  Also, provide an stxo slice so the spent txout
            # details are generated.
            stxos = []
            view.connect_transactions(block, stxos)

            # TOCHECK check the stxos change as expected

            # Update the database and chain state.
            self._connect_block(n, block, view, stxos)

        # Log the point where the chain forked and old and new best chain
        # heads.
        first_attach_node = attach_nodes[0]
        first_detach_node = detach_nodes[0]
        last_attach_node = attach_nodes[-1]
        logger.info("REORGANIZE: Chain forks at %s" % first_attach_node.parent.hash)
        logger.info("REORGANIZE: Old best chain head was %s" % first_detach_node.hash)
        logger.info("REORGANIZE: New best chain head is %s" % last_attach_node.hash)

        return

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
    def _connect_best_chain(self, node, block, flags):
        fast_add = (flags & BFFastAdd) == BFFastAdd

        # We are extending the main (best) chain with a new block.  This is the
        # most common case.
        parent_hash = block.get_msg_block().header.prev_block
        if parent_hash == self.best_chain.tip().hash:
            # Skip checks if node has already been fully validated.
            fast_add = fast_add or self.index.node_status(node).known_valid()

            # Perform several checks to verify the block can be connected
            # to the main chain without violating any rules and without
            # actually connecting the block.
            view = UtxoViewpoint()
            view.set_best_hash(parent_hash)
            stxos = []
            if not fast_add:
                need_flush = True
                try:
                    self._check_connect_block(node, block, view, stxos)
                except RuleError as e:
                    self.index.set_status_flags(node, BlockStatus.statusValidateFailed)
                    raise e
                except Exception as e:
                    need_flush = False
                    raise e
                else:
                    self.index.set_status_flags(node, BlockStatus.statusValid)
                finally:
                    # Intentionally ignore errors writing updated node status to DB. If
                    # it fails to write, it's not the end of the world. If the block is
                    # valid, we flush in connectBlock and if the block is invalid, the
                    # worst that can happen is we revalidate the block after a restart.
                    if need_flush:
                        try:
                            self.index.flush_to_db()
                        except Exception as e:
                            logger.warning("Error flushing block index changes to disk: %s" % e)

            # In the fast add case the code to check the block connection
            # was skipped, so the utxo view needs to load the referenced
            # utxos, spend them, and add the new utxos being created by
            # this block.
            if fast_add:
                view.fetch_input_utxos(self.db, block)

                view.connect_transactions(block, stxos)

            # Connect the block to the main chain.
            self._connect_block(node, block, view, stxos)

            return True

        if fast_add:
            logger.warning("fastAdd set in the side chain case? %s\n" % block.hash())

        # We're extending (or creating) a side chain, but the cumulative
        # work for this new side chain is not enough to make it the new chain.
        if node.work_sum <= self.best_chain.tip().work_sum:
            # Log information about how the block is forking the chain.
            fork = self.best_chain.find_fork(node)
            if fork.hash == parent_hash:
                logger.info(("FORK: Block %s forks the chain at height %d" +
                             "/block %s, but does not cause a reorganize") % (
                                node.hash, fork.height, fork.hash
                            ))
            else:
                logger.info(("EXTEND FORK: Block %s extends a side chain " +
                             "which forks the chain at height %d/block %s") % (
                                node.hash, fork.height, fork.hash
                            ))
            return False

        # We're extending (or creating) a side chain and the cumulative work
        # for this new side chain is more than the old best chain, so this side
        # chain needs to become the main chain.  In order to accomplish that,
        # find the common ancestor of both sides of the fork, disconnect the
        # blocks that form the (now) old fork from the main chain, and attach
        # the blocks that form the new chain to the main chain starting at the
        # common ancenstor (the point where the chain forked).
        detach_nodes, attach_nodes = self._get_reorganize_nodes(node)

        # Reorganize the chain.
        logger.info("REORGANIZE: Block %s is causing a reorganize." % node.hash)
        try:
            self._reorganize_chain(detach_nodes, attach_nodes)
        finally:
            # Either getReorganizeNodes or reorganizeChain could have made unsaved
            # changes to the block index, so flush regardless of whether there was an
            # error. The index would only be dirty if the block failed to connect, so
            # we can ignore any errors writing.
            try:
                self.index.flush_to_db()
            except Exception as e:
                logger.warning("Error flushing block index changes to disk: %s" % e)

        return True

    # isCurrent returns whether or not the chain believes it is current.  Several
    # factors are used to guess, but the key factors that allow the chain to
    # believe it is current are:
    #  - Latest block height is after the latest checkpoint (if enabled)
    #  - Latest block has a timestamp newer than 24 hours ago  # TOCONSIDER why 24hours
    #
    # This function MUST be called with the chain state lock held (for reads).
    def _is_current(self):
        # Not current if the latest main (best) chain height is before the
        # latest known good checkpoint (when checkpoints are enabled).
        checkpoint = self.lastest_checkpoint()
        if checkpoint is not None and self.best_chain.tip().height < checkpoint.height:
            return False

        # Not current if the latest best block has a timestamp before 24 hours
        # ago.
        #
        # The chain appears to be current if none of the checks reported
        # otherwise.
        minus_24_hours = self.time_source.adjusted_time() - 24 * 60 * 60
        return self.best_chain.tip().timestamp >= minus_24_hours

    # IsCurrent returns whether or not the chain believes it is current.  Several
    # factors are used to guess, but the key factors that allow the chain to
    # believe it is current are:
    #  - Latest block height is after the latest checkpoint (if enabled)
    #  - Latest block has a timestamp newer than 24 hours ago
    #
    # This function is safe for concurrent access.
    def is_current(self):
        self.chain_lock.r_lock()
        current = self._is_current()
        self.chain_lock.r_unlock()
        return current

    # BestSnapshot returns information about the current best chain block and
    # related state as of the current point in time.  The returned instance must be
    # treated as immutable since it is shared by all callers.
    #
    # This function is safe for concurrent access.
    def best_snapshot(self) -> BestState:
        self.state_lock.r_lock()
        snapshot = self.state_snapshot
        self.state_lock.r_unlock()
        return snapshot

    # FetchHeader returns the block header identified by the given hash or an error
    # if it doesn't exist.
    def fetch_header(self, hash: chainhash.Hash) -> wire.BlockHeader:
        # Reconstruct the header from the block index if possible.
        node = self.index.lookup_node(hash)
        if node is not None:
            return node.header()

        # Fall back to loading it from the database.
        header = wire.BlockHeader()

        def fn(db_tx: database.Tx):
            nonlocal header
            header = db_fetch_header_by_hash(db_tx, hash)

        self.db.view(fn)
        return header

    # MainChainHasBlock returns whether or not the block with the given hash is in
    # the main chain.
    #
    # This function is safe for concurrent access.
    def main_chain_hash_block(self, hash: chainhash.Hash) -> bool:
        node = self.index.lookup_node(hash)
        return node is not None and self.best_chain.contains(node)

    # BlockLocatorFromHash returns a block locator for the passed block hash.
    # See BlockLocator for details on the algorithm used to create a block locator.
    #
    # In addition to the general algorithm referenced above, this function will
    # return the block locator for the latest known tip of the main (best) chain if
    # the passed hash is not currently known.
    #
    # This function is safe for concurrent access.
    def block_locator_from_hash(self, hash: chainhash.Hash) -> BlockLocator:
        self.chain_lock.r_lock()
        node = self.index.lookup_node(hash)
        locator = self.best_chain._block_locator(node)
        self.chain_lock.r_unlock()
        return locator

    # LatestBlockLocator returns a block locator for the latest known tip of the
    # main (best) chain.
    #
    # This function is safe for concurrent access.
    def lastest_block_locator(self) -> BlockLocator:
        self.chain_lock.r_lock()
        locator = self.best_chain.block_locator(None)
        self.chain_lock.r_unlock()
        return locator

    # BlockHeightByHash returns the height of the block with the given hash in the
    # main chain.
    #
    # This function is safe for concurrent access.
    def block_height_by_hash(self, hash: chainhash.Hash) -> int:
        node = self.index.lookup_node(hash)
        if node is None or not self.best_chain.contains(node):
            msg = "block %s is not in the main chain" % hash
            raise NotInMainChainErr(msg)

        return node.height

    # BlockHashByHeight returns the hash of the block at the given height in the
    # main chain.
    #
    # This function is safe for concurrent access.
    def block_hash_by_height(self, block_height: int) -> chainhash.Hash:
        node = self.best_chain.node_by_height(block_height)
        if node is None:
            msg = "no block at height %d exists" % block_height
            raise NotInMainChainErr(msg)

        return node.hash

    # HeightRange returns a range of block hashes for the given start and end
    # heights.  It is inclusive of the start height and exclusive of the end
    # height.  The end height will be limited to the current main chain height.
    #
    # This function is safe for concurrent access.
    def height_range(self, start_height: int, end_height: int) -> [chainhash.Hash]:
        # Ensure requested heights are sane.
        if start_height < 0:
            raise AssertError("start height of fetch range must not be less than zero - got %d" % start_height)

        if end_height < start_height:
            raise AssertError(
                "end height of fetch range must not be less than the start height - got start %d, end %d" % (
                    start_height,
                    end_height))
        # There is nothing to do when the start and end heights are the same,
        # so return now to avoid the chain view lock.
        if start_height == end_height:
            return []

        # Grab a lock on the chain view to prevent it from changing due to a
        # reorg while building the hashes.
        self.best_chain.lock.acquire()
        try:
            # When the requested start height is after the most recent best chain
            # height, there is nothing to do.
            latest_height = self.best_chain.tip().height
            if start_height > latest_height:
                return []

            # Limit the ending height to the latest height of the chain.
            if end_height > latest_height + 1:
                end_height = latest_height + 1

            # Fetch as many as are available within the specified range.
            hashes = []
            i = start_height
            while i < end_height:
                hashes.append(self.best_chain.node_by_height(i).hash)
                i += 1

            return hashes

        finally:
            self.best_chain.lock.release()

    # HeightToHashRange returns a range of block hashes for the given start height
    # and end hash, inclusive on both ends.  The hashes are for all blocks that are
    # ancestors of endHash with height greater than or equal to startHeight.  The
    # end hash must belong to a block that is known to be valid.
    #
    # This function is safe for concurrent access.
    def height_to_hash_range(self, start_height: int, end_hash: chainhash.Hash, max_results: int) -> [chainhash.Hash]:

        end_node = self.index.lookup_node(end_hash)
        if end_node is None:
            raise AssertError("no known block header with hash %s" % end_hash)

        if not self.index.node_status(end_node).known_valid():
            raise AssertError("block %s is not yet validated" % end_hash)

        end_height = end_node.height

        if start_height < 0:
            raise AssertError("start height (%d) is below 0" % start_height)

        if start_height > end_height:
            raise AssertError("start height (%d) is past end height (%d)" % (start_height, end_height))

        result_length = end_height - start_height + 1

        if result_length > max_results:
            raise AssertError("number of results (%d) would exceed max (%d)" % (result_length, max_results))

        # Walk backwards from endHeight to startHeight, collecting block hashes.
        hashes = []
        node = end_node
        i = result_length - 1
        while i >= 0:
            hashes.append(node.hash)
            node = node.parent
            i -= 1
        return hashes

    # IntervalBlockHashes returns hashes for all blocks that are ancestors of
    # endHash where the block height is a positive multiple of interval.
    #
    # This function is safe for concurrent access.
    def interval_block_hashes(self, end_hash: chainhash.Hash, interval: int) -> [chainhash.Hash]:
        end_node = self.index.lookup_node(end_hash)
        if end_node is None:
            raise AssertError("no known block header with hash %s" % end_hash)

        if not self.index.node_status(end_node).known_valid():
            raise AssertError("block %s is not yet validated" % end_hash)

        end_height = end_node.height
        hashes = []

        self.best_chain.lock.acquire()
        try:
            block_node = end_node
            index = end_height // interval
            while index > 0:
                # Use the bestChain chainView for faster lookups once lookup intersects
                # the best chain.
                block_heght = index * interval

                if self.best_chain._contains(block_node):
                    block_node = self.best_chain.node_by_height(block_heght)
                else:
                    block_node = block_node.ancestor(block_heght)

                hashes.append(block_node.hash)

                index -= 1

            hashes.reverse()
            return hashes

        finally:
            self.best_chain.lock.release()

    # ------------------------------------
    # Methods add from threshold_state
    # ------------------------------------
    # ThresholdState returns the current rule change threshold state of the given
    # deployment ID for the block AFTER the end of the current best chain.
    #
    # This function is safe for concurrent access.
    def threshold_state(self, deployment_id: int):
        self.chain_lock.lock()
        try:
            state = self._deployment_state(self.best_chain.tip(), deployment_id)
            return state
        finally:
            self.chain_lock.unlock()

    # thresholdState returns the current rule change threshold state for the block
    # AFTER the given node and deployment ID.  The cache is used to ensure the
    # threshold states for previous windows are only calculated once.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _threshold_state(self, prev_node: BlockNode or None, checker: ThresholdConditionChecker,
                         cache: ThresholdStateCache):
        # The threshold state for the window that contains the genesis block is
        # defined by definition.
        confirmation_window = checker.miner_confirmation_window()
        if prev_node is None or prev_node.height + 1 < confirmation_window:
            return ThresholdState.ThresholdDefined

        # Get the ancestor that is the last block of the previous confirmation
        # window in order to get its threshold state.  This can be done because
        # the state is the same for all blocks within a given window.
        # TOConsider
        prev_node = prev_node.ancestor(prev_node.height - (prev_node.height + 1) % confirmation_window)

        # Iterate backwards through each of the previous confirmation windows
        # to find the most recently cached threshold state.
        needed_states = []
        while prev_node is not None:
            # Nothing more to do if the state of the block is already
            # cached.
            _, ok = cache.look_up(prev_node.hash)
            if ok:
                break

            # The start and expiration times are based on the median block
            # time, so calculate it now.
            median_time = prev_node.calc_past_median_time()

            # The state is simply defined if the start time hasn't been
            # been reached yet.
            if median_time < checker.begin_time():
                cache.update(prev_node.hash, ThresholdState.ThresholdDefined)
                break

            # Add this node to the list of nodes that need the state
            # calculated and cached.
            needed_states.append(prev_node)

            # Get the ancestor that is the last block of the previous
            # confirmation window.
            prev_node = prev_node.relative_ancestor(confirmation_window)

        # Start with the threshold state for the most recent confirmation
        # window that has a cached state.
        state = ThresholdState.ThresholdDefined
        if prev_node is not None:
            state, ok = cache.look_up(prev_node.hash)
            if not ok:
                msg = "thresholdState: cache lookup failed for %s" % prev_node.hash
                raise AssertError(msg=msg, extra=ThresholdState.ThresholdFailed)

        # Since each threshold state depends on the state of the previous
        # window, iterate starting from the oldest unknown window.
        for prev_node in reversed(needed_states):
            if state is ThresholdState.ThresholdDefined:
                # The deployment of the rule change fails if it expires
                # before it is accepted and locked in.
                median_time = prev_node.calc_past_median_time()
                if median_time >= checker.end_time():
                    state = ThresholdState.ThresholdFailed
                    break

                # The state for the rule moves to the started state
                # once its start time has been reached (and it hasn't
                # already expired per the above).
                if median_time >= checker.begin_time():
                    state = ThresholdState.ThresholdStarted

            elif state is ThresholdState.ThresholdStarted:

                # The deployment of the rule change fails if it expires
                # before it is accepted and locked in.
                median_time = prev_node.calc_past_median_time()
                if median_time >= checker.end_time():
                    state = ThresholdState.ThresholdFailed
                    break

                # At this point, the rule change is still being voted
                # on by the miners, so iterate backwards through the
                # confirmation window to count all of the votes in it.
                count = 0
                count_node = prev_node
                for i in range(confirmation_window):
                    condition = checker.condition(count_node)

                    if condition:
                        count += 1

                    count_node = count_node.parent

                # The state is locked in if the number of blocks in the
                # period that voted for the rule change meets the
                # activation threshold.
                if count >= checker.rule_change_activation_threshold():
                    state = ThresholdState.ThresholdLockedIn
            elif state is ThresholdState.ThresholdLockedIn:
                # The new rule becomes active when its previous state
                # was locked in.
                state = ThresholdState.ThresholdActive
            elif state in (ThresholdState.ThresholdActive, ThresholdState.ThresholdFailed):
                pass

            cache.update(prev_node.hash, state)
        return state

    # deploymentState returns the current rule change threshold for a given
    # deploymentID. The threshold is evaluated from the point of view of the block
    # node passed in as the first argument to this method.
    #
    # It is important to note that, as the variable name indicates, this function
    # expects the block node prior to the block for which the deployment state is
    # desired.  In other words, the returned deployment state is for the block
    # AFTER the passed node.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _deployment_state(self, prev_node: BlockNode, deployment_id: int):
        if deployment_id > len(self.chain_params.deployments):
            raise DeploymentError(extra=ThresholdState.ThresholdFailed)

        deployment = self.chain_params.deployments[deployment_id]
        checker = DeploymentChecker(deployment=deployment, chain=self)
        cache = self.deployment_caches[deployment_id]
        return self._threshold_state(prev_node, checker, cache)

    # IsDeploymentActive returns true if the target deploymentID is active, and
    # false otherwise.
    #
    # This function is safe for concurrent access.
    def is_deployment_active(self, deployment_id: int) -> bool:
        self.chain_lock.lock()

        try:

            state = self._deployment_state(self.best_chain.tip(), deployment_id)

        finally:
            self.chain_lock.unlock()

        return state == ThresholdState.ThresholdActive

    # initThresholdCaches initializes the threshold state caches for each warning
    # bit and defined deployment and provides warnings if the chain is current per
    # the warnUnknownVersions and warnUnknownRuleActivations functions.
    def init_threshold_caches(self):
        # Initialize the warning and deployment caches by calculating the
        # threshold state for each of them.  This will ensure the caches are
        # populated and any states that needed to be recalculated due to
        # definition changes is done now.
        prev_node = self.best_chain.tip().parent
        for bit in range(vbNumBits):
            checker = BitConditionChecker(bit=bit, chain=self)
            cache = self.warning_caches[bit]
            self._threshold_state(prev_node, checker, cache)

        for idx in range(len(self.chain_params.deployments)):
            deployment = self.chain_params.deployments[idx]
            cache = self.deployment_caches[idx]
            checker = DeploymentChecker(deployment=deployment, chain=self)
            self._threshold_state(prev_node, checker, cache)

        # No warnings about unknown rules or versions until the chain is
        # current.
        if self._is_current():
            # Warn if a high enough percentage of the last blocks have
            # unexpected versions.
            best_node = self.best_chain.tip()
            self._warn_unknown_versions(best_node)

            # Warn if any unknown new rules are either about to activate or
            # have already been activated.
            self._warn_unknown_rule_activations(best_node)
        return

    # ------------------------------------
    # END
    # ------------------------------------

    # --------------------------------
    # Methods add from version_bits
    # --------------------------------

    # TOCONSIDER
    # warnUnknownRuleActivations displays a warning when any unknown new rules are
    # either about to activate or have been activated.  This will only happen once
    # when new rules have been activated and every block for those about to be
    # activated.
    #
    # This function MUST be called with the chain state lock held (for writes)
    def _warn_unknown_rule_activations(self, node: BlockNode):
        #  Warn if any unknown new rules are either about to activate or have
        # already been activated.
        for bit in range(vbNumBits):
            checker = BitConditionChecker(bit=bit, chain=self)
            cache = self.warning_caches[bit]
            state = self._threshold_state(node.parent, checker, cache)

            if state == ThresholdState.ThresholdActive:
                if not self.unknown_rules_warned:
                    logger.warning("Unknown new rules activated (bit %d)" % bit)
                    self.unknown_rules_warned = True
            elif state == ThresholdState.ThresholdLockedIn:
                window = checker.miner_confirmation_window()
                activation_height = window - (node.height % window)
                logger.warning(
                    "Unknown new rules are about to activate in %d blocks (bit %d)" % (activation_height, bit))

        return

    # TOCONSIDER
    # warnUnknownVersions logs a warning if a high enough percentage of the last
    # blocks have unexpected versions.
    #
    # This function MUST be called with the chain state lock held (for writes)
    def _warn_unknown_versions(self, node: BlockNode):
        # Nothing to do if already warned.
        if self.unknown_version_warned:
            return

        # Warn if enough previous blocks have unexpected versions.
        num_upgraded = 0
        i = 0
        while i < unknownVerNumToCheck and node is not None:
            expected_version = self._calc_next_block_version(node.parent)
            if expected_version > vbLegacyBlockVersion and ((node.version & ~expected_version) != 0):
                num_upgraded += 1

            node = node.parent
            i += 1
        if num_upgraded > unknownVerWarnNum:
            logger.warning(
                "Unknown block versions are being mined, so new rules might be in effect. " +
                "Are you running the latest version of the software?")
            self.unknown_version_warned = True

        return

    # calcNextBlockVersion calculates the expected version of the block after the
    # passed previous block node based on the state of started and locked in
    # rule change deployments.
    #
    # This function differs from the exported CalcNextBlockVersion in that the
    # exported version uses the current best chain as the previous block node
    # while this function accepts any block node.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _calc_next_block_version(self, prev_node: BlockNode):
        # Set the appropriate bits for each actively defined rule deployment
        # that is either in the process of being voted on, or locked in for the
        # activation at the next threshold window change.
        expected_version = vbTopBits

        for i in range(self.chain_params.deployments):

            deployment = self.chain_params.deployments[i]
            cache = self.deployment_caches[i]
            checker = DeploymentChecker(deployment=deployment, chain=self)
            state = self._threshold_state(prev_node, checker, cache)

            # TOCHECK why only count state of `started` and `lockedin` ?
            if state == ThresholdState.ThresholdStarted or state == ThresholdState.ThresholdLockedIn:
                expected_version |= (1 << deployment.bit_number)

        return expected_version

    # CalcNextBlockVersion calculates the expected version of the block after the
    # end of the current best chain based on the state of started and locked in
    # rule change deployments.
    #
    # This function is safe for concurrent access.
    def calc_next_block_version(self):
        self.chain_lock.lock()
        try:
            version = self._calc_next_block_version(self.best_chain.tip())
        finally:
            self.chain_lock.unlock()

        return version

    # --------------------------------
    # END
    # --------------------------------

    # --------------------------------
    # Methods add from utxo_viewpoint
    # --------------------------------

    # FetchUtxoView loads unspent transaction outputs for the inputs referenced by
    # the passed transaction from the point of view of the end of the main chain.
    # It also attempts to fetch the utxos for the outputs of the transaction itself
    # so the returned view can be examined for duplicate transactions.
    #
    # This function is safe for concurrent access however the returned view is NOT.
    def fetch_utxo_view(self, tx: btcutil.Tx) -> UtxoViewpoint:
        # Create a set of needed outputs based on those referenced by the
        # inputs of the passed transaction and the outputs of the transaction
        # itself.
        needed_set = {}

        for tx_out_idx, tx_out in range(tx.get_msg_tx().tx_outs):
            prev_out = wire.OutPoint(hash=tx.hash(), index=tx_out_idx)
            needed_set[prev_out] = {}  # the {} here is not for store data. need change to set()

        if not is_coin_base(tx):
            for tx_in in tx.get_msg_tx().tx_ins:
                needed_set[tx_in.previous_out_point] = {}

                # Request the utxos from the point of view of the end of the main
                # chain.
        view = UtxoViewpoint()
        self.chain_lock.r_lock()
        try:
            view.fetch_utxos_main(self.db, needed_set)
        finally:
            self.chain_lock.r_unlock()
        return view

    # FetchUtxoEntry loads and returns the requested unspent transaction output
    # from the point of view of the end of the main chain.
    #
    # NOTE: Requesting an output for which there is no data will NOT return an
    # error.  Instead both the entry and the error will be nil.  This is done to
    # allow pruning of spent transaction outputs.  In practice this means the
    # caller must check if the returned entry is nil before invoking methods on it.
    #
    # This function is safe for concurrent access however the returned entry (if
    # any) is NOT.
    def fetch_utxo_entry(self, outpoint: wire.OutPoint) -> UtxoEntry:
        self.chain_lock.r_lock()
        try:
            entry = None

            def fn(db_tx: database.Tx):
                nonlocal entry
                entry = db_fetch_utxo_entry(db_tx, outpoint)
                return

            self.db.view(fn)

        finally:
            self.chain_lock.r_unlock()

        return entry

    # ------------------------------------
    # END
    # ------------------------------------

    # --------------------------------
    # Methods add from process
    # --------------------------------

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

    # processOrphans determines if there are any orphans which depend on the passed
    # block hash (they are no longer orphans if true) and potentially accepts them.
    # It repeats the process for the newly accepted blocks (to detect further
    # orphans which may no longer be orphans) until there are no more.
    #
    # The flags do not modify the behavior of this function directly, however they
    # are needed to pass along to maybeAcceptBlock.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _process_orphans(self, hash: chainhash.Hash, flags: BehaviorFlags):
        # Start with processing at least the passed hash.  Leave a little room
        # for additional orphan blocks that need to be processed without
        # needing to grow the array in the common case.
        process_hashes = [hash]

        while len(process_hashes) > 0:
            # Pop the first hash to process from the slice.
            process_hash = process_hashes.pop(0)

            # Look up all orphans that are parented by the block we just
            # accepted.  This will typically only be one, but it could
            # be multiple if multiple blocks are mined and broadcast
            # around the same time.  The one with the most proof of work
            # will eventually win out.  An indexing for loop is
            # intentionally used over a range here as range does not
            # reevaluate the slice on each iteration nor does it adjust the
            # index for the modified slice.
            not_orphans = self.prev_orphans[process_hash]
            for o in not_orphans:
                # Remove the orphan from the orphan pool.
                self._remove_orphan_block(o)

                # Potentially accept the block into the block chain.
                self._maybe_accept_block(o.block, flags)

                # Add this block to the list of blocks to process so
                # any orphan blocks that depend on this block are
                # handled too.
                process_hashes.append(o.block.hash())

        return

    # ProcessBlock is the main workhorse for handling insertion of new blocks into
    # the block chain.  It includes functionality such as rejecting duplicate
    # blocks, ensuring blocks follow all rules, orphan handling, and insertion into
    # the block chain along with best chain selection and reorganization.
    #
    # When no errors occurred during processing, the first return value indicates
    # whether or not the block is on the main chain and the second indicates
    # whether or not the block is an orphan.
    #
    # This function is safe for concurrent access.
    def process_block(self, block: btcutil.Block, flags: BehaviorFlags) -> (bool, bool):
        self.chain_lock.lock()
        try:
            fast_add = (flags & BFFastAdd) == BFFastAdd

            block_hash = block.hash()
            logger.info("Processing block %s", block_hash)

            # The block must not already exist in the main chain or side chains.
            exists = self._block_exists(block_hash)
            if exists:
                msg = "already have block %s" % block_hash
                raise RuleError(ErrorCode.ErrDuplicateBlock, msg)

            # The block must not already exist as an orphan.
            if block_hash in self.orphans:
                msg = "already have block (orphan) %s" % block_hash
                raise RuleError(ErrorCode.ErrDuplicateBlock, msg)

            # Perform preliminary sanity checks on the block and its transactions.
            check_block_sanity_noexport(block, self.chain_params.pow_limit, self.time_source, flags)

            # Find the previous checkpoint and perform some additional checks based
            # on the checkpoint.  This provides a few nice properties such as
            # preventing old side chain blocks before the last checkpoint,
            # rejecting easy to mine, but otherwise bogus, blocks that could be
            # used to eat memory, and ensuring expected (versus claimed) proof of
            # work requirements since the previous checkpoint are met.
            block_header = block.get_msg_block().header
            checkpoint_node = self._find_previous_checkpoint()
            if checkpoint_node:
                # Ensure the block timestamp is after the checkpoint timestamp.
                if block_header.timestamp < checkpoint_node.timestamp:
                    msg = "block %s has timestamp %s before last checkpoint timestamp %s" % (
                        block_header, block_header.timestamp, checkpoint_node.timestamp
                    )
                    raise RuleError(ErrorCode.ErrCheckpointTimeTooOld, msg)

                # TOCONSIDER
                if not fast_add:
                    # Even though the checks prior to now have already ensured the
                    # proof of work exceeds the claimed amount, the claimed amount
                    # is a field in the block header which could be forged.  This
                    # check ensures the proof of work is at least the minimum
                    # expected based on elapsed time since the last checkpoint and
                    # maximum adjustment allowed by the retarget rules.
                    duration = block_header.timestamp - checkpoint_node.timestamp
                    required_target = compact_to_big(self._calc_easiest_difficulty(
                        checkpoint_node.bits, duration
                    ))
                    current_target = compact_to_big(block_header.bits)
                    if current_target > required_target:
                        msg = "block target difficulty of %064x is too low when compared to the previous checkpoint" % current_target
                        raise RuleError(ErrorCode.ErrDifficultyTooLow, msg)

            # Handle orphan blocks.
            prev_hash = block_header.prev_block
            prev_hash_exists = self._block_exists(prev_hash)
            if not prev_hash_exists:
                logger.info("Adding orphan block %s with parent %s" % (block_hash, prev_hash))
                self._add_orphan_block(block)
                return False, True

            # The block has passed all context independent checks and appears sane
            # enough to potentially accept it into the block chain.
            is_main_chain = self._maybe_accept_block(block, flags)

            # Accept any orphan blocks that depend on this block (they are
            # no longer orphans) and repeat for those accepted blocks until
            # there are no more.
            self._process_orphans(block_hash, flags)

            logger.info("Accepted block %s" % block_hash)

            return is_main_chain, False

        finally:
            self.chain_lock.unlock()

    # ------------------------------------
    # END
    # ------------------------------------

    # --------------------------------
    # Methods add from notifications
    # --------------------------------
    # Subscribe to block chain notifications. Registers a callback to be executed
    # when various events take place. See the documentation on Notification and
    # NotificationType for details on the types and contents of notifications.
    def subscribe(self, callback: NotificationCallback):
        self.notifications_lock.lock()
        self.notifications.append(callback)
        self.notifications_lock.unlock()
        return

    # sendNotification sends a notification with the passed type and data if the
    # caller requested notifications by providing a callback function in the call
    # to New.
    def _send_notification(self, typ: NotificationType, data):
        # Generate and send the notification.
        n = Notification(type=typ, data=data)

        self.notifications_lock.r_lock()

        for callback in self.notifications:
            callback(n)

        self.notifications_lock.r_unlock()
        return

    # ------------------------------------
    # END
    # ------------------------------------

    # --------------------------------
    # Methods add from difficulty
    # --------------------------------

    # TOCONSIDER
    # calcEasiestDifficulty calculates the easiest possible difficulty that a block
    # can have given starting difficulty bits and a duration.  It is mainly used to
    # verify that claimed proof of work by a block is sane as compared to a
    # known good checkpoint.
    def _calc_easiest_difficulty(self, bits: int, duration: int) -> int:
        adjuest_factor = self.chain_params.retarget_adjustment_factor

        # The test network rules allow minimum difficulty blocks after more
        # than twice the desired amount of time needed to generate a block has
        # elapsed.
        if self.chain_params.reduce_min_difficulty:
            reduction_time = self.chain_params.min_diff_reduction_time
            if duration > reduction_time:
                return self.chain_params.pow_limit_bits

        # Since easier difficulty equates to higher numbers, the easiest
        # difficulty for a given duration is the largest value possible given
        # the number of retargets for the duration and starting difficulty
        # multiplied by the max adjustment factor.
        new_target = compact_to_big(bits)

        while duration > 0 and new_target < self.chain_params.pow_limit:
            new_target *= adjuest_factor
            duration -= self.max_retarget_timespan

        # Limit new value to the proof of work limit.
        if new_target > self.chain_params.pow_limit:
            new_target = self.chain_params.pow_limit

        return big_to_compact(new_target)

    # findPrevTestNetDifficulty returns the difficulty of the previous block which
    # did not have the special testnet minimum difficulty rule applied.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _find_prev_test_net_difficulty(self, start_node: BlockNode) -> int:
        iter_node = start_node

        # TOCONSIDER why the loop conditions?
        while iter_node is not None and \
                                iter_node.height % self.blocks_per_retarget != 0 and \
                        iter_node.bits == self.chain_params.pow_limit_bits:
            iter_node = iter_node.parent

        # Return the found difficulty or the minimum difficulty if no
        # appropriate block was found.
        last_bits = self.chain_params.pow_limit_bits
        if iter_node is not None:
            last_bits = iter_node.bits
        return last_bits

    # calcNextRequiredDifficulty calculates the required difficulty for the block
    # after the passed previous block node based on the difficulty retarget rules.
    # This function differs from the exported CalcNextRequiredDifficulty in that
    # the exported version uses the current best chain as the previous block node
    # while this function accepts any block node.
    def _calc_next_required_difficulty(self, last_node: BlockNode, new_block_time: int) -> int:

        # Genesis block.
        if last_node is None:
            return self.chain_params.pow_limit_bits

        # Return the previous block's difficulty requirements if this block
        # is not at a difficulty retarget interval.
        if (last_node.height + 1) % self.blocks_per_retarget != 0:
            # For networks that support it, allow special reduction of the
            # required difficulty once too much time has elapsed without
            # mining a block.
            if self.chain_params.reduce_min_difficulty:
                # Return minimum difficulty when more than the desired
                # amount of time has elapsed without mining a block.
                reduction_time = self.chain_params.min_diff_reduction_time
                allow_min_time = last_node.timestamp + reduction_time
                if new_block_time > allow_min_time:
                    return self.chain_params.pow_limit_bits

            # For the main network (or any unrecognized networks), simply
            # return the previous block's difficulty requirements.
            return last_node.bits

        # Get the block node at the previous retarget (targetTimespan days
        # worth of blocks).
        first_node = last_node.relative_ancestor(self.blocks_per_retarget - 1)
        if first_node is None:
            raise AssertError("unable to obtain previous retarget block")

        # Limit the amount of adjustment that can occur to the previous
        # difficulty.
        actual_timespan = last_node.timestamp - first_node.timestamp
        adjusted_timespan = actual_timespan

        if actual_timespan < self.min_retarget_timespan:
            adjusted_timespan = self.min_retarget_timespan
        elif actual_timespan > self.max_retarget_timespan:
            adjusted_timespan = self.max_retarget_timespan

        # Calculate new target difficulty as:
        #  currentDifficulty * (adjustedTimespan / targetTimespan)
        # The result uses integer division which means it will be slightly
        # rounded down.  Bitcoind also uses integer division to calculate this
        # result.
        old_target = compact_to_big(last_node.bits)
        target_timespan = self.chain_params.target_timespan
        new_target = old_target * adjusted_timespan // target_timespan  # the core part

        # Limit new value to the proof of work limit.
        if new_target > self.chain_params.pow_limit:
            new_target = self.chain_params.pow_limit

        # Log new target difficulty and return it.  The new target logging is
        # intentionally converting the bits back to a number instead of using
        # newTarget since conversion to the compact representation loses
        # precision.
        new_target_bits = big_to_compact(new_target)
        logger.debug("Difficulty retarget at block height %d" % (last_node.height + 1))
        logger.debug("Old target %08x (%064x)" % (last_node.bits, old_target))
        logger.debug("New target %08x (%064x)" % (new_target_bits, compact_to_big(new_target_bits)))
        logger.debug("Actual timespan %s, adjusted timespan %s, target timespan %s" % (
            actual_timespan, adjusted_timespan, self.chain_params.target_timespan
        ))
        return new_target_bits

    # CalcNextRequiredDifficulty calculates the required difficulty for the block
    # after the end of the current best chain based on the difficulty retarget
    # rules.
    #
    # This function is safe for concurrent access.
    def calc_next_required_difficulty(self, timestamp: int) -> int:
        self.chain_lock.lock()
        try:
            difficulty = self._calc_next_required_difficulty(self.best_chain.tip(), timestamp)
        finally:
            self.chain_lock.unlock()

        return difficulty

    # ------------------------------------
    # END
    # ------------------------------------

    # --------------------------------
    # Methods add from checkpoints
    # --------------------------------

    # Checkpoints returns a slice of checkpoints (regardless of whether they are
    # already known).  When there are no checkpoints for the chain, it will return
    # nil.
    #
    # This function is safe for concurrent access.
    def checkpoints(self) -> [chaincfg.Checkpoint]:
        return self.checkpoints

    # HasCheckpoints returns whether this BlockChain has checkpoints defined.
    #
    # This function is safe for concurrent access.
    def has_checkpoints(self) -> bool:
        return len(self.checkpoints) > 0

    # LatestCheckpoint returns the most recent checkpoint (regardless of whether it
    # is already known). When there are no defined checkpoints for the active chain
    # instance, it will return nil.
    #
    # This function is safe for concurrent access.
    def lastest_checkpoint(self) -> chaincfg.Checkpoint or None:
        if self.has_checkpoints():
            return self.checkpoints[-1]
        else:
            return None

    # verifyCheckpoint returns whether the passed block height and hash combination
    # match the checkpoint data.  It also returns true if there is no checkpoint
    # data for the passed block height.
    def _verify_checkpoint(self, height: int, hash: chainhash.Hash) -> bool:
        if not self.has_checkpoints():
            return True

        # Nothing to check if there is no checkpoint data for the block height.
        if height not in self.checkpoints_by_height:
            return True

        checkpoint = self.checkpoints_by_height.get(height)
        if checkpoint.hash != hash:
            return False

        logger.info("Verified checkpoint at height %d/block %s" % (
            checkpoint.height, checkpoint.hash
        ))
        return True

    # findPreviousCheckpoint finds the most recent checkpoint that is already
    # available in the downloaded portion of the block chain and returns the
    # associated block node.  It returns nil if a checkpoint can't be found (this
    # should really only happen for blocks before the first checkpoint).
    #
    # This function MUST be called with the chain lock held (for reads).
    def _find_previous_checkpoint(self) -> BlockNode:
        if not self.has_checkpoints():
            return None

        # Perform the initial search to find and cache the latest known
        # checkpoint if the best chain is not known yet or we haven't already
        # previously searched.
        num_checkpoints = len(self.checkpoints)
        if self.checkpoint_node is None and self.next_checkpoint is None:

            # Loop backwards through the available checkpoints to find one
            # that is already available.

            for idx in range(num_checkpoints - 1, -1, -1):
                checkpoint = self.checkpoints[idx]
                checkpoint_hash = checkpoint.hash
                node = self.index.lookup_node(checkpoint_hash)
                if node is None or not self.best_chain.contains(node):
                    continue

                    # Checkpoint found.  Cache it for future lookups and
                    # set the next expected checkpoint accordingly.
                self.checkpoint_node = node
                if idx < num_checkpoints - 1:  # this is not the last checkpoint
                    self.next_checkpoint = self.checkpoints[idx + 1]
                return self.checkpoint_node

            # No known latest checkpoint.  This will only happen on blocks
            # before the first known checkpoint.  So, set the next expected
            # checkpoint to the first checkpoint and return the fact there
            # is no latest known checkpoint block.
            self.next_checkpoint = self.checkpoints[0]
            return None

        # At this point we've already searched for the latest known checkpoint,
        # so when there is no next checkpoint, the current checkpoint lockin
        # will always be the latest known checkpoint.
        if self.next_checkpoint is None:
            return self.checkpoint_node

        # When there is a next checkpoint and the height of the current best
        # chain does not exceed it, the current checkpoint lockin is still
        # the latest known checkpoint.
        if self.best_chain.tip().height < self.next_checkpoint.height:
            return self.checkpoint_node

        # We've reached or exceeded the next checkpoint height.  Note that
        # once a checkpoint lockin has been reached, forks are prevented from
        # any blocks before the checkpoint, so we don't have to worry about the
        # checkpoint going away out from under us due to a chain reorganize.

        # Cache the latest known checkpoint for future lookups.  Note that if
        # this lookup fails something is very wrong since the chain has already
        # passed the checkpoint which was verified as accurate before inserting
        # it.

        # find and set checkpoint_node
        checkpoint_node = self.index.lookup_node(self.next_checkpoint.hash)
        if checkpoint_node is None:
            raise AssertError(
                "findPreviousCheckpoint failed lookup of known good block node %s" % self.next_checkpoint.hash)

        self.checkpoint_node = checkpoint_node

        # set next_checkpoint
        checkpoint_idx = -1
        for idx in range(num_checkpoints - 1, -1, -1):
            if self.checkpoints[idx].hash == self.next_checkpoint.hash:
                checkpoint_idx = idx
                break

        self.next_checkpoint = None
        if checkpoint_idx != -1 and checkpoint_idx < num_checkpoints - 1:
            self.next_checkpoint = self.checkpoints[checkpoint_idx + 1]

        return self.checkpoint_node

    # IsCheckpointCandidate returns whether or not the passed block is a good
    # checkpoint candidate.
    #
    # The factors used to determine a good checkpoint are:
    #  - The block must be in the main chain
    #  - The block must be at least 'CheckpointConfirmations' blocks prior to the
    #    current end of the main chain
    #  - The timestamps for the blocks before and after the checkpoint must have
    #    timestamps which are also before and after the checkpoint, respectively
    #    (due to the median time allowance this is not always the case)
    #  - The block must not contain any strange transaction such as those with
    #    nonstandard scripts
    #
    # The intent is that candidates are reviewed by a developer to make the final
    # decision and then manually added to the list of checkpoints for a network.
    #
    # This function is safe for concurrent access.
    def is_checkpoint_candidate(self, block: btcutil.Block) -> bool:
        self.chain_lock.r_lock()
        try:
            # A checkpoint must be in the main chain.
            node = self.index.lookup_node(block.hash())
            if node is None or not self.best_chain.contains(node):
                return False

            # Ensure the height of the passed block and the entry for the block in
            # the main chain match.  This should always be the case unless the
            # caller provided an invalid block.
            if node.height != block.height():
                logger.warning("passed block height of %d does not match the main chain height of %d" % (
                    block.height(), node.height
                ))
                return False  # TOCINSIDER raise or return false?

            # A checkpoint must be at least CheckpointConfirmations blocks
            # before the end of the main chain.
            main_chain_height = self.best_chain.tip().height
            if node.height > (main_chain_height - CheckpointConfirmations):
                return False

            # A checkpoint must be have at least one block after it.
            #
            # This should always succeed since the check above already made sure it
            # is CheckpointConfirmations back, but be safe in case the constant
            # changes.
            next_node = self.best_chain.next(node)
            if next_node is None:
                return False

            # A checkpoint must be have at least one block before it.
            if node.parent is None:
                return False

            # A checkpoint must have timestamps for the block and the blocks on
            # either side of it in order (due to the median time allowance this is
            # not always the case).
            prev_time = node.parent.timestamp
            cur_time = block.get_msg_block().header.timestamp
            next_time = next_node.timestamp
            if not prev_time < cur_time < next_time:
                return False

            # A checkpoint must have transactions that only contain standard
            # scripts.
            for tx in block.get_transactions():
                if is_nonstandard_transaction(tx):
                    return False

            # All of the checks passed, so the block is a candidate.
            return True

        finally:
            self.chain_lock.r_unlock()

    # ------------------------------------
    # END
    # ------------------------------------

    # --------------------------------
    # Methods add from validate
    # --------------------------------
    # checkBlockHeaderContext performs several validation checks on the block header
    # which depend on its position within the block chain.
    #
    # The flags modify the behavior of this function as follows:
    #  - BFFastAdd: All checks except those involving comparing the header against
    #    the checkpoints are not performed.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _check_block_header_context(self, header: wire.BlockHeader, prev_node: BlockNode, flags: BehaviorFlags):
        fast_add = (flags & BFFastAdd) == BFFastAdd
        if not fast_add:
            # Ensure the difficulty specified in the block header matches
            # the calculated difficulty based on the previous block and
            # difficulty retarget rules.
            expected_difficulty = self._calc_next_required_difficulty(prev_node, header.timestamp)
            block_difficulty = header.bits
            if block_difficulty != expected_difficulty:
                msg = "block difficulty of %d is not the expected value of %d" % (block_difficulty, expected_difficulty)
                raise RuleError(ErrorCode.ErrUnexpectedDifficulty, msg)

            # Ensure the timestamp for the block header is after the
            #  median time of the last several blocks (medianTimeBlocks).
            median_time = prev_node.calc_past_median_time()
            if not header.timestamp > median_time:
                msg = "block timestamp of %s is not after expected %s" % (header.timestamp, median_time)
                raise RuleError(ErrorCode.ErrTimeTooOld, msg)

        # The height of this block is one more than the referenced previous
        # block.
        block_height = prev_node.height + 1

        # Ensure chain matches up to predetermined checkpoints.
        block_hash = header.block_hash()
        if not self._verify_checkpoint(block_height, block_hash):
            msg = "block at height %d does not match checkpoint hash" % block_height
            raise RuleError(ErrorCode.ErrBadCheckpoint, msg)

        # Find the previous checkpoint and prevent blocks which fork the main
        # chain before it.  This prevents storage of new, otherwise valid,
        # blocks which build off of old blocks that are likely at a much easier
        # difficulty and therefore could be used to waste cache and disk space.
        checkpoint_node = self._find_previous_checkpoint()
        if checkpoint_node is not None and block_height < checkpoint_node.height:
            msg = "block at height %d forks the main chain before the previous checkpoint at height %d" % (
                block_height, checkpoint_node.height
            )
            raise RuleError(ErrorCode.ErrForkTooOld, msg)

        # Reject outdated block versions once a majority of the network
        # has upgraded.  These were originally voted on by BIP0034,
        # BIP0065, and BIP0066.
        params = self.chain_params
        if header.version < 2 and block_height >= params.bip0034_height or \
                (header.version < 3 and block_height >= params.bip0066_height) or \
                (header.version < 4 and block_height >= params.bip0065_height):
            msg = "new blocks with version %d are no longer valid" % header.version
            raise RuleError(ErrorCode.ErrBlockVersionTooOld, msg)

        return

    # checkBlockContext peforms several validation checks on the block which depend
    # on its position within the block chain.
    #
    # The flags modify the behavior of this function as follows:
    #  - BFFastAdd: The transaction are not checked to see if they are finalized
    #    and the somewhat expensive BIP0034 validation is not performed.
    #
    # The flags are also passed to checkBlockHeaderContext.  See its documentation
    # for how the flags modify its behavior.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _check_block_context(self, block: btcutil.Block, prev_node: BlockNode, flags: BehaviorFlags):
        # Perform all block header related validation checks.
        header = block.get_msg_block().header
        self._check_block_header_context(header, prev_node, flags)

        fast_add = (flags & BFFastAdd) == BFFastAdd
        if not fast_add:
            # Obtain the latest state of the deployed CSV soft-fork in
            # order to properly guard the new validation behavior based on
            # the current BIP 9 version bits state.
            csv_state = self._deployment_state(prev_node, chaincfg.DeploymentCSV)

            # Once the CSV soft-fork is fully active, we'll switch to
            # using the current median time past of the past block's
            # timestamps for all lock-time based checks.
            if csv_state == ThresholdState.ThresholdActive:
                block_time = prev_node.calc_past_median_time()
            else:
                block_time = header.timestamp

            # The height of this block is one more than the referenced
            # previous block.
            block_height = prev_node.height + 1

            # Ensure all transactions in the block are finalized.
            for tx in block.get_transactions():
                if not is_finalized_transaction(tx, block_height, block_time):
                    msg = "block contains unfinalized transaction %s" % tx.hash()
                    raise RuleError(ErrorCode.ErrUnfinalizedTx, msg)

            # Ensure coinbase starts with serialized block heights for
            # blocks whose version is the serializedHeightVersion or newer
            # once a majority of the network has upgraded.  This is part of
            # BIP0034.
            if should_have_serialized_block_height(header) and \
                            block_height >= self.chain_params.bip0034_height:
                coinbase_tx = block.get_transactions()[0]
                check_serialized_height(coinbase_tx, block_height)

            # Query for the Version Bits state for the segwit soft-fork
            # deployment. If segwit is active, we'll switch over to
            # enforcing all the new rules.
            segwit_state = self._deployment_state(prev_node, chaincfg.DeploymentSegwit)

            # If segwit is active, then we'll need to fully validate the
            # new witness commitment for adherence to the rules.
            if segwit_state == ThresholdState.ThresholdActive:
                # Validate the witness commitment (if any) within the
                # block.  This involves asserting that if the coinbase
                # contains the special commitment output, then this
                # merkle root matches a computed merkle root of all
                # the wtxid's of the transactions within the block. In
                # addition, various other checks against the
                # coinbase's witness stack.
                validate_witness_commitment(block)

                # Once the witness commitment, witness nonce, and sig
                # op cost have been validated, we can finally assert
                # that the block's weight doesn't exceed the current
                # consensus parameter.
                block_weight = get_block_weight(block)
                if block_weight > MaxBlockWeight:
                    msg = ("block's weight metric is " +
                           "too high - got %s, max %s") % (
                              block_weight, MaxBlockWeight
                          )
                    raise RuleError(ErrorCode.ErrBlockWeightTooHigh, msg)

        return

    # checkBIP0030 ensures blocks do not contain duplicate transactions which
    # 'overwrite' older transactions that are not fully spent.  This prevents an
    # attack where a coinbase and all of its dependent transactions could be
    # duplicated to effectively revert the overwritten transactions to a single
    # confirmation thereby making them vulnerable to a double spend.
    #
    # For more details, see
    # https:#github.com/bitcoin/bips/blob/master/bip-0030.mediawiki and
    # http:#r6.ca/blog/20120206T005236Z.html.
    #
    # This function MUST be called with the chain state lock held (for reads).
    def _check_bip0030(self, node: BlockNode, block: btcutil.Block, view: UtxoViewpoint):
        # Fetch utxos for all of the transaction ouputs in this block.
        # Typically, there will not be any utxos for any of the outputs.
        fetch_set = {}  # TOCHANGE to set() struct
        for tx in block.get_transactions():
            for idx, _ in enumerate(tx.tx_outs):
                prev_out = wire.OutPoint(hash=tx.hash(), index=idx)
                fetch_set[prev_out] = {}

        view.fetch_utxos(self.db, fetch_set)

        # Duplicate transactions are only allowed if the previous transaction
        # is fully spent.
        for outpoint in fetch_set.keys():
            utxo = view.lookup_entry(outpoint)
            if utxo is not None and not utxo.is_spent():
                msg = "tried to overwrite transaction %s at block height %d that is not fully spent" % (
                    outpoint.hash, utxo.get_block_height()
                )
                raise RuleError(ErrorCode.ErrOverwriteTx, msg)

        return

    # checkConnectBlock performs several checks to confirm connecting the passed
    # block to the chain represented by the passed view does not violate any rules.
    # In addition, the passed view is updated to spend all of the referenced
    # outputs and add all of the new utxos created by block.  Thus, the view will
    # represent the state of the chain as if the block were actually connected and
    # consequently the best hash for the view is also updated to passed block.
    #
    # An example of some of the checks performed are ensuring connecting the block
    # would not cause any duplicate transaction hashes for old transactions that
    # aren't already fully spent, double spends, exceeding the maximum allowed
    # signature operations per block, invalid values in relation to the expected
    # block subsidy, or fail transaction script validation.
    #
    # The CheckConnectBlockTemplate function makes use of this function to perform
    # the bulk of its work.  The only difference is this function accepts a node
    # which may or may not require reorganization to connect it to the main chain
    # whereas CheckConnectBlockTemplate creates a new node which specifically
    # connects to the end of the current main chain and then calls this function
    # with that node.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _check_connect_block(self, node: BlockNode, block: btcutil.Block, view: UtxoViewpoint,
                             stxos: [SpentTxOut] or None):
        # If the side chain blocks end up in the database, a call to
        # CheckBlockSanity should be done here in case a previous version
        # allowed a block that is no longer valid.  However, since the
        # implementation only currently uses memory for the side chain blocks,
        # it isn't currently necessary.

        # TOCONSIDER why compare node.hash not node.parent.hash here
        # The coinbase for the Genesis block is not spendable, so just return
        # an error now.
        if node.hash == self.chain_params.genesis_hash:
            msg = "the coinbase for the genesis block is not spendable"
            raise RuleError(ErrorCode.ErrMissingTxOut, msg)

        # Ensure the view is for the node being checked.
        parent_hash = block.get_msg_block().header.prev_block
        if view.get_best_hash() != parent_hash:
            msg = ("inconsistent view when " +
                   "checking block connection: best hash is %s instead " +
                   "of expected %s"
                   ) % (
                      view.get_best_hash(), parent_hash
                  )
            raise AssertError(msg=msg)

        # BIP0030 added a rule to prevent blocks which contain duplicate
        # transactions that 'overwrite' older transactions which are not fully
        # spent.  See the documentation for checkBIP0030 for more details.
        #
        # There are two blocks in the chain which violate this rule, so the
        # check must be skipped for those blocks.  The isBIP0030Node function
        # is used to determine if this block is one of the two blocks that must
        # be skipped.
        #
        # In addition, as of BIP0034, duplicate coinbases are no longer
        # possible due to its requirement for including the block height in the
        # coinbase and thus it is no longer possible to create transactions
        # that 'overwrite' older ones.  Therefore, only enforce the rule if
        # BIP0034 is not yet active.  This is a useful optimization because the
        # BIP0030 check is expensive since it involves a ton of cache misses in
        # the utxoset.
        if not is_bip003_node(node) and (node.height < self.chain_params.bip0034_height):
            self._check_bip0030(node, block, view)

        # Load all of the utxos referenced by the inputs for all transactions
        # in the block don't already exist in the utxo view from the database.
        #
        # These utxo entries are needed for verification of things such as
        # transaction inputs, counting pay-to-script-hashes, and scripts.
        view.fetch_input_utxos(self.db, block)

        # TOCONDER why bip0016 use timestamp to check
        # while segwit use deployment state to check?

        # BIP0016 describes a pay-to-script-hash type that is considered a
        # "standard" type.  The rules for this BIP only apply to transactions
        # after the timestamp defined by txscript.Bip16Activation.  See
        # https://en.bitcoin.it/wiki/BIP_0016 for more details.
        enforce_bip0016 = node.timestamp >= txscript.Bip16Activation

        # Query for the Version Bits state for the segwit soft-fork
        # deployment. If segwit is active, we'll switch over to enforcing all
        # the new rules.
        segwit_state = self._deployment_state(node.parent, chaincfg.DeploymentSegwit)

        enforce_segwit = segwit_state == ThresholdState.ThresholdActive

        # The number of signature operations must be less than the maximum
        # allowed per block.  Note that the preliminary sanity checks on a
        # block also include a check similar to this one, but this check
        # expands the count to include a precise count of pay-to-script-hash
        # signature operations in each of the input transaction public key
        # scripts.
        transactions = block.get_transactions()
        total_sig_op_cost = 0
        for i, tx in enumerate(transactions):
            # Since the first (and only the first) transaction has
            # already been verified to be a coinbase transaction,
            # use i == 0 as an optimization for the flag to
            # countP2SHSigOps for whether or not the transaction is
            # a coinbase transaction rather than having to do a
            # full coinbase check again.
            sig_op_cost = get_sig_op_cost(tx, i == 0, view, enforce_bip0016, enforce_segwit)

            # Check for overflow or going over the limits.  We have to do
            # this on every loop iteration to avoid overflow.
            last_sig_op_cost = total_sig_op_cost  # TOCHANGE not nessary in python
            total_sig_op_cost += sig_op_cost
            if total_sig_op_cost < last_sig_op_cost or total_sig_op_cost > MaxBlockSigOpsCost:
                msg = "block contains too many signature operations - got %s, max %s" % (
                    total_sig_op_cost, MaxBlockSigOpsCost)
                raise RuleError(ErrorCode.ErrTooManySigOps, msg)

        # Perform several checks on the inputs for each transaction.  Also
        # accumulate the total fees.  This could technically be combined with
        # the loop above instead of running another loop over the transactions,
        # but by separating it we can avoid running the more expensive (though
        # still relatively cheap as compared to running the scripts) checks
        # against all the inputs when the signature operations are out of
        # bounds.
        total_fees = 0
        for tx in transactions:
            tx_fee = check_transaction_inputs(tx, node.height, view, self.chain_params)

            #  Sum the total fees and ensure we don't overflow the
            #  accumulator.
            total_fees += tx_fee
            if total_fees > pyutil.MaxInt64:
                raise RuleError(ErrorCode.ErrBadFees, "total fees for block overflows accumulator")

            # Add all of the outputs for this transaction which are not
            # provably unspendable as available utxos.  Also, the passed
            # spent txos slice is updated to contain an entry for each
            # spent txout in the order each transaction spends them.
            view.connect_transaction(tx, node.height, stxos)

        # The total output values of the coinbase transaction must not exceed
        # the expected subsidy value plus total transaction fees gained from
        # mining the block.  It is safe to ignore overflow and out of range
        # errors here because those error conditions would have already been
        # caught by checkTransactionSanity.
        total_satoshi_out = 0
        for tx_out in transactions[0].get_msg_tx().tx_outs:
            total_satoshi_out += tx_out.value

        expected_satoshi_out = calc_block_subsidy(node.height, self.chain_params) + total_fees
        if total_satoshi_out > expected_satoshi_out:
            msg = "coinbase transaction for block pays %s which is more than expected value of %s" % (
                total_satoshi_out, expected_satoshi_out
            )
            raise RuleError(ErrorCode.ErrBadCoinbaseValue, msg)

        # Don't run scripts if this node is before the latest known good
        # checkpoint since the validity is verified via the checkpoints (all
        # transactions are included in the merkle root hash and any changes
        # will therefore be detected by the next checkpoint).  This is a huge
        # optimization because running the scripts is the most time consuming
        # portion of block handling.
        checkpoint = self.lastest_checkpoint()
        runscript = True
        if checkpoint is not None and node.height <= checkpoint.height:
            runscript = False

        # Blocks created after the BIP0016 activation time need to have the
        # pay-to-script-hash checks enabled.
        script_flags = txscript.ScriptFlags(0)
        if enforce_bip0016:
            script_flags |= txscript.ScriptBip16

        # Enforce DER signatures for block versions 3+ once the historical
        # activation threshold has been reached.  This is part of BIP0066.
        block_header = block.get_msg_block().header
        if block_header.version >= 3 and node.height >= self.chain_params.bip0066_height:
            script_flags |= txscript.ScriptVerifyDERSignatures

        # Enforce CHECKLOCKTIMEVERIFY for block versions 4+ once the historical
        # activation threshold has been reached.  This is part of BIP0065.
        if block_header.version >= 4 and node.height >= self.chain_params.bip0065_height:
            script_flags |= txscript.ScriptVerifyCheckLockTimeVerify

        # Enforce CHECKSEQUENCEVERIFY during all block validation checks once
        # the soft-fork deployment is fully active.
        csv_state = self._deployment_state(node.parent, chaincfg.DeploymentCSV)

        if csv_state == ThresholdState.ThresholdActive:
            # If the CSV soft-fork is now active, then modify the
            # scriptFlags to ensure that the CSV op code is properly
            # validated during the script checks bleow.
            script_flags |= txscript.ScriptVerifyCheckSequenceVerify

            # We obtain the MTP of the *previous* block in order to
            # determine if transactions in the current block are final.
            median_time = node.parent.calc_past_median_time()

            # Additionally, if the CSV soft-fork package is now active,
            # then we also enforce the relative sequence number based
            # lock-times within the inputs of all transactions in this
            # candidate block.
            for tx in block.get_transactions():
                #  A transaction can only be included within a block
                # once the sequence locks of *all* its inputs are
                # active.
                sequence_lock = self._calc_sequence_lock(node, tx, view, mempool=False)

                if not sequence_lock_active(sequence_lock, node.height, median_time):
                    msg = "block contains transaction whose input sequence locks are not met"
                    raise RuleError(ErrorCode.ErrUnfinalizedTx, msg)

        # Enforce the segwit soft-fork package once the soft-fork has shifted
        # into the "active" version bits state.
        if enforce_segwit:
            script_flags |= txscript.ScriptVerifyWitness
            script_flags |= txscript.ScriptStrictMultiSig

        # Now that the inexpensive checks are done and have passed, verify the
        # transactions are actually allowed to spend the coins by running the
        # expensive ECDSA signature check scripts.  Doing this last helps
        # prevent CPU exhaustion attacks.
        if runscript:
            check_block_scripts(block, view, script_flags, self.sig_cache, self.hash_cache)

        # Update the best hash for view to include this block since all of its
        # transactions have been connected.
        view.set_best_hash(node.hash)

        return

    # CheckConnectBlockTemplate fully validates that connecting the passed block to
    # the main chain does not violate any consensus rules, aside from the proof of
    # work requirement. The block must connect to the current tip of the main chain.
    #
    # This function is safe for concurrent access.
    def check_connect_block_template(self, block: btcutil.Block):
        self.chain_lock.lock()
        try:
            # Skip the proof of work check as this is just a block template.
            flags = BFNoPoWCheck

            # This only checks whether the block can be connected to the tip of the
            # current chain.
            tip = self.best_chain.tip()
            header = block.get_msg_block().header
            if tip.hash != header.prev_block:
                msg = "previous block must be the current chain tip %s, instead got %s" % (
                    tip.hash, header.prev_block
                )
                raise RuleError(ErrorCode.ErrPrevBlockNotBest, msg)

            # Check block sanity
            check_block_sanity_noexport(block, self.chain_params.pow_limit, self.time_source, flags)

            # Check block context
            self._check_block_context(block, tip, flags)

            #  Leave the spent txouts entry nil in the state since the information
            #  is not needed and thus extra work can be avoided.
            view = UtxoViewpoint()
            view.set_best_hash(tip.hash)
            new_node = BlockNode.init_from(block_header=header, parent=tip)
            return self._check_connect_block(new_node, block, view, None)
        finally:
            self.chain_lock.unlock()

    # ------------------------------------
    # END
    # ------------------------------------



    # --------------------------------
    # Methods add from accept
    # --------------------------------
    # maybeAcceptBlock potentially accepts a block into the block chain and, if
    # accepted, returns whether or not it is on the main chain.  It performs
    # several validation checks which depend on its position within the block chain
    # before adding it.  The block is expected to have already gone through
    # ProcessBlock before calling this function with it.
    #
    # The flags are also passed to checkBlockContext and connectBestChain.  See
    # their documentation for how the flags modify their behavior.
    #
    # This function MUST be called with the chain state lock held (for writes).
    def _maybe_accept_block(self, block: btcutil.Block, flags: BehaviorFlags) -> bool:
        # The height of this block is one more than the referenced previous
        # block.
        prev_hash = block.get_msg_block().header.prev_block
        prev_node = self.index.lookup_node(prev_hash)
        if prev_node is None:
            msg = "previous block %s is unknown" % prev_hash
            raise RuleError(ErrorCode.ErrPreviousBlockUnknown, msg)
        elif self.index.node_status(prev_node).known_invalid():
            msg = "previous block %s is known to be invalid" % prev_hash
            raise RuleError(ErrorCode.ErrInvalidAncestorBlock, msg)

        block_height = prev_node.height + 1
        block.set_height(block_height)

        # The block must pass all of the validation rules which depend on the
        # position of the block within the block chain.
        self._check_block_context(block, prev_node, flags)

        # Insert the block into the database if it's not already there.  Even
        # though it is possible the block will ultimately fail to connect, it
        # has already passed all proof-of-work and validity tests which means
        # it would be prohibitively expensive for an attacker to fill up the
        # disk with a bunch of blocks that fail to connect.  This is necessary
        # since it allows block download to be decoupled from the much more
        # expensive connection logic.  It also has some other nice properties
        # such as making blocks that never become part of the main chain or
        # blocks that fail to connect available for further analysis.
        def fn(db_tx: database.Tx):
            return db_store_block(db_tx, block)

        self.db.update(fn)

        # Create a new block node for the block and add it to the node index. Even
        # if the block ultimately gets connected to the main chain, it starts out
        # on a side chain.
        block_header = block.get_msg_block().header
        new_node = BlockNode.init_from(block_header, prev_node)
        new_node.status = BlockStatus.statusDataStored

        self.index.add_node(new_node)
        self.index.flush_to_db()

        # Connect the passed block to the chain while respecting proper chain
        # selection according to the chain with the most proof of work.  This
        # also handles validation of the transaction scripts.
        is_main_chain = self._connect_best_chain(new_node, block, flags)

        # Notify the caller that the new block was accepted into the block
        # chain.  The caller would typically want to react by relaying the
        # inventory to other peers.
        self.chain_lock.unlock()
        self._send_notification(NTBlockAccepted, block)
        self.chain_lock.lock()

        return is_main_chain

        # ------------------------------------
        # END
        # ------------------------------------


def lock_time_to_sequence(is_seconds: bool, locktime: int):
    pass


# countSpentOutputs returns the number of utxos the passed block spends.
def count_spent_outputs(block: btcutil.Block):
    # Exclude the coinbase transaction since it can't spend anything.
    num_spent = 0
    for tx in block.get_transactions()[1:]:
        num_spent += len(tx.get_msg_tx().tx_ins)
    return num_spent
