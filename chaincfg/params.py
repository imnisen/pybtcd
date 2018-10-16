import chainhash
import wire
from .genesis import *
from .constant import *

######################################
# These variables are the chain proof-of-work limit parameters for each default
# network.
######################################

# mainPowLimit is the highest proof of work value a Bitcoin block can
# have for the main network.  It is the value 2^224 - 1.
mainPowLimit = 2 ** 224 - 1

# regressionPowLimit is the highest proof of work value a Bitcoin block
# can have for the regression test network.  It is the value 2^255 - 1.
regressionPowLimit = 2 ** 255 - 1

# testNet3PowLimit is the highest proof of work value a Bitcoin block
# can have for the test network (version 3).  It is the value
# 2^224 - 1.
testNet3PowLimit = 2 ** 224 - 1

# simNetPowLimit is the highest proof of work value a Bitcoin block
# can have for the simulation test network.  It is the value 2^255 - 1.
simNetPowLimit = 2 * 255 - 1


# Checkpoint identifies a known good point in the block chain.  Using
# checkpoints allows a few optimizations for old blocks during initial download
# and also prevents forks from old blocks.
#
# Each checkpoint is selected based upon several factors.  See the
# documentation for blockchain.IsCheckpointCandidate for details on the
# selection criteria.
class Checkpoint:
    def __init__(self, height=None, hash=None):
        """

        :param int32 height:
        :param chainhash.Hash hash:
        """
        self.height = height or 0
        self.hash = hash or chainhash.Hash()


# DNSSeed identifies a DNS seed.
class DNSSeed:
    def __init__(self, host=None, has_filtering=None):
        """

        :param str host:
        :param bool has_filtering:
        """
        # Host defines the hostname of the seed.
        self.host = host or ""

        # HasFiltering defines whether the seed supports filtering
        # by service flags (wire.ServiceFlag).
        self.has_filtering = has_filtering or False

    def __str__(self):
        return self.host


# ConsensusDeployment defines details related to a specific consensus rule
# change that is voted in.  This is part of BIP0009.
class ConsensusDeployment:
    def __init__(self, bit_number=None, start_time=None, expire_time=None):
        """

        :param uint8 bit_number:
        :param uint64 start_time:
        :param uint64 expire_time:
        """
        # BitNumber defines the specific bit number within the block version
        # this particular soft-fork deployment refers to.
        self.bit_number = bit_number or 0

        # StartTime is the median block time after which voting on the
        # deployment starts.
        self.start_time = start_time or 0

        # ExpireTime is the median block time after which the attempted
        # deployment expires.
        self.expire_time = expire_time or 0


######################################
# Constants that define the deployment offset in the deployments field of the
# parameters for each deployment.  This is useful to be able to get the details
# of a specific deployment by name.
######################################

# DeploymentTestDummy defines the rule change deployment ID for testing
# purposes.
DeploymentTestDummy = 0

# DeploymentCSV defines the rule change deployment ID for the CSV
# soft-fork package. The CSV package includes the deployment of BIPS
# 68, 112, and 113.
DeploymentCSV = 1

# DeploymentSegwit defines the rule change deployment ID for the
# Segregated Witness (segwit) soft-fork package. The segwit package
# includes the deployment of BIPS 141, 142, 144, 145, 147 and 173.
DeploymentSegwit = 2

# NOTE: DefinedDeployments must always come last since it is used to
# determine how many defined deployments there currently are.

# DefinedDeployments is the number of currently defined deployments.
DefinedDeployments = 3


