import chaincfg
import typing
import txscript
import btcutil
import mining
import wire
import blockchain
import chainhash
import pyutil
import logging
from .error import *

_logger = logging.getLogger(__name__)

# orphanExpireScanInterval is the minimum amount of time in between
# scans of the orphan pool to evict expired transactions.
orphanExpireScanInterval = pyutil.Minute * 5

# orphanTTL is the maximum amount of time an orphan is allowed to
# stay in the orphan pool before it expires and is evicted during the
# next scan.
orphanTTL = pyutil.Minute * 15


# Tag represents an identifier to use for tagging orphan transactions.  The
# caller may choose any scheme it desires, however it is common to use peer IDs
# so that orphans can be identified by which peer first relayed them.
class Tag(int):
    pass


# Config is a descriptor containing the memory pool configuration.
class Config:
    def __init__(self, policy: 'Policy' = None,
                 chain_params: chaincfg.Params = None,
                 fetch_utxo_view: typing.Callable = None,
                 best_height: typing.Callable = None,
                 median_time_past: typing.Callable = None,
                 cacl_sequence_lock: typing.Callable = None,
                 is_deployment_active: typing.Callable = None,
                 sig_cache: txscript.SigCache = None,
                 hash_cache: txscript.HashCache = None,
                 addr_index=None,  # TODO
                 fee_estimator=None):  # TODO

        # Policy defines the various mempool configuration options related
        # to policy.
        self.policy = policy

        # ChainParams identifies which chain parameters the txpool is
        # associated with.
        self.chain_params = chain_params

        # FetchUtxoView defines the function to use to fetch unspent
        # transaction output information.
        self.fetch_utxo_view = fetch_utxo_view

        # BestHeight defines the function to use to access the block height of
        # the current best chain.
        self.best_height = best_height

        # MedianTimePast defines the function to use in order to access the
        # median time past calculated from the point-of-view of the current
        # chain tip within the best chain.
        self.median_time_past = median_time_past

        # CalcSequenceLock defines the function to use in order to generate
        # the current sequence lock for the given transaction using the passed
        # utxo view.
        self.cacl_sequence_lock = cacl_sequence_lock

        # IsDeploymentActive returns true if the target deploymentID is
        # active, and false otherwise. The mempool uses this function to gauge
        # if transactions using new to be soft-forked rules should be allowed
        # into the mempool or not.
        self.is_deployment_active = is_deployment_active

        # SigCache defines a signature cache to use.
        self.sig_cache = sig_cache

        # HashCache defines the transaction hash mid-state cache to use.
        self.hash_cache = hash_cache

        # AddrIndex defines the optional address index instance to use for
        # indexing the unconfirmed transactions in the memory pool.
        # This can be nil if the address index is not enabled.
        self.addr_index = addr_index

        # FeeEstimatator provides a feeEstimator. If it is not nil, the mempool
        # records all new transactions it observes into the feeEstimator.
        self.fee_estimator = fee_estimator


class Policy:
    def __init__(self, max_tx_version: int = None,
                 disable_relay_priority: bool = None,
                 accept_non_std: bool = None,
                 free_tx_relay_limit: float = None,
                 max_orphan_txs: int = None,
                 max_orphan_tx_size: int = None,
                 max_sig_op_cost_per_tx: int = None,
                 min_relay_tx_fee: btcutil.Amount = None):
        # MaxTxVersion is the transaction version that the mempool should
        # accept.  All transactions above this version are rejected as
        # non-standard.
        self.max_tx_version = max_tx_version or 0

        # DisableRelayPriority defines whether to relay free or low-fee
        # transactions that do not have enough priority to be relayed.

        self.disable_relay_priority = disable_relay_priority or False

        # AcceptNonStd defines whether to accept non-standard transactions. If
        # true, non-standard transactions will be accepted into the mempool.
        # Otherwise, all non-standard transactions will be rejected.

        self.accept_non_std = accept_non_std or False

        # FreeTxRelayLimit defines the given amount in thousands of bytes
        # per minute that transactions with no fee are rate limited to.

        self.free_tx_relay_limit = free_tx_relay_limit or 0.0

        # MaxOrphanTxs is the maximum number of orphan transactions
        # that can be queued.
        self.max_orphan_txs = max_orphan_txs or 0

        # MaxOrphanTxSize is the maximum size allowed for orphan transactions.
        # This helps prevent memory exhaustion attacks from sending a lot of
        # of big orphans.
        self.max_orphan_tx_size = max_orphan_tx_size or 0

        # MaxSigOpCostPerTx is the cumulative maximum cost of all the signature
        # operations in a single transaction we will relay or mine.  It is a
        # fraction of the max signature operations for a block.

        self.max_sig_op_cost_per_tx = max_sig_op_cost_per_tx or 0

        # MinRelayTxFee defines the minimum transaction fee in BTC/kB to be
        # considered a non-zero fee.
        self.min_relay_tx_fee = min_relay_tx_fee or btcutil.Amount(0)


