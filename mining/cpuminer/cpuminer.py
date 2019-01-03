import chaincfg
import mining
import btcutil
import wire
import chainhash
from typing import Callable


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
    def __init__(self, ):
        pass  # TODO

    # speedMonitor handles tracking the number of hashes per second the mining
    # process is performing.  It must be run as a goroutine.
    def _speed_monitor(self):
        pass

    # submitBlock submits the passed block to network after ensuring it passes all
    # of the consensus validation rules.
    def _submit_block(self, block: btcutil.Block):
        pass

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
        pass

    # generateBlocks is a worker that is controlled by the miningWorkerController.
    # It is self contained in that it creates block templates and attempts to solve
    # them while detecting when it is performing stale work and reacting
    # accordingly by generating a new block template.  When a block is solved, it
    # is submitted.
    #
    # It must be run as a goroutine.
    def _generate_blocks(self, quit):
        pass

    # miningWorkerController launches the worker goroutines that are used to
    # generate block templates and solve them.  It also provides the ability to
    # dynamically adjust the number of running worker goroutines.
    #
    # It must be run as a goroutine.
    def _mining_worker_controller(self):
        pass

    # Start begins the CPU mining process as well as the speed monitor used to
    # track hashing metrics.  Calling this function when the CPU miner has
    # already been started will have no effect.
    #
    # This function is safe for concurrent access.
    def start(self):
        pass

    # Stop gracefully stops the mining process by signalling all workers, and the
    # speed monitor to quit.  Calling this function when the CPU miner has not
    # already been started will have no effect.
    #
    # This function is safe for concurrent access.
    def stop(self):
        pass

    # IsMining returns whether or not the CPU miner has been started and is
    # therefore currenting mining.
    #
    # This function is safe for concurrent access.
    def is_mining(self) -> bool:
        pass

    # HashesPerSecond returns the number of hashes per second the mining process
    # is performing.  0 is returned if the miner is not currently running.
    #
    # This function is safe for concurrent access.
    def hashes_per_second(self) -> float:
        pass

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
    def num_workers(self) -> int:
        pass

    # GenerateNBlocks generates the requested number of blocks. It is self
    # contained in that it creates block templates and attempts to solve them while
    # detecting when it is performing stale work and reacting accordingly by
    # generating a new block template.  When a block is solved, it is submitted.
    # The function returns a list of the hashes of generated blocks.
    def generate_n_blocks(self, n: int) -> [chainhash.Hash]:
        pass
