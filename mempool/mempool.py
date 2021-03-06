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
from .policy import *

_logger = logging.getLogger(__name__)

# orphanExpireScanInterval is the minimum amount of time in between
# scans of the orphan pool to evict expired transactions.
orphanExpireScanInterval = pyutil.Minute * 5

# orphanTTL is the maximum amount of time an orphan is allowed to
# stay in the orphan pool before it expires and is evicted during the
# next scan.
orphanTTL = pyutil.Minute * 15

# DefaultBlockPrioritySize is the default size in bytes for high-
# priority / low-fee transactions.  It is used to help determine which
# are allowed into the mempool and consequently affects their relay and
# inclusion when generating block templates.
DefaultBlockPrioritySize = 50000


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
                 calc_sequence_lock: typing.Callable = None,
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
        self.calc_sequence_lock = calc_sequence_lock

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
    def __init__(self,
                 tx: btcutil.Tx,
                 added: int,
                 height: int,
                 fee: int,
                 fee_per_kb: int,
                 starting_priority: float = None):
        super().__init__(tx, added, height, fee, fee_per_kb)

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
        self.last_updated = last_updated or None
        self.mtx = mtx or pyutil.RWLock()
        self.cfg = cfg or None
        self.pool = pool or {}
        self.orphans = orphans or {}
        self.orphans_by_prev = orphans_by_prev or {}
        self.outpoints = outpoints or {}

        # exponentially decaying total for penny spends.
        self.penny_total = penny_total or 0.0
        # unix time of last ``penny spend''
        self.last_penny_unix = last_penny_unix or 0

        # nextExpireScan is the time after which the orphan pool will be
        # scanned in order to evict orphans.  This is NOT a hard deadline as
        # the scan will only run when an orphan is added to the pool as opposed
        # to on an unconditional timer.
        self.next_expire_scan = next_expire_scan or (pyutil.now() + orphanExpireScanInterval)

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

    # addTransaction adds the passed transaction to the memory pool.  It should
    # not be called directly as it doesn't perform any validation.  This is a
    # helper for maybeAcceptTransaction.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _add_transaction(self, utxo_view: blockchain.UtxoViewpoint, tx: btcutil.Tx,
                         height: int, fee: int) -> TxDesc:

        # Add the transaction to the pool and mark the referenced outpoints
        # as spent by the pool.
        tx_d = TxDesc(
            tx=tx,
            added=pyutil.now(),
            height=height,
            fee=fee,
            fee_per_kb=int(fee * 1000 / get_tx_virtual_size(tx)),
            starting_priority=mining.calc_priority(tx.get_msg_tx(), utxo_view, height)
        )

        self.pool[tx.hash()] = tx_d

        for tx_in in tx.get_msg_tx().tx_ins:
            self.outpoints[tx_in.previous_out_point] = tx

        self.last_updated = pyutil.now()  # TODO TOCHECK  atomic.StoreInt64(&mp.lastUpdated, time.Now().Unix())

        # Add unconfirmed address index entries associated with the transaction
        # if enabled.
        if self.cfg.addr_index is not None:
            self.cfg.addr_index.add_unconfirmed_tx(tx, utxo_view)  # TODO TOADD

        # Record this tx for fee estimation if enabled.
        if self.cfg.fee_estimator is not None:
            self.cfg.fee_estimator.observe_transaction(tx_d)  # TODO TOADD

        return tx_d

    # checkPoolDoubleSpend checks whether or not the passed transaction is
    # attempting to spend coins already spent by other transactions in the pool.
    # Note it does not check for double spends against transactions already in the
    # main chain.
    #
    # This function MUST be called with the mempool lock held (for reads).
    def _check_pool_double_spend(self, tx: btcutil.Tx):
        for tx_in in tx.get_msg_tx().tx_ins:
            if tx_in.previous_out_point in self.outpoints:
                tx_r = self.outpoints[tx_in.previous_out_point]
                msg = "output %s already spent by transaction %s in the memory pool" % (
                    tx_in.previous_out_point, tx_r.hash()
                )
                raise tx_rule_error(wire.RejectCode.RejectDuplicate, msg)

        return

    # CheckSpend checks whether the passed outpoint is already spent by a
    # transaction in the mempool. If that's the case the spending transaction will
    # be returned, if not nil will be returned.
    def check_spend(self, op: wire.OutPoint) -> btcutil.Tx or None:
        self.mtx.r_lock()
        tx_r = self.outpoints.get(op, None)
        self.mtx.r_unlock()
        return tx_r

    # fetchInputUtxos loads utxo details about the input transactions referenced by
    # the passed transaction.  First, it loads the details form the viewpoint of
    # the main chain, then it adjusts them based upon the contents of the
    # transaction pool.
    #
    # This function MUST be called with the mempool lock held (for reads).
    def _fetch_input_utxos(self, tx: btcutil.Tx) -> blockchain.UtxoViewpoint:

        utxo_view = self.cfg.fetch_utxo_view(tx)

        # Attempt to populate any missing inputs from the transaction pool.
        for tx_in in tx.get_msg_tx().tx_ins:

            prev_out = tx_in.previous_out_point
            entry = utxo_view.lookup_entry(prev_out)

            # we find utxo entry and it is not marked spent
            if entry is not None and not entry.is_spent():
                continue

            # if prev_out_point refer to tx in mempool
            if prev_out.hash in self.pool:
                pool_tx_desc = self.pool[prev_out.hash]
                # AddTxOut ignores out of range index values, so it is
                # safe to call without bounds checking here.
                utxo_view.add_tx_out(pool_tx_desc.tx, prev_out.index, mining.UnminedHeight)

        return utxo_view

    # FetchTransaction returns the requested transaction from the transaction pool.
    # This only fetches from the main transaction pool and does not include
    # orphans.
    #
    # This function is safe for concurrent access.
    def fetch_transaction(self, tx_hash: chainhash.Hash) -> btcutil.Tx:
        self.mtx.r_lock()
        try:
            if tx_hash in self.pool:
                return self.pool[tx_hash].tx
            else:
                raise Exception("transaction is not in the pool")
        finally:
            self.mtx.r_unlock()

    # maybeAcceptTransaction is the internal function which implements the public
    # MaybeAcceptTransaction.  See the comment for MaybeAcceptTransaction for
    # more details.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _maybe_accept_transaction(self,
                                  tx: btcutil.Tx,
                                  is_new: bool,
                                  rate_limit: bool,
                                  reject_dup_orphans: bool) -> ([chainhash.Hash], TxDesc):
        tx_hash = tx.hash()

        # 1. check segwit active
        # If a transaction has witness data, and segwit isn't active yet, If
        # segwit isn't active yet, then we won't accept it into the mempool as
        # it can't be mined yet.
        if tx.get_msg_tx().has_witness():
            segwit_active = self.cfg.is_deployment_active(chaincfg.DeploymentSegwit)

            if not segwit_active:
                msg = "transaction %s has witness data, but segwit isn't active yet" % tx_hash
                raise tx_rule_error(wire.RejectCode.RejectNonstandard, msg)

        # 2. check tx duplicate
        # Don't accept the transaction if it already exists in the pool.  This
        # applies to orphan transactions as well when the reject duplicate
        # orphans flag is set.  This check is intended to be a quick check to
        # weed out duplicates.
        if self._is_transaction_in_pool(tx_hash) or \
                (reject_dup_orphans and self._is_orphan_in_pool(tx_hash)):
            msg = "already have transaction %s" % tx_hash
            raise tx_rule_error(wire.RejectCode.RejectDuplicate, msg)

        # 3. check tx sanity
        # Perform preliminary sanity checks on the transaction.  This makes
        # use of blockchain which contains the invariant rules for what
        # transactions are allowed into blocks.
        try:
            blockchain.check_transaction_sanity(tx)
        except blockchain.RuleError as e:
            raise chain_rule_error(e)

        # 4. check not coinbase
        # A standalone transaction must not be a coinbase transaction.
        if tx.is_coin_base():
            msg = "transaction %s is an individual coinbase" % tx_hash
            raise tx_rule_error(wire.RejectCode.RejectInvalid, msg)

        # Get the current height of the main chain.  A standalone transaction
        # will be mined into the next block at best, so its height is at least
        # one more than the current height.
        best_height = self.cfg.best_height()
        next_block_height = best_height + 1

        median_time_past = self.cfg.median_time_past()

        # 5. check tx standard
        # Don't allow non-standard transactions if the network parameters
        # forbid their acceptance.
        if not self.cfg.policy.accept_non_std:

            try:
                check_transaction_standard(tx, next_block_height, median_time_past,
                                           self.cfg.policy.min_relay_tx_fee, self.cfg.policy.max_tx_version)
            except Exception as e:
                reject_code, found = extract_reject_code(e)
                if not found:
                    reject_code = wire.RejectCode.RejectNonstandard
                msg = "transaction %s is not standard: %s" % (tx_hash, e)
                raise tx_rule_error(reject_code, msg)

        # 6. check tx double spend in pool
        # The transaction may not use any of the same outputs as other
        # transactions already in the pool as that would ultimately result in a
        # double spend.  This check is intended to be quick and therefore only
        # detects double spends within the transaction pool itself.  The
        # transaction could still be double spending coins from the main chain
        # at this point.  There is a more in-depth check that happens later
        # after fetching the referenced transaction inputs from the main chain
        # which examines the actual spend data and prevents double spends.
        self._check_pool_double_spend(tx)

        # 7. fetch utxos of tx spend
        # Fetch all of the unspent transaction outputs referenced by the inputs
        # to this transaction.  This function also attempts to fetch the
        # transaction itself to be used for detecting a duplicate transaction
        # without needing to do a separate lookup.
        try:
            utxo_view = self._fetch_input_utxos(tx)
        except blockchain.RuleError as e:
            raise chain_rule_error(e)

        # 8. check no exist utxo same hash and index as this tx
        # Don't allow the transaction if it exists in the main chain and is not
        # not already fully spent.
        for tx_out_idx in range(len(tx.get_msg_tx().tx_outs)):
            prev_out = wire.OutPoint(
                hash=tx_hash,
                index=tx_out_idx
            )
            entry = utxo_view.lookup_entry(prev_out)
            if entry is not None and not entry.is_spent():
                msg = "transaction already exists"
                raise tx_rule_error(wire.RejectCode.RejectDuplicate, msg)
            utxo_view.remove_entry(prev_out)

        # 9. check referenced utxos is not null and not spend, return missing ones.
        # Transaction is an orphan if any of the referenced transaction outputs
        # don't exist or are already spent.  Adding orphans to the orphan pool
        # is not handled by this function, and the caller should use
        # maybeAddOrphan if this behavior is desired.
        missing_parents = []
        for outpoin, entry in utxo_view.get_entries().items():
            if entry is None or entry.is_spent():
                # Must make a copy of the hash here since the iterator
                # is replaced and taking its address directly would
                # result in all of the entries pointing to the same
                # memory location and thus all be the final hash.
                hash_copy = outpoin.hash.copy()
                missing_parents.append(hash_copy)

        if len(missing_parents) > 0:
            return missing_parents, None

        # 10. check tx sequence_lock
        # Don't allow the transaction into the mempool unless its sequence
        # lock is active, meaning that it'll be allowed into the next block
        # with respect to its defined relative lock times.
        try:
            sequence_lock = self.cfg.calc_sequence_lock(tx, utxo_view)
        except blockchain.RuleError as e:
            return chain_rule_error(e)

        if not blockchain.sequence_lock_active(sequence_lock, next_block_height, median_time_past):
            msg = "transaction's sequence locks on inputs not met"
            raise tx_rule_error(wire.RejectCode.RejectNonstandard, msg)

        # 11. check tx inputs
        # Perform several checks on the transaction inputs using the invariant
        # rules in blockchain for what transactions are allowed into blocks.
        # Also returns the fees associated with the transaction which will be
        # used later.
        try:
            tx_fee = blockchain.check_transaction_inputs(tx, next_block_height, utxo_view, self.cfg.chain_params)
        except blockchain.RuleError as e:
            raise chain_rule_error(e)

        # 12. check tx input standard according to config
        # Don't allow transactions with non-standard inputs if the network
        # parameters forbid their acceptance.
        if not self.cfg.policy.accept_non_std:
            try:
                check_inputs_stand(tx, utxo_view)
            except Exception as e:
                reject_code, found = extract_reject_code(e)
                if not found:
                    reject_code = wire.RejectCode.RejectNonstandard
                msg = "transaction %s has a non-standard input: %s" % (tx_hash, e)
                raise tx_rule_error(reject_code, msg)

        # 13. check tx sig_op_cost below max allowed per tx
        # Don't allow transactions with an excessive number of signature
        # operations which would result in making it impossible to mine.  Since
        # the coinbase address itself can contain signature operations, the
        # maximum allowed signature operations per transaction is less than
        # the maximum allowed signature operations per block.
        # TODO(roasbeef): last bool should be conditional on segwit activation
        try:
            sig_op_cost = blockchain.get_sig_op_cost(tx, is_coin_base_p=False, utxo_view=utxo_view, bip16_p=True,
                                                     seg_wit_p=True)
        except blockchain.RuleError as e:
            raise chain_rule_error(e)
        if sig_op_cost > self.cfg.policy.max_sig_op_cost_per_tx:
            msg = "transaction %s sigop cost is too high: %d > %d" % (
                tx_hash, sig_op_cost, self.cfg.policy.max_sig_op_cost_per_tx)
            raise tx_rule_error(wire.RejectCode.RejectNonstandard, msg)

        # 14. Reject tx that has a large size but small fee
        # Don't allow transactions with fees too low to get into a mined block.
        #
        # Most miners allow a free transaction area in blocks they mine to go
        # alongside the area used for high-priority transactions as well as
        # transactions with fees.  A transaction size of up to 1000 bytes is
        # considered safe to go into this section.  Further, the minimum fee
        # calculated below on its own would encourage several small
        # transactions to avoid fees rather than one single larger transaction
        # which is more desirable.  Therefore, as long as the size of the
        # transaction does not exceeed 1000 less than the reserved space for
        # high-priority transactions, don't require a fee for it.
        serialized_size = get_tx_virtual_size(tx)
        min_fee = calc_min_required_tx_relay_fee(serialized_size, self.cfg.policy.min_relay_tx_fee)
        if serialized_size >= DefaultBlockPrioritySize - 1000 and tx_fee < min_fee:
            msg = "transaction %s has %d fees which is under the required amount of %d" % (
                tx_hash, tx_fee, min_fee
            )
            raise tx_rule_error(wire.RejectCode.RejectInsufficientFee, msg)

        # 15. Reject tx with small fee and low priority
        # Require that free transactions have sufficient priority to be mined
        # in the next block.  Transactions which are being added back to the
        # memory pool from blocks that have been disconnected during a reorg
        # are exempted.
        if is_new and not self.cfg.policy.disable_relay_priority and tx_fee < min_fee:
            current_priority = mining.calc_priority(tx.get_msg_tx(), utxo_view, next_block_height)
            if current_priority <= mining.MinHighPriority:
                msg = "transaction %s has insufficient priority (%s <= %s)" % (
                    tx_hash, current_priority, mining.MinHighPriority
                )
                raise tx_rule_error(wire.RejectCode.RejectInsufficientFee, msg)

        # 16. Reject some small fee tx according to `penny_total mechanism`
        # Free-to-relay transactions are rate limited here to prevent
        # penny-flooding with tiny transactions as a form of attack.
        if rate_limit and tx_fee < min_fee:
            now_unix = pyutil.now()
            # Decay passed data with an exponentially decaying ~10 minute
            # window - matches bitcoind handling.
            self.penny_total *= pow(1.0 - 1.0 / 600.0, now_unix - self.last_penny_unix)
            self.last_penny_unix = now_unix

            # Are we still over the limit?
            if self.penny_total >= self.cfg.policy.free_tx_relay_limit * 10 * 1000:
                msg = "transaction %s has been rejected by the rate limiter due to low fees" % tx_hash
                raise tx_rule_error(wire.RejectCode.RejectInsufficientFee, msg)
            old_total = self.penny_total

            self.penny_total += serialized_size
            _logger.info("rate limit: curTotal %s, nextTotal: %s, limit %s" % (
                old_total, self.penny_total, self.cfg.policy.free_tx_relay_limit * 10 * 1000
            ))

        # 17. check tx input signature correct
        # Verify crypto signatures for each input and reject the transaction if
        # any don't verify.
        try:
            blockchain.validate_transaction_scripts(tx, utxo_view, txscript.StandardVerifyFlags,
                                                    self.cfg.sig_cache, self.cfg.hash_cache)
        except blockchain.RuleError as e:
            raise chain_rule_error(e)

        # Add to transaction pool.
        tx_d = self._add_transaction(utxo_view, tx, best_height, tx_fee)

        _logger.debug("Accepted transaction %s (pool size: %s)" % (tx_hash, len(self.pool)))
        return None, tx_d

    # MaybeAcceptTransaction is the main workhorse for handling insertion of new
    # free-standing transactions into a memory pool.  It includes functionality
    # such as rejecting duplicate transactions, ensuring transactions follow all
    # rules, detecting orphan transactions, and insertion into the memory pool.
    #
    # If the transaction is an orphan (missing parent transactions), the
    # transaction is NOT added to the orphan pool, but each unknown referenced
    # parent is returned.  Use ProcessTransaction instead if new orphans should
    # be added to the orphan pool.
    #
    # This function is safe for concurrent access.
    def maybe_accept_transaction(self,
                                 tx: btcutil.Tx,
                                 is_new: bool,
                                 rate_limit: bool) -> ([chainhash.Hash], TxDesc):
        self.mtx.lock()
        try:
            return self._maybe_accept_transaction(tx, is_new, rate_limit, reject_dup_orphans=True)
        finally:
            self.mtx.unlock()

    # processOrphans is the internal function which implements the public
    # ProcessOrphans.  See the comment for ProcessOrphans for more details.
    #
    # This function MUST be called with the mempool lock held (for writes).
    def _process_orphans(self, accepted_tx: btcutil.Tx) -> [TxDesc]:
        accepted_txns = []

        process_list = [accepted_tx]
        while process_list:
            process_item = process_list.pop(0)

            for tx_out_idx in range(len(process_item.get_msg_tx().tx_outs)):
                # Look up all orphans that redeem the output that is
                # now available.  This will typically only be one, but
                # it could be multiple if the orphan pool contains
                # double spends.  While it may seem odd that the orphan
                # pool would allow this since there can only possibly
                # ultimately be a single redeemer, it's important to
                # track it this way to prevent malicious actors from
                # being able to purposely constructing orphans that
                # would otherwise make outputs unspendable.
                #
                # Skip to the next available output if there are none.
                prev_out = wire.OutPoint(hash=process_item.hash(), index=tx_out_idx)
                if prev_out not in self.orphans_by_prev:
                    continue

                orphans = self.orphans_by_prev[prev_out]
                for tx in orphans.values():
                    try:
                        missing, tx_d = self._maybe_accept_transaction(tx, is_new=True, rate_limit=True,
                                                                       reject_dup_orphans=False)
                    except Exception:
                        # The orphan is now invalid, so there
                        # is no way any other orphans which
                        # redeem any of its outputs can be
                        # accepted.  Remove them.
                        self._remove_orphan(tx, remove_redeemers=True)
                        break

                    # Transaction is still an orphan.  Try the next
                    # orphan which redeems this output.
                    if len(missing) > 0:
                        continue

                    # Transaction was accepted into the main pool.
                    #
                    # Add it to the list of accepted transactions
                    # that are no longer orphans, remove it from
                    # the orphan pool, and add it to the list of
                    # transactions to process so any orphans that
                    # depend on it are handled too.
                    accepted_txns.append(tx_d)
                    self._remove_orphan(tx, remove_redeemers=False)
                    process_list.append(tx)

                    # Only one transaction for this outpoint can be
                    # accepted, so the rest are now double spends
                    # and are removed later.
                    break

        # Recursively remove any orphans that also redeem any outputs redeemed
        # by the accepted transactions since those are now definitive double
        # spends.
        self._remove_orphan_double_spends(accepted_tx)
        for tx_d in accepted_txns:
            self._remove_orphan_double_spends(tx_d.tx)

        return accepted_txns

    # ProcessOrphans determines if there are any orphans which depend on the passed
    # transaction hash (it is possible that they are no longer orphans) and
    # potentially accepts them to the memory pool.  It repeats the process for the
    # newly accepted transactions (to detect further orphans which may no longer be
    # orphans) until there are no more.
    #
    # It returns a slice of transactions added to the mempool.  A nil slice means
    # no transactions were moved from the orphan pool to the mempool.
    #
    # This function is safe for concurrent access.
    def process_orphans(self, accepted_tx: btcutil.Tx) -> [TxDesc]:
        self.mtx.lock()
        accepted_txns = self._process_orphans(accepted_tx)
        self.mtx.unlock()
        return accepted_txns

    # Count returns the number of transactions in the main pool.  It does not
    # include the orphan pool.
    #
    # This function is safe for concurrent access.
    def count(self) -> int:
        self.mtx.r_lock()
        count = len(self.pool)
        self.mtx.r_unlock()
        return count

    # TxHashes returns a slice of hashes for all of the transactions in the memory
    # pool.
    #
    # This function is safe for concurrent access.
    def tx_hashes(self) -> [chainhash.Hash]:
        self.mtx.r_lock()
        hashes = []
        for hash in self.pool.keys():
            hashes.append(hash.copy())
        self.mtx.r_unlock()

        return hashes

    # TxDescs returns a slice of descriptors for all the transactions in the pool.
    # The descriptors are to be treated as read only.
    #
    # This function is safe for concurrent access.
    def tx_descs(self) -> [TxDesc]:
        self.mtx.r_lock()
        descs = []
        for desc in self.pool.values():
            descs.append(desc)
        self.mtx.r_unlock()

        return descs

    # MiningDescs returns a slice of mining descriptors for all the transactions
    # in the pool.
    #
    # This is part of the mining.TxSource interface implementation and is safe for
    # concurrent access as required by the interface contract.
    def mining_descs(self) -> [mining.TxDesc]:
        self.mtx.r_lock()
        descs = []
        for desc in self.pool.values():
            descs.append(desc.tx_desc)
        self.mtx.r_unlock()

        return descs

    # TODO TOADD latter
    def raw_mempool_verbose(self):
        pass

    # LastUpdated returns the last time a transaction was added to or removed from
    # the main pool.  It does not include the orphan pool.
    #
    # This function is safe for concurrent access.
    def get_last_updated(self) -> int:
        return self.last_updated  # TODO this is not concurrent safe now, change latter