# Params defines a Bitcoin network by its parameters.  These parameters may be
# used by Bitcoin applications to differentiate networks as well as addresses
# and keys for one network from those intended for use on another network.
class Params:
    def __init__(self, name=None, net=None, default_port=None, dns_seeds=None,
                 genesis_block=None, genesis_hash=None, pow_limit=None, pow_limit_bits=None,
                 bip0034_height=None, bip0065_height=None, bip0066_height=None, coinbase_maturity=None,
                 subsidy_reduction_interval=None, target_timespan=None, target_time_per_block=None,
                 retarget_adjustment_factor=None, reduce_min_difficulty=None, min_diff_reduction_time=None,
                 generate_supported=None, checkpoints=None, rule_change_activation_threshold=None,
                 miner_confirmation_window=None, deployments=None, relay_non_std_txs=None,
                 bech32_hrp_segwit=None, pub_key_hash_addr_id=None, script_hash_addr_id=None,
                 private_key_id=None, witness_pub_key_hash_addr_id=None, witness_script_hash_addr_id=None,
                 hd_private_key_id=None, hd_public_key_id=None, hd_coin_type=None

                 ):
        """"""

        # Name defines a human-readable identifier for the network.
        self.name = name or ""

        # Net defines the magic bytes used to identify the network.
        self.net = net or wire.BitcoinNet.from_int(0)

        # DefaultPort defines the default peer-to-peer port for the network.
        self.default_port = default_port or ""

        # DNSSeeds defines a list of DNS seeds for the network that are used
        # as one method to discover peers.
        self.dns_seeds = dns_seeds or []

        # GenesisBlock defines the first block of the chain.
        self.genesis_block = genesis_block or wire.MsgBlock()

        # GenesisHash is the starting block hash.
        self.genesis_hash = genesis_hash or chainhash.Hash()

        # PowLimit defines the highest allowed proof of work value for a block
        # as a uint256.
        self.pow_limit = pow_limit or 0

        # PowLimitBits defines the highest allowed proof of work value for a
        # block in compact form.
        self.pow_limit_bits = pow_limit_bits or 0

        # These fields define the block heights at which the specified softfork
        # BIP became active.
        self.bip0034_height = bip0034_height or 0
        self.bip0065_height = bip0065_height or 0
        self.bip0066_height = bip0066_height or 0

        # CoinbaseMaturity is the number of blocks required before newly mined
        # coins (coinbase transactions) can be spent.
        self.coinbase_maturity = coinbase_maturity or 0

        # SubsidyReductionInterval is the interval of blocks before the subsidy
        # is reduced.
        self.subsidy_reduction_interval = subsidy_reduction_interval or 0

        # TargetTimespan is the desired amount of time that should elapse
        # before the block difficulty requirement is examined to determine how
        # it should be changed in order to maintain the desired block
        # generation rate.
        self.target_timespan = target_timespan or 0

        # TargetTimePerBlock is the desired amount of time to generate each
        # block.
        self.target_time_per_block = target_time_per_block or 0

        # RetargetAdjustmentFactor is the adjustment factor used to limit
        # the minimum and maximum amount of adjustment that can occur between
        # difficulty retargets.
        self.retarget_adjustment_factor = retarget_adjustment_factor or 0

        # ReduceMinDifficulty defines whether the network should reduce the
        # minimum required difficulty after a long enough period of time has
        # passed without finding a block.  This is really only useful for test
        # networks and should not be set on a main network.
        self.reduce_min_difficulty = reduce_min_difficulty or False

        # MinDiffReductionTime is the amount of time after which the minimum
        # required difficulty should be reduced when a block hasn't been found.
        #
        # NOTE: This only applies if ReduceMinDifficulty is true.
        self.min_diff_reduction_time = min_diff_reduction_time or 0

        # GenerateSupported specifies whether or not CPU mining is allowed.
        self.generate_supported = generate_supported or False

        # Checkpoints ordered from oldest to newest.
        self.checkpoints = checkpoints or []

        # These fields are related to voting on consensus rule changes as
        # defined by BIP0009.
        #
        # RuleChangeActivationThreshold is the number of blocks in a threshold
        # state retarget window for which a positive vote for a rule change
        # must be cast in order to lock in a rule change. It should typically
        # be 95% for the main network and 75% for test networks.
        #
        # MinerConfirmationWindow is the number of blocks in each threshold
        # state retarget window.
        #
        # Deployments define the specific consensus rule changes to be voted
        # on.
        self.rule_change_activation_threshold = rule_change_activation_threshold or 0
        self.miner_confirmation_window = miner_confirmation_window or 0
        self.deployments = deployments or []

        # Mempool parameters
        self.relay_non_std_txs = relay_non_std_txs or False

        # Human-readable part for Bech32 encoded segwit addresses, as defined
        # in BIP 173.
        self.bech32_hrp_segwit = bech32_hrp_segwit or ""

        # Address encoding magics
        self.pub_key_hash_addr_id = pub_key_hash_addr_id or bytes()  # First byte of a P2PKH address
        self.script_hash_addr_id = script_hash_addr_id or bytes()  # First byte of a P2SH address
        self.private_key_id = private_key_id or bytes()  # First byte of a WIF private key
        self.witness_pub_key_hash_addr_id = witness_pub_key_hash_addr_id or bytes()  # First byte of a P2WPKH address
        self.witness_script_hash_addr_id = witness_script_hash_addr_id or bytes()  # First byte of a P2WSH address

        # BIP32 hierarchical deterministic extended key magics
        self.hd_private_key_id = hd_private_key_id or bytes(4)
        self.hd_public_key_id = hd_public_key_id or bytes(4)

        # BIP44 coin type used in the hierarchical deterministic path for
        # address generation.
        self.hd_coin_type = hd_coin_type or 0