# TxDesc is a descriptor containing a transaction in the mempool along with
# additional metadata.
class TxDesc(mining.TxDesc):
    def __init__(self, starting_priority: float = None):
        # StartingPriority is the priority of the transaction when it was added
        # to the pool.
        self.starting_priority = starting_priority or 0.0


# orphanTx is normal transaction that references an ancestor transaction
# that is not yet available.  It also contains additional information related
# to it such as an expiration time to help prevent caching the orphan forever.
class OrphanTx:
    def __init__(self, tx: btcutil.Tx = None,
                 tag: Tag = None,
                 expiration: int = None):
        self.tx = tx
        self.tag = tag
        self.expiration = expiration


# TxPool is used as a source of transactions that need to be mined into blocks
# and relayed to other peers.  It is safe for concurrent access from multiple
# peers.
class TxPool:
    def __init__(self, last_updated: int = None,
                 mtx: pyutil.RWLock = None,
                 cfg: Config = None,
                 pool: dict = None,
                 orphans: dict = None,
                 orphans_by_prev: dict = None,
                 outpoints: dict = None,
                 penny_total: float = None,
                 last_penny_unix: int = None,
                 next_expire_scan: int = None):
        # The following variables must only be used atomically.

        # last time pool was updated
        self.last_updated = last_updated
        self.mtx = mtx or pyutil.RWLock()
        self.cfg = cfg
        self.pool = pool
        self.orphans = orphans
        self.orphans_by_prev = orphans_by_prev
        self.outpoints = outpoints

        # exponentially decaying total for penny spends.
        self.penny_total = penny_total
        # unix time of last ``penny spend''
        self.last_penny_unix = last_penny_unix

        # nextExpireScan is the time after which the orphan pool will be
        # scanned in order to evict orphans.  This is NOT a hard deadline as
        # the scan will only run when an orphan is added to the pool as opposed
        # to on an unconditional timer.
        self.next_expire_scan = next_expire_scan

    # RemoveOrphan removes the passed orphan transaction from the orphan pool and
    # previous orphan index.
    #
    # This function is safe for concurrent access.
    def remove_orphans(self, tx: btcutil.Tx):
        self.mtx.lock()
        self._remove_orphan(tx, remove_redeemers=False)
        self.mtx.unlock()

    # TOCHECK
    # removeOrphan is the internal function which implements the public
    # RemoveOrphan.  See the comment for RemoveOrphan for more details.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _remove_orphan(self, tx: btcutil.Tx, remove_redeemers: bool):
        # Nothing to do if passed tx is not an orphan.
        tx_hash = tx.hash()
        if tx_hash not in self.orphans:
            return
        otx = self.orphans[tx_hash]

        # Remove the reference from the previous orphan index.
        for tx_in in otx.tx.get_msg_tx().tx_ins:
            if tx_in.previous_out_point in self.orphans_by_prev:
                orphans = self.orphans_by_prev[tx_in.previous_out_point]
                del orphans[tx_hash]

                # Remove the map entry altogether if there are no
                # longer any orphans which depend on it.
                if len(orphans) == 0:
                    del self.orphans_by_prev[tx_in.previous_out_point]

        # Remove any orphans that redeem outputs from this one if requested.
        if remove_redeemers:
            for tx_out_idx in range(len(tx.get_msg_tx().tx_outs)):
                prev_out = wire.OutPoint(index=tx_out_idx, hash=tx_hash)
                for orphan in self.orphans_by_prev[prev_out].values():
                    self._remove_orphan(orphan, remove_redeemers=True)

        # Remove the transaction from the orphan pool.
        del self.orphans[tx_hash]

        return

    # limitNumOrphans limits the number of orphan transactions by evicting a random
    # orphan if adding a new one would cause it to overflow the max allowed.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _limit_num_orphans(self):

        # Scan through the orphan pool and remove any expired orphans when it's
        # time.  This is done for efficiency so the scan only happens
        # periodically instead of on every orphan added to the pool.
        now = pyutil.now()
        if now > self.next_expire_scan:
            origin_num_orphans = len(self.orphans)

            for otx in self.orphans.values():
                if now > otx.expiration:
                    # Remove redeemers too because the missing
                    # parents are very unlikely to ever materialize
                    # since the orphan has already been around more
                    # than long enough for them to be delivered.
                    self._remove_orphan(otx.tx, remove_redeemers=True)

            # Set next expiration scan to occur after the scan interval.
            self.next_expire_scan = now + orphanExpireScanInterval

            num_orphans = len(self.orphans)
            num_expired = num_orphans - origin_num_orphans
            if num_expired > 0:
                _logger.info("Expired %d orphan(s) (remaining: %d)" % (num_expired, num_orphans))

        # Nothing to do if adding another orphan will not cause the pool to
        # exceed the limit.
        if len(self.orphans) + 1 <= self.cfg.policy.max_orphan_txs:
            return

        # TOCHANGE the comment
        # Remove a random entry from the map.  For most compilers, Go's
        # range statement iterates starting at a random item although
        # that is not 100% guaranteed by the spec.  The iteration order
        # is not important here because an adversary would have to be
        # able to pull off preimage attacks on the hashing function in
        # order to target eviction of specific entries anyways.
        for otx in self.orphans.values():
            # TODCHECK can we delete items the orphans in loop?
            # Don't remove redeemers in the case of a random eviction since
            # it is quite possible it might be needed again shortly.
            self._remove_orphan(otx.tx, remove_redeemers=False)
            break

        return

    # addOrphan adds an orphan transaction to the orphan pool.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _add_orphan(self, tx: btcutil.Tx, tag: Tag):
        # Nothing to do if no orphans are allowed.
        if self.cfg.policy.max_orphan_txs <= 0:
            return

        # Limit the number orphan transactions to prevent memory exhaustion.
        # This will periodically remove any expired orphans and evict a random
        # orphan if space is still needed.
        self._limit_num_orphans()

        self.orphans[tx.hash()] = OrphanTx(
            tx=tx,
            tag=tag,
            expiration=pyutil.now() + orphanTTL
        )
        for tx_in in tx.get_msg_tx().tx_ins:
            if tx_in.previous_out_point not in self.orphans_by_prev:
                self.orphans_by_prev[tx_in.previous_out_point] = {}
            self.orphans_by_prev[tx_in.previous_out_point][tx.hash()] = tx

            _logger.debug("Stored orphan transaction %s (total: %d)", tx.hash(), len(self.orphans))
        return

    # maybeAddOrphan potentially adds an orphan to the orphan pool.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _maybe_add_orphan(self, tx: btcutil.Tx, tag: Tag):
        # Ignore orphan transactions that are too large.  This helps avoid
        # a memory exhaustion attack based on sending a lot of really large
        # orphans.  In the case there is a valid transaction larger than this,
        # it will ultimtely be rebroadcast after the parent transactions
        # have been mined or otherwise received.
        #
        # Note that the number of orphan transactions in the orphan pool is
        # also limited, so this equates to a maximum memory used of
        # mp.cfg.Policy.MaxOrphanTxSize * mp.cfg.Policy.MaxOrphanTxs (which is ~5MB
        # using the default values at the time this comment was written).
        serialized_len = tx.get_msg_tx().serialize_size()
        if serialized_len > self.cfg.policy.max_orphan_tx_size:
            msg = "orphan transaction size of %d bytes is larger than max allowed size of %d bytes" % \
                  (serialized_len, self.cfg.policy.max_orphan_tx_size)
            raise tx_rule_error(wire.RejectCode.RejectNonstandard, msg)

        # Add the orphan if the none of the above disqualified it.
        self._add_orphan(tx, tag)
        return

    # removeOrphanDoubleSpends removes all orphans which spend outputs spent by the
    # passed transaction from the orphan pool.  Removing those orphans then leads
    # to removing all orphans which rely on them, recursively.  This is necessary
    # when a transaction is added to the main pool because it may spend outputs
    # that orphans also spend.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _remove_orphan_double_spends(self, tx: btcutil.Tx):
        msg_tx = tx.get_msg_tx()
        for tx_in in msg_tx.tx_ins:
            for orphan in self.orphans_by_prev[tx_in.previous_out_point].values:
                self._remove_orphan(orphan, remove_redeemers=True)
        return

    # isTransactionInPool returns whether or not the passed transaction already
    # exists in the main pool.
    #
    # This function MUST be called with the mempool lock held (for reads).
    def _is_transaction_in_pool(self, hash: chainhash.Hash) -> bool:
        return hash in self.pool

    # IsTransactionInPool returns whether or not the passed transaction already
    # exists in the main pool.
    #
    # This function is safe for concurrent access.
    def is_transaction_in_pool(self, hash: chainhash.Hash) -> bool:
        # Protect concurrent access
        self.mtx.r_lock()
        in_pool = self._is_transaction_in_pool(hash)
        self.mtx.r_unlock()
        return in_pool

    # isOrphanInPool returns whether or not the passed transaction already exists
    # in the orphan pool.
    #
    # This function MUST be called with the mempool lock held (for reads).
    def _is_orphan_in_pool(self, hash: chainhash.Hash) -> bool:
        return hash in self.orphans

    # IsOrphanInPool returns whether or not the passed transaction already exists
    # in the orphan pool.
    #
    # This function is safe for concurrent access.
    def is_orphan_in_pool(self, hash: chainhash.Hash) -> bool:
        # Protect concurrent access
        self.mtx.r_lock()
        in_pool = self._is_orphan_in_pool(hash)
        self.mtx.r_unlock()
        return in_pool

    # haveTransaction returns whether or not the passed transaction already exists
    # in the main pool or in the orphan pool.
    #
    # This function MUST be called with the mempool lock held (for reads).
    def _have_transaction(self, hash: chainhash.hash) -> bool:
        return self._is_transaction_in_pool(hash) or self._is_orphan_in_pool(hash)

    # HaveTransaction returns whether or not the passed transaction already exists
    # in the main pool or in the orphan pool.
    #
    # This function is safe for concurrent access.
    def have_transaction(self, hash: chainhash.hash) -> bool:
        # Protect concurrent access
        self.mtx.r_lock()
        have_tx = self._have_transaction(hash)
        self.mtx.r_unlock()
        return have_tx

    # removeTransaction is the internal function which implements the public
    # RemoveTransaction.  See the comment for RemoveTransaction for more details.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _remove_transaction(self, tx: btcutil.Tx, remove_redeemers: bool):
        tx_hash = tx.hash()

        if remove_redeemers:
            for i in range(len(tx.get_msg_tx().tx_outs)):
                prev_out = wire.OutPoint(hash=tx_hash, index=i)
                if prev_out in self.outpoints:
                    tx_redeemer = self.outpoints[prev_out]
                    self._remove_transaction(tx_redeemer, remove_redeemers=True)

        # Remove the transaction if needed
        if tx_hash in self.pool:
            tx_desc = self.pool[tx_hash]

            # Remove unconfirmed address index entries associated with the
            # transaction if enabled.
            if self.cfg.addr_index is not None:
                self.cfg.addr_index.remove_unconfirmed_tx(tx_hash)  # TODO

            # Mark the referenced outpoints as unspent by the pool.
            for tx_in in tx_desc.tx.get_msg_tx().tx_ins:
                del self.outpoints[tx_in.previous_out_point]

            del self.pool[tx_hash]

            # TOADD TOCHECK
            # need atomic.StoreInt64?
            self.last_updated = pyutil.now()

        return

    # RemoveTransaction removes the passed transaction from the mempool. When the
    # removeRedeemers flag is set, any transactions that redeem outputs from the
    # removed transaction will also be removed recursively from the mempool, as
    # they would otherwise become orphans.
    #
    # This function is safe for concurrent access.
    def remove_transaction(self, tx: btcutil.Tx, remove_redeemers: bool):
        # Protect concurrent access
        self.mtx.lock()
        self._remove_transaction(tx, remove_redeemers)
        self.mtx.unlock()

    # RemoveDoubleSpends removes all transactions which spend outputs spent by the
    # passed transaction from the memory pool.  Removing those transactions then
    # leads to removing all transactions which rely on them, recursively.  This is
    # necessary when a block is connected to the main chain because the block may
    # contain transactions which were previously unknown to the memory pool.
    #
    # This function is safe for concurrent access.
    def remove_double_spends(self, tx: btcutil.Tx):
        # Protect concurrent access.
        self.mtx.lock()
        for tx_in in tx.get_msg_tx().tx_ins:
            if tx_in.previous_out_point in self.outpoints:
                tx_redeemer = self.outpoints[tx_in.previous_out_point]
                if tx_redeemer.hash() != tx.hash():
                    self._remove_transaction(tx_redeemer, remove_redeemers=True)
        self.mtx.unlock()
        
    # # addTransaction adds the passed transaction to the memory pool.  It should
    # # not be called directly as it doesn't perform any validation.  This is a
    # # helper for maybeAcceptTransaction.
    # #
    # # This function MUST be called with the mempool lock held (for writes).
    # def _add_transaction(self, utxo_view: blockchain.UtxoViewpoint, tx: btcutil.Tx,
    #                      height: int, fee:int) -> TxDesc:
    #     # TODO

