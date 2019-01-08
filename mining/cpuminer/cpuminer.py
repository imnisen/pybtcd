import chaincfg
import mining
import btcutil
import wire
import chainhash
import pyutil
from typing import Callable
import aiochan as ac
import asyncio
import random
import time
import logging

logger = logging.getLogger(__name__)

# hpsUpdateSecs is the number of seconds to wait in between each
# update to the hashes per second monitor.
hpsUpdateSecs = 10

# hashUpdateSec is the number of seconds each worker waits in between
# notifying the speed monitor with how many hashes have been completed
# while they are actively searching for a solution.  This is done to
# reduce the amount of syncs between the workers that must be done to
# keep track of the hashes per second.
hashUpdateSecs = 15


# Config is a descriptor containing the cpu miner configuration.
class Config:
    def __init__(self, chain_params: chaincfg.Params, block_template_generator: mining.BlkTmplGenerator,
                 mining_addrs: [btcutil.Address], process_block: Callable, connected_count: Callable,
                 is_current: Callable):
        """

        :param chaincfg.Params *chaincfg.Params chain_params:
        :param mining.BlkTmplGenerator *mining.BlkTmplGenerator block_template_generator:
        :param [btcutil.Address] []btcutil.Address mining_addrs:
        :param function `func(*btcutil.Block, blockchain.BehaviorFlags) (bool, error)` process_block:
        :param function `func() int32` connected_count:
        :param function `func() bool` is_current:
        """

        # ChainParams identifies which chain parameters the cpu miner is
        # associated with.
        self.chain_params = chain_params

        # BlockTemplateGenerator identifies the instance to use in order to
        # generate block templates that the miner will attempt to solve.
        self.block_template_generator = block_template_generator

        # MiningAddrs is a list of payment addresses to use for the generated
        # blocks.  Each generated block will randomly choose one of them.
        self.mining_addrs = mining_addrs

        # ProcessBlock defines the function to call with any solved blocks.
        # It typically must run the provided block through the same set of
        # rules and handling as any other block coming from the network.
        self.process_block = process_block

        # ConnectedCount defines the function to use to obtain how many other
        # peers the server is connected to.  This is used by the automatic
        # persistent mining routine to determine whether or it should attempt
        # mining.  This is useful because there is no point in mining when not
        # connected to any peers since there would no be anyone to send any
        # found blocks to.
        self.connected_count = connected_count

        # IsCurrent defines the function to use to obtain whether or not the
        # block chain is current.  This is used by the automatic persistent
        # mining routine to determine whether or it should attempt mining.
        # This is useful because there is no point in mining if the chain is
        # not current since any solved blocks would be on a side chain and and
        # up orphaned anyways.
        self.is_current = is_current