# MainNetParams defines the network parameters for the main Bitcoin network.
MainNetParams = Params(
    name="mainnet",
    net=wire.BitcoinNet.MainNet,
    default_port="8333",
    dns_seeds=[
        DNSSeed(host="seed.bitcoin.sipa.be", has_filtering=True),
        DNSSeed(host="dnsseed.bluematt.me", has_filtering=True),
        DNSSeed(host="dnsseed.bitcoin.dashjr.org", has_filtering=False),
        DNSSeed(host="seed.bitcoinstats.com", has_filtering=True),
        DNSSeed(host="seed.bitnodes.io", has_filtering=False),
        DNSSeed(host="seed.bitcoin.jonasschnelli.ch", has_filtering=True),
    ],

    # Chain parameters
    genesis_block=genesisBlock,
    genesis_hash=genesisHash,
    pow_limit=mainPowLimit,
    pow_limit_bits=0x1d00ffff,
    bip0034_height=227931,  # 000000000000024b89b42a942fe0d9fea3bb44ab7bd1b19115dd6a759c0808b8
    bip0065_height=388381,  # 000000000000000004c2b624ed5d7756c508d90fd0da2c7c679febfa6c4735f0
    bip0066_height=363725,  # 00000000000000000379eaa19dce8c9b722d46ae6a57c2f1a988119488b50931
    coinbase_maturity=100,
    subsidy_reduction_interval=210000,
    target_timespan=3600 * 24 * 14,  # 14 days
    target_time_per_block=60 * 10,  # 10minutes
    retarget_adjustment_factor=4,  # 25% less, 400% more
    reduce_min_difficulty=False,
    min_diff_reduction_time=0,
    generate_supported=False,

    # Checkpoints ordered from oldest to newest.
    checkpoints=[
        Checkpoint(height=11111,
                   hash=chainhash.Hash("0000000069e244f73d78e8fd29ba2fd2ed618bd6fa2ee92559f542fdb26e7c1d")),
        Checkpoint(height=33333,
                   hash=chainhash.Hash("000000002dd5588a74784eaa7ab0507a18ad16a236e7b1ce69f00d7ddfb5d0a6")),
        Checkpoint(height=74000,
                   hash=chainhash.Hash("0000000000573993a3c9e41ce34471c079dcf5f52a0e824a81e7f953b8661a20")),
        Checkpoint(height=105000,
                   hash=chainhash.Hash("00000000000291ce28027faea320c8d2b054b2e0fe44a773f3eefb151d6bdc97")),
        Checkpoint(height=134444,
                   hash=chainhash.Hash("00000000000005b12ffd4cd315cd34ffd4a594f430ac814c91184a0d42d2b0fe")),
        Checkpoint(height=168000,
                   hash=chainhash.Hash("000000000000099e61ea72015e79632f216fe6cb33d7899acb35b75c8303b763")),
        Checkpoint(height=193000,
                   hash=chainhash.Hash("000000000000059f452a5f7340de6682a977387c17010ff6e6c3bd83ca8b1317")),
        Checkpoint(height=210000,
                   hash=chainhash.Hash("000000000000048b95347e83192f69cf0366076336c639f9b7228e9ba171342e")),
        Checkpoint(height=216116,
                   hash=chainhash.Hash("00000000000001b4f4b433e81ee46494af945cf96014816a4e2370f11b23df4e")),
        Checkpoint(height=225430,
                   hash=chainhash.Hash("00000000000001c108384350f74090433e7fcf79a606b8e797f065b130575932")),
        Checkpoint(height=250000,
                   hash=chainhash.Hash("000000000000003887df1f29024b06fc2200b55f8af8f35453d7be294df2d214")),
        Checkpoint(height=267300,
                   hash=chainhash.Hash("000000000000000a83fbd660e918f218bf37edd92b748ad940483c7c116179ac")),
        Checkpoint(height=279000,
                   hash=chainhash.Hash("0000000000000001ae8c72a0b0c301f67e3afca10e819efa9041e458e9bd7e40")),
        Checkpoint(height=300255,
                   hash=chainhash.Hash("0000000000000000162804527c6e9b9f0563a280525f9d08c12041def0a0f3b2")),
        Checkpoint(height=319400,
                   hash=chainhash.Hash("000000000000000021c6052e9becade189495d1c539aa37c58917305fd15f13b")),
        Checkpoint(height=343185,
                   hash=chainhash.Hash("0000000000000000072b8bf361d01a6ba7d445dd024203fafc78768ed4368554")),
        Checkpoint(height=352940,
                   hash=chainhash.Hash("000000000000000010755df42dba556bb72be6a32f3ce0b6941ce4430152c9ff")),
        Checkpoint(height=382320,
                   hash=chainhash.Hash("00000000000000000a8dc6ed5b133d0eb2fd6af56203e4159789b092defd8ab2")),

    ],

    # Consensus rule change deployments.
    #
    # The miner confirmation window is defined as:
    #   target proof of work timespan / target proof of work spacing
    rule_change_activation_threshold=1916,  # 95% of MinerConfirmationWindow
    miner_confirmation_window=2016,
    deployments=[
        # DeploymentTestDummy
        ConsensusDeployment(
            bit_number=28,
            start_time=1199145601,  # January 1, 2008 UTC
            expire_time=1230767999,  # December 31, 2008 UTC
        ),

        # DeploymentCSV
        ConsensusDeployment(
            bit_number=0,
            start_time=1462060800,  # May 1st, 2016
            expire_time=1493596800,  # May 1st, 2017
        ),

        # DeploymentSegwit
        ConsensusDeployment(
            bit_number=1,
            start_time=1479168000,  # November 15, 2016 UTC
            expire_time=1510704000,  # November 15, 2017 UTC.
        ),
    ],

    # Mempool parameters
    relay_non_std_txs=False,

    # Human-readable part for Bech32 encoded segwit addresses, as defined in
    # BIP 173.
    bech32_hrp_segwit="bc",  # always bc for main net

    # Address encoding magics
    pub_key_hash_addr_id=0x00,  # starts with 1
    script_hash_addr_id=0x05,  # starts with 3
    private_key_id=0x80,  # starts with 5 (uncompressed) or K (compressed)
    witness_pub_key_hash_addr_id=0x06,  # starts with p2
    witness_script_hash_addr_id=0x0A,  # starts with 7Xh

    # BIP32 hierarchical deterministic extended key magics
    hd_private_key_id=bytes([0x04, 0x88, 0xad, 0xe4]),  # starts with xprv
    hd_public_key_id=bytes([0x04, 0x88, 0xb2, 0x1e]),  # starts with xpub

    # BIP44 coin type used in the hierarchical deterministic path for
    # address generation.
    hd_coin_type=0
)

