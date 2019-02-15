import chaincfg
import typing
import txscript
import btcutil
import mining
import pyutil
import logging

_logger = logging.getLogger(__name__)

# orphanExpireScanInterval is the minimum amount of time in between
# scans of the orphan pool to evict expired transactions.
orphanExpireScanInterval = pyutil.Minute * 5


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
        self.mtx = mtx
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

    # TODO
    # removeOrphan is the internal function which implements the public
    # RemoveOrphan.  See the comment for RemoveOrphan for more details.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _remove_orphan(self, tx: btcutil.Tx, remove_redeemers: bool):
        pass

    # limitNumOrphans limits the number of orphan transactions by evicting a random
    # orphan if adding a new one would cause it to overflow the max allowed.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def limit_num_orphans(self):

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
