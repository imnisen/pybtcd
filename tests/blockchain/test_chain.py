import unittest
import btcutil
from blockchain.chain import *
from tests.blockchain.common import *


# nodeHeaders is a convenience function that returns the headers for all of
# the passed indexes of the provided nodes.  It is used to construct expected
# located headers in the tests.
def node_headers(nodes: [BlockNode], *indexes) -> [wire.BlockHeader]:
    headers = []
    for i in indexes:
        headers.append(nodes[i].header())
    return headers


# nodeHashes is a convenience function that returns the hashes for all of the
# passed indexes of the provided nodes.  It is used to construct expected hash
# slices in the tests.
def node_hashes(nodes: [BlockNode], *indexes) -> [chainhash.Hash]:
    hashes = []
    for i in indexes:
        hashes.append(nodes[i].hash)
    return hashes


class TestChain(unittest.TestCase):
    # TestHaveBlock tests the HaveBlock API to ensure proper functionality.
    def test_have_block(self):
        # Load up blocks such that there is a side chain.
        # (genesis block) -> 1 -> 2 -> 3 -> 4
        #                          \-> 3a
        test_files = ["blk_0_to_4.dat.bz2", "blk_3A.dat.bz2"]

        blocks = []

        # Load init blocks from files
        for file in test_files:
            block_tmp = load_blocks(file)

            blocks.extend(block_tmp)

        # Create a new database and chain instance to run tests against.
        chain, teardown_func = chain_setup("haveblock", chaincfg.MainNetParams)

        try:
            # Since we're not dealing with the real block chain, set the coinbase
            # maturity to 1.
            chain.chain_params.coinbase_maturity = 1

            for block in blocks[1:]:
                _, is_orphan = chain.process_block_no_exception(block, BFNone)

                self.assertFalse(is_orphan)

            # Insert an orphan block.
            _, is_orphan = chain.process_block_no_exception(btcutil.Block(Block100000), BFNone)
            self.assertTrue(is_orphan)

            # Now we prepare the env
            tests = [
                # Genesis block should be present (in the main chain).
                {"hash": chaincfg.MainNetParams.genesis_hash.to_str(), "want": True},

                # Block 3a should be present (on a side chain).
                {"hash": "00000000474284d20067a4d33f6a02284e6ef70764a3a26d6a5b9df52ef663dd", "want": True},

                # Block 100000 should be present (as an orphan).
                {"hash": "000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506", "want": True},

                # Random hashes should not be available.
                {"hash": "123", "want": False},

            ]
            for test in tests:
                block_hash = chainhash.Hash(test['hash'])
                result = chain.have_block(block_hash)
                self.assertEqual(result, test['want'])
        finally:
            teardown_func()

    # TestCalcSequenceLock tests the LockTimeToSequence function, and the
    # CalcSequenceLock method of a Chain instance. The tests exercise several
    # combinations of inputs to the CalcSequenceLock function in order to ensure
    # the returned SequenceLocks are correct for each test instance.
    def test_calc_sequence_lock(self):
        net_params = chaincfg.SimNetParams

        # We need to activate CSV in order to test the processing logic, so
        # manually craft the block version that's used to signal the soft-fork
        # activation.
        csv_bit = net_params.deployments[chaincfg.DeploymentCSV].bit_number
        block_version = 0x20000000 | (1 << csv_bit)

        # Generate enough synthetic blocks to activate CSV.
        chain = new_fake_chain(net_params)
        node = chain.best_chain.tip()
        block_time = node.header().timestamp
        num_blocks_to_active = (net_params.miner_confirmation_window * 3)  # defined -> started -> locked_in -> active

        for _ in range(num_blocks_to_active):
            # the new block time
            block_time = block_time + 1
            # Make the new fake node
            node = new_fake_node(parent=node, block_version=block_version, bits=0, timestamp=block_time)
            # Add to chain index
            chain.index.add_node(node)
            # set chainview
            chain.best_chain.set_tip(node)

        # Create a utxo view with a fake utxo for the inputs used in the
        # transactions created below.  This utxo is added such that it has an
        # age of 4 blocks.
        target_tx = btcutil.Tx.from_msg_tx(
            wire.MsgTx(
                tx_outs=[
                    wire.TxOut(
                        pk_script=bytes(),
                        value=10
                    )
                ]
            )
        )

        utxo_view = UtxoViewpoint()
        utxo_view.add_tx_outs(target_tx, num_blocks_to_active - 4)
        utxo_view.set_best_hash(node.hash)

        # Create a utxo that spends the fake utxo created above for use in the
        # transactions created in the tests.  It has an age of 4 blocks.  Note
        # that the sequence lock heights are always calculated from the same
        # point of view that they were originally calculated from for a given
        # utxo.  That is to say, the height prior to it.
        utxo = wire.OutPoint(
            hash=target_tx.hash(),
            index=0
        )
        prev_utxo_height = num_blocks_to_active - 4

        # Obtain the median time past from the PoV of the input created above.
        # The MTP for the input is the MTP from the PoV of the block *prior*
        # to the one that included it.
        median_time = node.relative_ancestor(distance=5).calc_past_median_time()

        # The median time calculated from the PoV of the best block in the
        # test chain.  For unconfirmed inputs, this value will be used since
        # the MTP will be calculated from the PoV of the yet-to-be-mined
        # block.
        next_median_time = node.calc_past_median_time()
        next_block_height = num_blocks_to_active + 1

        # Add an additional transaction which will serve as our unconfirmed
        # output.
        un_conf_tx = wire.MsgTx(
            tx_outs=[
                wire.TxOut(
                    pk_script=bytes(),
                    value=5
                )
            ]
        )

        un_conf_utxo = wire.OutPoint(
            hash=un_conf_tx.tx_hash(),
            index=0,
        )

        # TOCONSIDER why height 0x7fffffff?
        # Adding a utxo with a height of 0x7fffffff indicates that the output
        # is currently unmined.
        utxo_view.add_tx_outs(btcutil.Tx.from_msg_tx(un_conf_tx), block_height=0x7fffffff)

        # Here comes the test cases
        tests = [

            # A transaction of version one should disable sequence locks
            # as the new sequence number semantics only apply to
            # transactions version 2 or higher.
            {
                "tx": wire.MsgTx(
                    version=1,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=3)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=-1,
                    block_height=-1
                )
            },

            # A transaction with a single input with max sequence number.
            # This sequence number has the high bit set, so sequence locks
            # should be disabled.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=wire.MaxTxInSequenceNum
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=-1,
                    block_height=-1
                )
            },

            # A transaction with a single input whose lock time is
            # expressed in seconds.  However, the specified lock time is
            # below the required floor for time based lock times since
            # they have time granularity of 512 seconds.  As a result, the
            # seconds lock-time should be just before the median time of
            # the targeted block.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=2)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=median_time - 1,
                    block_height=-1
                )
            },

            # A transaction with a single input whose lock time is
            # expressed in seconds.  The number of seconds should be 1023
            # seconds after the median past time of the last block in the
            # chain.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=1024)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=median_time + 1023,
                    block_height=-1
                )
            },

            # A transaction with multiple inputs.  The first input has a
            # lock time expressed in seconds.  The second input has a
            # sequence lock in blocks with a value of 4.  The last input
            # has a sequence number with a value of 5, but has the disable
            # bit set.  So the first lock should be selected as it's the
            # latest lock that isn't disabled.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=2560)
                        ),

                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=4)
                        ),

                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=5) | wire.SequenceLockTimeDisabled
                        ),
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=median_time + (5 << wire.SequenceLockTimeGranularity) - 1,
                    block_height=prev_utxo_height + 3
                )
            },

            # Transaction with a single input.  The input's sequence number
            # encodes a relative lock-time in blocks (3 blocks).  The
            # sequence lock should  have a value of -1 for seconds, but a
            # height of 2 meaning it can be included at height 3.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=3)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=-1,
                    block_height=prev_utxo_height + 2
                )
            },

            # A transaction with two inputs with lock times expressed in
            # seconds.  The selected sequence lock value for seconds should
            # be the time further in the future.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=5120)
                        ),
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=2560)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=median_time + (10 << wire.SequenceLockTimeGranularity) - 1,
                    block_height=-1
                )
            },

            # A transaction with two inputs with lock times expressed in
            # blocks.  The selected sequence lock value for blocks should
            # be the height further in the future, so a height of 10
            # indicating it can be included at height 11.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=1)
                        ),
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=11)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=-1,
                    block_height=prev_utxo_height + 10
                )
            },

            # A transaction with multiple inputs.  Two inputs are time
            # based, and the other two are block based. The lock lying
            # further into the future for both inputs should be chosen.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=2560)
                        ),
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=6656)
                        ),
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=3)
                        ),
                        wire.TxIn(
                            previous_out_point=utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=9)
                        )
                    ]
                ),
                "view": utxo_view,
                "mempool": False,
                "want": SequenceLock(
                    seconds=median_time + (13 << wire.SequenceLockTimeGranularity) - 1,
                    block_height=prev_utxo_height + 8
                )
            },

            # A transaction with a single unconfirmed input.  As the input
            # is confirmed, the height of the input should be interpreted
            # as the height of the *next* block.  So, a 2 block relative
            # lock means the sequence lock should be for 1 block after the
            # *next* block height, indicating it can be included 2 blocks
            # after that.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=un_conf_utxo,
                            sequence=lock_time_to_sequence(is_seconds=False, locktime=2)
                        ),
                    ]
                ),
                "view": utxo_view,
                "mempool": True,
                "want": SequenceLock(
                    seconds=-1,
                    block_height=next_block_height + 1
                )
            },

            # A transaction with a single unconfirmed input.  The input has
            # a time based lock, so the lock time should be based off the
            # MTP of the *next* block.
            {
                "tx": wire.MsgTx(
                    version=2,
                    tx_ins=[
                        wire.TxIn(
                            previous_out_point=un_conf_utxo,
                            sequence=lock_time_to_sequence(is_seconds=True, locktime=1024)
                        ),
                    ]
                ),
                "view": utxo_view,
                "mempool": True,
                "want": SequenceLock(
                    seconds=next_median_time + 1023,
                    block_height=-1,
                )
            },

        ]

        for test in tests:
            util_tx = btcutil.Tx.from_msg_tx(test['tx'])
            seq_lock = chain.calc_sequence_lock(util_tx, test['view'], test['mempool'])

            self.assertEqual(seq_lock.seconds, test['want'].seconds)
            self.assertEqual(seq_lock.block_height, test['want'].block_height)

    # TestLocateInventory ensures that locating inventory via the LocateHeaders and
    # LocateBlocks functions behaves as expected.
    def test_locate_inventory(self):
        # Construct a synthetic block chain with a block index consisting of
        # the following structure.
        #     genesis -> 1 -> 2 -> ... -> 15 -> 16  -> 17  -> 18
        #                                   \-> 16a -> 17a
        chain = new_fake_chain(chaincfg.MainNetParams)
        branch0_nodes = chained_nodes(chain.best_chain.genesis(), num_nodes=18)
        branch1_nodes = chained_nodes(branch0_nodes[14],
                                      num_nodes=2)

        for node in branch0_nodes:
            chain.index.add_node(node)

        for node in branch1_nodes:
            chain.index.add_node(node)

        chain.best_chain.set_tip(branch0_nodes[-1])

        # Create chain views for different branches of the overall chain to
        # simulate a local and remote node on different parts of the chain.
        local_view = ChainView.new_from_tip(branch0_nodes[-1])
        remote_view = ChainView.new_from_tip(branch1_nodes[-1])

        # Create a chain view for a completely unrelated block chain to
        # simulate a remote node on a totally different chain.
        unrelated_branch_nodes = chained_nodes(parent=None, num_nodes=5)
        unrelated_view = ChainView.new_from_tip(unrelated_branch_nodes[-1])

        tests = [
            # Empty block locators and unknown stop hash.  No
            # inventory should be located.
            {
                "name": "no locators, no stop",
                "locator": None,
                "hash_stop": chainhash.Hash(),
                "max_allowed": 0,
                "headers": None,
                "hashes": None,
            },

            # Empty block locators and stop hash in side chain.
            # The expected result is the requested block.
            {
                "name": "no locators, stop in side",
                "locator": None,
                "hash_stop": branch1_nodes[-1].hash,
                "max_allowed": 0,
                "headers": node_headers(branch1_nodes, 1),
                "hashes": node_hashes(branch1_nodes, 1),
            },

            # Empty block locators and stop hash in main chain.
            # The expected result is the requested block.
            {
                "name": "no locators, stop in main",
                "locator": None,
                "hash_stop": branch0_nodes[12].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 12),
                "hashes": node_hashes(branch0_nodes, 12),
            },

            # Locators based on remote being on side chain and a
            # stop hash local node doesn't know about.  The
            # expected result is the blocks after the fork point in
            # the main chain and the stop hash has no effect.
            {
                "name": "remote side chain, unknown stop",
                "locator": remote_view.block_locator(node=None),
                "hash_stop": chainhash.Hash(bytes([0x01])),
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 15, 16, 17),
            },

            # Locators based on remote being on side chain and a
            # stop hash in side chain.  The expected result is the
            # blocks after the fork point in the main chain and the
            # stop hash has no effect.
            {
                "name": "remote side chain, stop in side",
                "locator": remote_view.block_locator(node=None),
                "hash_stop": branch1_nodes[-1].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 15, 16, 17),
            },

            # Locators based on remote being on side chain and a
            # stop hash in main chain, but before fork point.  The
            # expected result is the blocks after the fork point in
            # the main chain and the stop hash has no effect.
            {
                "name": "remote side chain, stop in main before",
                "locator": remote_view.block_locator(node=None),
                "hash_stop": branch0_nodes[13].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 15, 16, 17),
            },

            # Locators based on remote being on side chain and a
            # stop hash in main chain, but exactly at the fork
            # point.  The expected result is the blocks after the
            # fork point in the main chain and the stop hash has no
            # effect.
            {
                "name": "remote side chain, stop in main exact",
                "locator": remote_view.block_locator(node=None),
                "hash_stop": branch0_nodes[14].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 15, 16, 17),
            },

            # Locators based on remote being on side chain and a
            # stop hash in main chain just after the fork point.
            # The expected result is the blocks after the fork
            # point in the main chain up to and including the stop
            # hash.
            {
                "name": "remote side chain, stop in main after",
                "locator": remote_view.block_locator(node=None),
                "hash_stop": branch0_nodes[15].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 15),
                "hashes": node_hashes(branch0_nodes, 15),
            },

            # Locators based on remote being on side chain and a
            # stop hash in main chain some time after the fork
            # point.  The expected result is the blocks after the
            # fork point in the main chain up to and including the
            # stop hash.
            {
                "name": "remote side chain, stop in main after more",
                "locator": remote_view.block_locator(node=None),
                "hash_stop": branch0_nodes[16].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 15, 16),
                "hashes": node_hashes(branch0_nodes, 15, 16),
            },

            # Locators based on remote being on main chain in the
            # past and a stop hash local node doesn't know about.
            # The expected result is the blocks after the known
            # point in the main chain and the stop hash has no
            # effect.
            {
                "name": "remote main chain past, unknown stop",
                "locator": local_view.block_locator(node=branch0_nodes[12]),
                "hash_stop": chainhash.Hash(bytes([0x01])),
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 13, 14, 15, 16, 17),
            },

            # Locators based on remote being on main chain in the
            # past and a stop hash in a side chain.  The expected
            # result is the blocks after the known point in the
            # main chain and the stop hash has no effect.
            {
                "name": "remote main chain past, stop in side",
                "locator": local_view.block_locator(node=branch0_nodes[12]),
                "hash_stop": branch1_nodes[-1].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 13, 14, 15, 16, 17),
            },

            # Locators based on remote being on main chain in the
            # past and a stop hash in the main chain before that
            # point.  The expected result is the blocks after the
            # known point in the main chain and the stop hash has
            # no effect.
            {
                "name": "remote main chain past, stop in main before",
                "locator": local_view.block_locator(node=branch0_nodes[12]),
                "hash_stop": branch0_nodes[11].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 13, 14, 15, 16, 17),
            },

            # Locators based on remote being on main chain in the
            # past and a stop hash in the main chain exactly at that
            # point.  The expected result is the blocks after the
            # known point in the main chain and the stop hash has
            # no effect.
            {
                "name": "remote main chain past, stop in main exact",
                "locator": local_view.block_locator(node=branch0_nodes[12]),
                "hash_stop": branch0_nodes[12].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 13, 14, 15, 16, 17),
            },

            # Locators based on remote being on main chain in the
            # past and a stop hash in the main chain just after
            # that point.  The expected result is the blocks after
            # the known point in the main chain and the stop hash
            # has no effect.
            {
                "name": "remote main chain past, stop in main after",
                "locator": local_view.block_locator(node=branch0_nodes[12]),
                "hash_stop": branch0_nodes[13].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 13),
                "hashes": node_hashes(branch0_nodes, 13),
            },

            # Locators based on remote being on main chain in the
            # past and a stop hash in the main chain some time
            # after that point.  The expected result is the blocks
            # after the known point in the main chain and the stop
            # hash has no effect.
            {
                "name": "remote main chain past, stop in main after more",
                "locator": local_view.block_locator(node=branch0_nodes[12]),
                "hash_stop": branch0_nodes[15].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 13, 14, 15),
                "hashes": node_hashes(branch0_nodes, 13, 14, 15),
            },

            # Locators based on remote being at exactly the same
            # point in the main chain and a stop hash local node
            # doesn't know about.  The expected result is no
            # located inventory.
            {
                "name": "remote main chain same, unknown stop",
                "locator": local_view.block_locator(node=None),
                "hash_stop": chainhash.Hash(bytes([0x01])),
                "max_allowed": 0,
                "headers": None,
                "hashes": None,
            },

            # Locators based on remote being at exactly the same
            # point in the main chain and a stop hash at exactly
            # the same point.  The expected result is no located
            # inventory.
            {
                "name": "remote main chain same, stop same point",
                "locator": local_view.block_locator(node=None),
                "hash_stop": branch0_nodes[-1].hash,
                "max_allowed": 0,
                "headers": None,
                "hashes": None,
            },

            # Locators from remote that don't include any blocks
            # the local node knows.  This would happen if the
            # remote node is on a completely separate chain that
            # isn't rooted with the same genesis block.  The
            # expected result is the blocks after the genesis
            # block.
            {
                "name": "remote unrelated chain",
                "locator": unrelated_view.block_locator(node=None),
                "hash_stop": chainhash.Hash(bytes()),
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 0, 1, 2, 3, 4, 5, 6,
                                        7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 0, 1, 2, 3, 4, 5, 6,
                                      7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
            },

            # Locators from remote for second block in main chain
            # and no stop hash, but with an overridden max limit.
            # The expected result is the blocks after the second
            # block limited by the max.
            {
                "name": "remote genesis",
                "locator": [branch0_nodes[0].hash],
                "hash_stop": chainhash.Hash(bytes()),
                "max_allowed": 3,
                "headers": node_headers(branch0_nodes, 1, 2, 3),
                "hashes": node_hashes(branch0_nodes, 1, 2, 3),
            },

            # Poorly formed locator.
            #
            # Locator from remote that only includes a single
            # block on a side chain the local node knows.  The
            # expected result is the blocks after the genesis
            # block since even though the block is known, it is on
            # a side chain and there are no more locators to find
            # the fork point.
            {
                "name": "weak locator, single known side block",
                "locator": [branch1_nodes[1].hash],
                "hash_stop": chainhash.Hash(bytes()),
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 0, 1, 2, 3, 4, 5, 6,
                                        7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 0, 1, 2, 3, 4, 5, 6,
                                      7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
            },

            # Poorly formed locator.
            #
            # Locator from remote that only includes multiple
            # blocks on a side chain the local node knows however
            # none in the main chain.  The expected result is the
            # blocks after the genesis block since even though the
            # blocks are known, they are all on a side chain and
            # there are no more locators to find the fork point.
            {
                "name": "weak locator, multiple known side blocks",
                "locator": [branch1_nodes[1].hash, branch1_nodes[0].hash],
                "hash_stop": chainhash.Hash(bytes()),
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 0, 1, 2, 3, 4, 5, 6,
                                        7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
                "hashes": node_hashes(branch0_nodes, 0, 1, 2, 3, 4, 5, 6,
                                      7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
            },

            # Poorly formed locator.
            #
            # Locator from remote that only includes multiple
            # blocks on a side chain the local node knows however
            # none in the main chain but includes a stop hash in
            # the main chain.  The expected result is the blocks
            # after the genesis block up to the stop hash since
            # even though the blocks are known, they are all on a
            # side chain and there are no more locators to find the
            # fork point.
            {
                "name": "weak locator, multiple known side blocks, stop in main",
                "locator": [branch1_nodes[1].hash, branch1_nodes[0].hash],
                "hash_stop": branch0_nodes[5].hash,
                "max_allowed": 0,
                "headers": node_headers(branch0_nodes, 0, 1, 2, 3, 4, 5),
                "hashes": node_hashes(branch0_nodes, 0, 1, 2, 3, 4, 5),
            },

        ]

        for test in tests:
            # Ensure the expected headers are located
            if test['max_allowed'] != 0:
                # Need to use the unexported function to override the
                # max allowed for headers.
                chain.chain_lock.r_lock()
                headers = chain._locate_headers(test['locator'], test['hash_stop'], test['max_allowed'])
                chain.chain_lock.r_unlock()
            else:
                headers = chain.locate_headers(test['locator'], test['hash_stop'])

            if test['headers']:
                self.assertListEqual(headers, test['headers'])
            else:
                self.assertIsNone(headers)

            # Ensure the expected block hashes are located
            max_allowed = wire.MaxBlockHeadersPerMsg
            if test['max_allowed'] != 0:
                max_allowed = test['max_allowed']

            hashes = chain.locate_blocks(test['locator'], test['hash_stop'], max_allowed)

            if test['hashes']:
                self.assertListEqual(hashes, test['hashes'])
            else:
                self.assertIsNone(hashes)