# RegressionNetParams defines the network parameters for the regression test
# Bitcoin network.  Not to be confused with the test Bitcoin network (version
# 3), this network is sometimes simply called "testnet".
RegressionNetParams = Params(
    name="regtest",
    net=wire.BitcoinNet.TestNet,
    default_port="18444",
    dns_seeds=[],

    # Chain parameters
    genesis_block=regTestGenesisBlock,
    genesis_hash=regTestGenesisHash,
    pow_limit=regressionPowLimit,
    pow_limit_bits=0x207fffff,
    bip0034_height=100000000,  # Not active - Permit ver 1 blocks
    bip0065_height=1351,  # Used by regression tests
    bip0066_height=1251,  # Used by regression tests
    coinbase_maturity=100,
    subsidy_reduction_interval=210000,
    target_timespan=3600 * 24 * 14,  # 14 days
    target_time_per_block=60 * 10,  # 10minutes
    retarget_adjustment_factor=4,  # 25% less, 400% more
    reduce_min_difficulty=True,
    min_diff_reduction_time=60 * 20,  # TargetTimePerBlock * 2
    generate_supported=True,

    # Checkpoints ordered from oldest to newest.
    checkpoints=[],

    # Consensus rule change deployments.
    #
    # The miner confirmation window is defined as:
    #   target proof of work timespan / target proof of work spacing
    rule_change_activation_threshold=108,  # 75%  of MinerConfirmationWindow
    miner_confirmation_window=144,
    deployments=[
        # DeploymentTestDummy
        ConsensusDeployment(
            bit_number=28,
            start_time=0,  # Always available for vote
            expire_time=MaxInt64,  # Never expires
        ),

        # DeploymentCSV
        ConsensusDeployment(
            bit_number=0,
            start_time=0,  # Always available for vote
            expire_time=MaxInt64,  # Never expires.
        ),

        # DeploymentSegwit
        ConsensusDeployment(
            bit_number=1,
            start_time=0,  # Always available for vote
            expire_time=MaxInt64,  # Never expires.
        ),
    ],

    # Mempool parameters
    relay_non_std_txs=True,

    # Human-readable part for Bech32 encoded segwit addresses, as defined in
    # BIP 173.
    bech32_hrp_segwit="bcrt",  # always bcrt for reg test net

    # Address encoding magics
    pub_key_hash_addr_id=0x6f,  # starts with m or n
    script_hash_addr_id=0xc4,  # starts with 2
    private_key_id=0xef,  # starts with 9 (uncompressed) or c (compressed)

    # witness_pub_key_hash_addr_id=0x06,  # starts with p2
    # witness_script_hash_addr_id=0x0A,  # starts with 7Xh

    # BIP32 hierarchical deterministic extended key magics
    hd_private_key_id=bytes([0x04, 0x35, 0x83, 0x94]),  # starts with tprv
    hd_public_key_id=bytes([0x04, 0x35, 0x87, 0xcf]),  # starts with tpub

    # BIP44 coin type used in the hierarchical deterministic path for
    # address generation.
    hd_coin_type=1
)