# CPUMiner provides facilities for solving blocks (mining) using the CPU in
# a concurrency-safe manner.  It consists of two main goroutines -- a speed
# monitor and a controller for worker goroutines which generate and solve
# blocks.  The number of goroutines can be set via the SetMaxGoRoutines
# function, but the default is based on the number of processor cores in the
# system which is typically sufficient.
class CPUMiner:
    def __init__(self, lock=None, g: mining.BlkTmplGenerator = None, cfg: Config = None, num_workers=None, started=None,
                 discrete_mining=None,
                 submit_block_lock: pyutil.Lock = None, update_num_workers=None, query_hashes_per_sec=None,
                 update_hashes=None, speed_monitor_quit=None, quit=None):
        self._lock = lock or pyutil.Lock()
        self.g = g
        self.cfg = cfg
        self.num_workers = num_workers
        self.started = started
        self.discrete_mining = discrete_mining
        self.submit_block_lock = submit_block_lock or pyutil.Lock()
        self.update_num_workers = update_num_workers
        self.query_hashes_per_sec = query_hashes_per_sec
        self.update_hashes = update_hashes

        self.speed_monitor_quit = speed_monitor_quit
        self.quit = quit

        # # TODO  maybe invent a waitgroup here?
        # wg                sync.WaitGroup
        # workerWg          sync.WaitGroup

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()

    # speedMonitor handles tracking the number of hashes per second the mining
    # process is performing.  It must be run as a goroutine.
    async def _speed_monitor(self):
        logger.info("CPU miner speed monitor started")

        ticker = ac.tick_tock(hpsUpdateSecs)

        hashes_per_sec = 0
        total_hashes = 0

        try:
            while True:
                result, c = await ac.select(self.update_hashes, ticker, (self.query_hashes_per_sec, hashes_per_sec),
                                            self.speed_monitor_quit)

                # Periodic updates from the workers with how many hashes they
                # have performed.
                if c is self.update_hashes:
                    num_hashes = result
                    total_hashes += num_hashes

                # Time to update the hashes per second.
                elif c is ticker:
                    cur_hashes_per_sec = total_hashes / hpsUpdateSecs
                    if hashes_per_sec == 0:
                        hashes_per_sec = cur_hashes_per_sec
                        hashes_per_sec = (hashes_per_sec + cur_hashes_per_sec) / 2
                        total_hashes = 0
                        if hashes_per_sec != 0:
                            logger.info("Hash speed: %6.0f kilohashes/s" % hashes_per_sec / 1000)

                # Request for the number of hashes per second.
                elif c is self.query_hashes_per_sec:
                    # Nothing to do.
                    pass

                else:
                    break

            # TODO m.wg.Done()
            logger.info("CPU miner speed monitor done")
            return

        finally:
            ticker.close()

    # submitBlock submits the passed block to network after ensuring it passes all
    # of the consensus validation rules.
    def _submit_block(self, block: btcutil.Block):
        pass  # TODO

    # solveBlock attempts to find some combination of a nonce, extra nonce, and
    # current timestamp which makes the passed block hash to a value less than the
    # target difficulty.  The timestamp is updated periodically and the passed
    # block is modified with all tweaks during this process.  This means that
    # when the function returns true, the block is ready for submission.
    #
    # This function will return early with false when conditions that trigger a
    # stale block such as a new block showing up or periodically when there are
    # new transactions and enough time has elapsed without finding a solution.
    def _solve_block(self, msg_block: wire.MsgBlock, block_height: int, ticker, quit):
        pass  # TODO

    # generateBlocks is a worker that is controlled by the miningWorkerController.
    # It is self contained in that it creates block templates and attempts to solve
    # them while detecting when it is performing stale work and reacting
    # accordingly by generating a new block template.  When a block is solved, it
    # is submitted.
    #
    # It must be run as a goroutine.
    async def _generate_blocks(self, quit):
        logger.info("Starting generate blocks worker")

        # Start a ticker which is used to signal checks for stale work and
        # updates to the speed monitor.
        ticker = ac.tick_tock(hashUpdateSecs)
        try:
            while True:
                # Quit when the miner is stopped.
                result, c = await ac.select(quit, default="giveup")
                if c is quit:
                    break
                else:
                    # Non-blocking select to fall through
                    pass

                # Wait until there is a connection to at least one other peer
                # since there is no way to relay a found block or receive
                # transactions to work on when there are no connected peers.
                if self.cfg.connected_count() == 0:
                    time.sleep(1)  # TODO TOCHECK async?
                    continue

                # No point in searching for a solution before the chain is
                # synced.  Also, grab the same lock as used for block
                # submission, since the current block will be changing and
                # this would otherwise end up building a new block template on
                # a block that is in the process of becoming stale.
                self.submit_block_lock.lock()
                cur_height = self.g.best_snapshot().height
                if cur_height != 0 and not self.cfg.is_current():
                    self.submit_block_lock.unlock()
                    time.sleep(1)  # TODO TOCHECK async?
                    continue

                # Choose a payment address at random.
                pay_to_addr = random.choices(self.cfg.mining_addrs)

                # Create a new block template using the available transactions
                # in the memory pool as a source of transactions to potentially
                # include in the block.
                try:
                    template = self.g.new_block_template(pay_to_addr)
                except Exception as e:
                    msg = "Failed to create new block template: %s" % e
                    logger.warning(msg)
                    continue
                finally:
                    self.submit_block_lock.unlock()

                # Attempt to solve the block.  The function will exit early
                # with false when conditions that trigger a stale block, so
                # a new block template can be generated.  When the return is
                # true a solution was found, so submit the solved block.
                if self._solve_block(template.block, cur_height + 1, ticker, quit):
                    block = btcutil.Block.from_msg_block(template.block)
                    self._submit_block(block)

            # TODO m.workerWg.Done()
            logger.info("Generate blocks worker done")

        finally:
            ticker.close()

    # miningWorkerController launches the worker goroutines that are used to
    # generate block templates and solve them.  It also provides the ability to
    # dynamically adjust the number of running worker goroutines.
    #
    # It must be run as a goroutine.
    async def _mining_worker_controller(self):
        # launchWorkers groups common code to launch a specified number of
        # workers for generating blocks.
        running_workers = []

        def launch_workers(num_workers: int):
            for _ in range(num_workers):
                quit = ac.Chan()
                running_workers.append(quit)

                # m.workerWg.Add(1)

                ac.go(self._generate_blocks(quit))

        # Launch the current number of workers by default.
        launch_workers(self.num_workers)

        while True:
            result, c = await ac.select(self.update_num_workers, self.quit)

            # Update the number of running workers.
            if c is self.update_num_workers:
                # No change
                num_running = len(running_workers)
                if self.num_workers == num_running:
                    continue

                # Add new workers.
                if self.num_workers > num_running:
                    launch_workers(self.num_workers - num_running)
                    continue

                # Signal the most recently created goroutines to exit.
                for _ in range(num_running - self.num_workers):
                    quit_chan = running_workers.pop()
                    quit_chan.close()
            else:
                for quit_chan in running_workers:
                    quit_chan.close()
                break

        # Wait until all workers shut down to stop the speed monitor since
        # they rely on being able to send updates to it.
        # TODO m.workerWg.Wait()
        self.speed_monitor_quit.close()
        # TODO m.wg.Done()
        return

    # Start begins the CPU mining process as well as the speed monitor used to
    # track hashing metrics.  Calling this function when the CPU miner has
    # already been started will have no effect.
    #
    # This function is safe for concurrent access.
    def start(self):
        with self._lock:
            # Nothing to do if the miner is already running or if running in
            # discrete mode (using GenerateNBlocks).
            if self.started or self.discrete_mining:
                return

            self.quit = ac.Chan()
            self.speed_monitor_quit = ac.Chan()

            # TODO m.wg.Add(2)

            ac.go(self._speed_monitor())
            ac.go(self._mining_worker_controller())

            self.started = True

            logger.info("CPU miner started")

            return

    # Stop gracefully stops the mining process by signalling all workers, and the
    # speed monitor to quit.  Calling this function when the CPU miner has not
    # already been started will have no effect.
    #
    # This function is safe for concurrent access.
    def stop(self):
        with self._lock:
            # Nothing to do if the miner is not currently running or if running in
            # discrete mode (using GenerateNBlocks).
            if not self.started or self.discrete_mining:
                return

            self.quit.close()

            # TODO m.wg.Wait()

            self.started = False

            logger.info("CPU miner stopped")

            return

    # IsMining returns whether or not the CPU miner has been started and is
    # therefore currenting mining.
    #
    # This function is safe for concurrent access.
    def is_mining(self) -> bool:
        with self._lock:
            return self.started

    # HashesPerSecond returns the number of hashes per second the mining process
    # is performing.  0 is returned if the miner is not currently running.
    #
    # This function is safe for concurrent access.
    def hashes_per_second(self) -> float:
        with self._lock:
            # Nothing to do if the miner is not currently running.
            if not self.started:
                return 0

            return self.query_hashes_per_sec.get()  # TODO coroutine?

    # SetNumWorkers sets the number of workers to create which solve blocks.  Any
    # negative values will cause a default number of workers to be used which is
    # based on the number of processor cores in the system.  A value of 0 will
    # cause all CPU mining to be stopped.
    #
    # This function is safe for concurrent access.
    def set_num_workers(self, num_workers: int):
        pass

    # NumWorkers returns the number of workers which are running to solve blocks.
    #
    # This function is safe for concurrent access.
    def get_num_workers(self) -> int:
        with self._lock:
            return self.num_workers

    # GenerateNBlocks generates the requested number of blocks. It is self
    # contained in that it creates block templates and attempts to solve them while
    # detecting when it is performing stale work and reacting accordingly by
    # generating a new block template.  When a block is solved, it is submitted.
    # The function returns a list of the hashes of generated blocks.
    def generate_n_blocks(self, n: int) -> [chainhash.Hash]:
        pass
