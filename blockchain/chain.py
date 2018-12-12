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
                prev_hash = orphan.block.get_msg_block().header.prev_block
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
            prev_hash = orphan.block.get_msg_block().header.prev_block
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
    def add_orphan_block(self, block: btcutil.Block):
        # Remove expired orphan blocks.
        for _, o_block in self.orphans.items():
            if int(time.time()) > o_block.expiration:
                self.remove_orphan_block(o_block)
                continue

            # Update the oldest orphan block pointer so it can be discarded
            # in case the orphan pool fills up.
            if self.oldest_orphan is None or o_block.expiration < self.oldest_orphan.expiration:
                self.oldest_orphan = o_block

        # Limit orphan blocks to prevent memory exhaustion.
        if len(self.orphans) + 1 > maxOrphanBlocks:
            # Remove the oldest orphan to make room for the new one.
            self.remove_orphan_block(self.oldest_orphan)
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
            input_height = utxo.block_height()
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
        view.commit()  # TODO

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
        self._send_notification()  # TODO
        self.chain_lock.lock()
        return

    # disconnectBlock handles disconnecting the passed node/block from the end of
    # the main (best) chain.
    #
    # This function MUST be called with the chain state lock held (for writes)
    def disconnect_block(self, node, block, view):
        pass

    # countSpentOutputs returns the number of utxos the passed block spends.
    @staticmethod
    def _count_spent_outputs(block: btcutil.Block):
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

    # ------------------------------------
    # Methods add from threshold_state.py
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

    # ------------------------------------
    # END
    # ------------------------------------


    # --------------------------------
    # Methods add from version_bits.py
    # --------------------------------

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
                "Unknown block versions are being mined, so new rules might be in effect.  Are you running the latest version of the software?")
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
    # Methods add from version_bits.py
    # --------------------------------

    # TODO
    # FetchUtxoView loads unspent transaction outputs for the inputs referenced by
    # the passed transaction from the point of view of the end of the main chain.
    # It also attempts to fetch the utxos for the outputs of the transaction itself
    # so the returned view can be examined for duplicate transactions.
    #
    # This function is safe for concurrent access however the returned view is NOT.
    def fetch_utxo_view(self):
        pass


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
    def fetch_utxo_entry(self):
        pass

    # ------------------------------------
    # END
    # ------------------------------------

def lock_time_to_sequence(is_seconds: bool, locktime: int):
    pass