# TestNet3Params defines the network parameters for the test Bitcoin network
# (version 3).  Not to be confused with the regression test network, this
# network is sometimes simply called "testnet".
TestNet3Params = Params(
    name="testnet3",
    net=wire.BitcoinNet.TestNet3,
    default_port="18333",
    dns_seeds=[
        DNSSeed(host="testnet-seed.bitcoin.jonasschnelli.ch", has_filtering=True),
        DNSSeed(host="testnet-seed.bitcoin.schildbach.de", has_filtering=False),
        DNSSeed(host="seed.tbtc.petertodd.org", has_filtering=True),
        DNSSeed(host="testnet-seed.bluematt.me", has_filtering=False),
    ],

    # Chain parameters
    genesis_block=testNet3GenesisBlock,
    genesis_hash=testNet3GenesisHash,
    pow_limit=testNet3PowLimit,
    pow_limit_bits=0x1d00ffff,
    bip0034_height=21111,  # 0000000023b3a96d3484e5abb3755c413e7d41500f8e2a5c3f0dd01299cd8ef8
    bip0065_height=581885,  # 00000000007f6655f22f98e72ed80d8b06dc761d5da09df0fa1dc4be4f861eb6
    bip0066_height=330776,  # 000000002104c8c45e99a8853285a3b592602a3ccde2b832481da85e9e4ba182
    coinbase_maturity=100,
    subsidy_reduction_interval=210000,
    target_timespan=3600 * 24 * 14,  # 14 days
    target_time_per_block=60 * 10,  # 10minutes
    retarget_adjustment_factor=4,  # 25% less, 400% more
    reduce_min_difficulty=True,
    min_diff_reduction_time=60 * 20,  # TargetTimePerBlock * 2
    generate_supported=False,

    # Checkpoints ordered from oldest to newest.
    checkpoints=[
        Checkpoint(height=546, hash=chainhash.Hash("000000002a936ca763904c3c35fce2f3556c559c0214345d31b1bcebf76acb70")),
        Checkpoint(height=100000,
                   hash=chainhash.Hash("00000000009e2958c15ff9290d571bf9459e93b19765c6801ddeccadbb160a1e")),
        Checkpoint(height=200000,
                   hash=chainhash.Hash("0000000000287bffd321963ef05feab753ebe274e1d78b2fd4e2bfe9ad3aa6f2")),
        Checkpoint(height=300001,
                   hash=chainhash.Hash("0000000000004829474748f3d1bc8fcf893c88be255e6d7f571c548aff57abf4")),
        Checkpoint(height=400002,
                   hash=chainhash.Hash("0000000005e2c73b8ecb82ae2dbc2e8274614ebad7172b53528aba7501f5a089")),
        Checkpoint(height=500011,
                   hash=chainhash.Hash("00000000000929f63977fbac92ff570a9bd9e7715401ee96f2848f7b07750b02")),
        Checkpoint(height=600002,
                   hash=chainhash.Hash("000000000001f471389afd6ee94dcace5ccc44adc18e8bff402443f034b07240")),
        Checkpoint(height=700000,
                   hash=chainhash.Hash("000000000000406178b12a4dea3b27e13b3c4fe4510994fd667d7c1e6a3f4dc1")),
        Checkpoint(height=800010,
                   hash=chainhash.Hash("000000000017ed35296433190b6829db01e657d80631d43f5983fa403bfdb4c1")),
        Checkpoint(height=900000,
                   hash=chainhash.Hash("0000000000356f8d8924556e765b7a94aaebc6b5c8685dcfa2b1ee8b41acd89b")),
        Checkpoint(height=1000007,
                   hash=chainhash.Hash("00000000001ccb893d8a1f25b70ad173ce955e5f50124261bbbc50379a612ddf")),
    ],

    # Consensus rule change deployments.
    #
    # The miner confirmation window is defined as:
    #   target proof of work timespan / target proof of work spacing
    rule_change_activation_threshold=1512,  # 75% of MinerConfirmationWindow
    miner_confirmation_window=2016,
    deployments=[
        # DeploymentTestDummy
        ConsensusDeployment(
            bit_number=28,
            start_time=1199145601,  # January 1, 2008 UTC
            expire_time=1230767999,  # December 31, 2008 UTC
        ),

        # DeploymentCSV
        ConsensusDeployment(
            bit_number=0,
            start_time=1462060800,  # May 1st, 2016
            expire_time=1493596800,  # May 1st, 2017
        ),

        # DeploymentSegwit
        ConsensusDeployment(
            bit_number=1,
            start_time=1479168000,  # November 15, 2016 UTC
            expire_time=1510704000,  # November 15, 2017 UTC.
        ),
    ],

    # Mempool parameters
    relay_non_std_txs=True,

    # Human-readable part for Bech32 encoded segwit addresses, as defined in
    # BIP 173.
    bech32_hrp_segwit="tb",  # always tb for test net

    # Address encoding magics
    pub_key_hash_addr_id=0x6f,  # starts with m or n
    script_hash_addr_id=0xc4,  # starts with 2
    private_key_id=0x03,  # starts with QW
    witness_pub_key_hash_addr_id=0x28,  # starts with T7n
    witness_script_hash_addr_id=0xef,  # starts with 9 (uncompressed) or c (compressed)

    # BIP32 hierarchical deterministic extended key magics
    hd_private_key_id=bytes([0x04, 0x35, 0x83, 0x94]),  # starts with tprv
    hd_public_key_id=bytes([0x04, 0x35, 0x87, 0xcf]),  # starts with tpub

    # BIP44 coin type used in the hierarchical deterministic path for
    # address generation.
    hd_coin_type=1
)

# SimNetParams defines the network parameters for the simulation test Bitcoin
# network.  This network is similar to the normal test network except it is
# intended for private use within a group of individuals doing simulation
# testing.  The functionality is intended to differ in that the only nodes
# which are specifically specified are used to create the network rather than
# following normal discovery rules.  This is important as otherwise it would
# just turn into another public testnet.
SimNetParams = Params(
    name="simnet",
    net=wire.BitcoinNet.SimNet,
    default_port="18555",
    dns_seeds=[],

    # Chain parameters
    genesis_block=simNetGenesisBlock,
    genesis_hash=simNetGenesisHash,
    pow_limit=simNetPowLimit,
    pow_limit_bits=0x207fffff,
    bip0034_height=0,  # Always active on simnet
    bip0065_height=0,  # Always active on simnet
    bip0066_height=0,  # Always active on simnet
    coinbase_maturity=100,
    subsidy_reduction_interval=210000,
    target_timespan=3600 * 24 * 14,  # 14 days
    target_time_per_block=60 * 10,  # 10minutes
    retarget_adjustment_factor=4,  # 25% less, 400% more
    reduce_min_difficulty=True,
    min_diff_reduction_time=60 * 20,  # TargetTimePerBlock * 2
    generate_supported=True,

    # Checkpoints ordered from oldest to newest.
    checkpoints=[],

    # Consensus rule change deployments.
    #
    # The miner confirmation window is defined as:
    #   target proof of work timespan / target proof of work spacing
    rule_change_activation_threshold=75,  # 75% of MinerConfirmationWindow
    miner_confirmation_window=100,
    deployments=[
        # DeploymentTestDummy
        ConsensusDeployment(
            bit_number=28,
            start_time=0,  # Always available for vote
            expire_time=MaxInt64,  # Never expires
        ),

        # DeploymentCSV
        ConsensusDeployment(
            bit_number=0,
            start_time=0,  # Always available for vote
            expire_time=MaxInt64,  # Never expires.
        ),

        # DeploymentSegwit
        ConsensusDeployment(
            bit_number=1,
            start_time=0,  # Always available for vote
            expire_time=MaxInt64,  # Never expires.
        ),
    ],

    # Mempool parameters
    relay_non_std_txs=True,

    # Human-readable part for Bech32 encoded segwit addresses, as defined in
    # BIP 173.
    bech32_hrp_segwit="sb",  # always tb for sim net

    # Address encoding magics
    pub_key_hash_addr_id=0x3f,  # starts with S
    script_hash_addr_id=0x7b,  # starts with s
    private_key_id=0x64,  # starts with 4 (uncompressed) or F (compressed)
    witness_pub_key_hash_addr_id=0x19,  # starts with Gg
    witness_script_hash_addr_id=0x28,  # starts with ?

    # BIP32 hierarchical deterministic extended key magics
    hd_private_key_id=bytes([0x04, 0x20, 0xb9, 0x00]),  # starts with sprv
    hd_public_key_id=bytes([0x04, 0x20, 0xbd, 0x3a]),  # starts with spub

    # BIP44 coin type used in the hierarchical deterministic path for
    # address generation.
    hd_coin_type=115  # ASCII for s
)


# ErrDuplicateNet describes an error where the parameters for a Bitcoin
# network could not be set due to the network already being a standard
# network or previously-registered into this package.
class ErrDuplicateNet(BaseException):
    def __init__(self, msg=None):
        self.msg = msg or "duplicate Bitcoin network"


# ErrUnknownHDKeyID describes an error where the provided id which
# is intended to identify the network for a hierarchical deterministic
# private extended key is not registered.
class ErrUnknownHDKeyID(BaseException):
    def __init__(self, msg=None):
        self.msg = msg or "unknown hd private extended key bytes"


#
registerNets = {}
pubKeyHashAddrIDs = {}
scriptHashAddrIDs = {}
bech32SegwitPrefixes = {}
hdPrivToPubKeyIDs = {}


# Register registers the network parameters for a Bitcoin network.  This may
# error with ErrDuplicateNet if the network is already registered (either
# due to a previous Register call, or the network being one of the default
# networks).
#
# Network parameters should be registered into this package by a main package
# as early as possible.  Then, library packages may lookup networks or network
# parameters based on inputs and work regardless of the network being standard
# or not.
def register(params: Params):
    if params.net in registerNets:
        raise ErrDuplicateNet

    registerNets[params.net] = True
    pubKeyHashAddrIDs[params.pub_key_hash_addr_id] = True
    scriptHashAddrIDs[params.script_hash_addr_id] = True
    hdPrivToPubKeyIDs[params.hd_private_key_id] = params.hd_public_key_id

    # A valid Bech32 encoded segwit address always has as prefix the
    # human-readable part for the given net followed by '1'.
    bech32SegwitPrefixes[params.bech32_hrp_segwit + "1"] = True
    return


# mustRegister performs the same function as Register except it panics if there
# is an error.  This should only be called from package init functions.
def must_register(params: Params):
    register(params)


# IsPubKeyHashAddrID returns whether the id is an identifier known to prefix a
# pay-to-pubkey-hash address on any default or registered network.  This is
# used when decoding an address string into a specific address type.  It is up
# to the caller to check both this and IsScriptHashAddrID and decide whether an
# address is a pubkey hash address, script hash address, neither, or
# undeterminable (if both return true).
def is_pub_key_hash_addr_id(id)->bool:
    return id in pubKeyHashAddrIDs

# IsScriptHashAddrID returns whether the id is an identifier known to prefix a
# pay-to-script-hash address on any default or registered network.  This is
# used when decoding an address string into a specific address type.  It is up
# to the caller to check both this and IsPubKeyHashAddrID and decide whether an
# address is a pubkey hash address, script hash address, neither, or
# undeterminable (if both return true).
def is_script_hash_addr_id(id)->bool:
    return id in scriptHashAddrIDs

# IsBech32SegwitPrefix returns whether the prefix is a known prefix for segwit
# addresses on any default or registered network.  This is used when decoding
# an address string into a specific address type.
def is_bech32_segwit_prefix(prefix) -> bool:
    prefix = prefix.lower()
    return prefix in bech32SegwitPrefixes


# HDPrivateKeyToPublicKeyID accepts a private hierarchical deterministic
# extended key id and returns the associated public key id.  When the provided
# id is not registered, the ErrUnknownHDKeyID error will be returned.
def hd_private_key_to_public_key_id(id):
    if len(id) != 4:
        raise ErrUnknownHDKeyID

    if id in hdPrivToPubKeyIDs:
        return hdPrivToPubKeyIDs[id]
    else:
        raise ErrUnknownHDKeyID










