import chainhash
import btcutil
import wire

# ---block_node constant---
# zeroHash is the zero value for a chainhash.Hash and is defined as
# a package level variable to avoid the need to create a new instance
# every time a check is needed.
zeroHash = chainhash.Hash()

# ----chainio Constant---
# blockHdrSize is the size of a block header.  This is simply the
# constant from wire and is only provided here for convenience since
# wire.MaxBlockHeaderPayload is quite long.
blockHdrSize = wire.MaxBlockHeaderPayload

# latestUtxoSetBucketVersion is the current version of the utxo set
# bucket that is used to track all unspent outputs.
latestUtxoSetBucketVersion = 2

# latestSpendJournalBucketVersion is the current version of the spend
# journal bucket that is used to track all spent transactions for use
# in reorgs.
latestSpendJournalBucketVersion = 1

# blockIndexBucketName is the name of the db bucket used to house to the
# block headers and contextual information.
blockIndexBucketName = b"blockheaderidx"

# hashIndexBucketName is the name of the db bucket used to house to the
# block hash -> block height index.
hashIndexBucketName = b"hashidx"

# heightIndexBucketName is the name of the db bucket used to house to
# the block height -> block hash index.
heightIndexBucketName = b"heightidx"

# chainStateKeyName is the name of the db key used to store the best
# chain state.
chainStateKeyName = b"chainstate"

# spendJournalVersionKeyName is the name of the db key used to store
# the version of the spend journal currently in the database.
spendJournalVersionKeyName = b"spendjournalversion"

# spendJournalBucketName is the name of the db bucket used to house
# transactions outputs that are spent in each block.
spendJournalBucketName = b"spendjournal"

# utxoSetVersionKeyName is the name of the db key used to store the
# version of the utxo set currently in the database.
utxoSetVersionKeyName = b"utxosetversion"

# utxoSetBucketName is the name of the db bucket used to house the
# unspent transaction output set.
utxoSetBucketName = b"utxosetv2"

# byteOrder is the preferred byte order used for serializing numeric
# fields for storage in the database.
byteOrder = "little"

# --- validate constant ---
# medianTimeBlocks is the number of previous blocks which should be
# used to calculate the median time used to validate block timestamps.
medianTimeBlocks = 11

# serializedHeightVersion is the block version which changed block
# coinbases to start with the serialized block height.
serializedHeightVersion = 2

# baseSubsidy is the starting subsidy amount for mined blocks.  This
# value is halved every SubsidyHalvingInterval blocks.
baseSubsidy = 50 * btcutil.SatoshiPerBitcoin

# MinCoinbaseScriptLen is the minimum length a coinbase script can be.
MinCoinbaseScriptLen = 2

# MaxCoinbaseScriptLen is the maximum length a coinbase script can be.
MaxCoinbaseScriptLen = 100

# MaxTimeOffsetSeconds is the maximum number of seconds a block time
# is allowed to be ahead of the current time.  This is currently 2
# hours.
MaxTimeOffsetSeconds = 2 * 60 * 60

# block91842Hash is one of the two nodes which violate the rules
# set forth in BIP0030.  It is defined as a package level variable to
# avoid the need to create a new instance every time a check is needed.
block91842Hash = chainhash.Hash("00000000000a4d0a398161ffc163c503763b1f4360639393e0e4c8e300e0caec")

# block91880Hash is one of the two nodes which violate the rules
# set forth in BIP0030.  It is defined as a package level variable to
# avoid the need to create a new instance every time a check is needed.
block91880Hash = chainhash.Hash("00000000000743f190a18c5577a3c2d2a1f610ae9601ac046a38084ccb7cd721")

# --- weight constant---
# MaxBlockWeight defines the maximum block weight, where "block
# weight" is interpreted as defined in BIP0141. A block's weight is
# calculated as the sum of the of bytes in the existing transactions
# and header, plus the weight of each byte within a transaction. The
# weight of a "base" byte is 4, while the weight of a witness byte is
# 1. As a result, for a block to be valid, the BlockWeight MUST be
# less than, or equal to MaxBlockWeight.
MaxBlockWeight = 4000000

# MaxBlockBaseSize is the maximum number of bytes within a block
# which can be allocated to non-witness data.
MaxBlockBaseSize = 1000000

# MaxBlockSigOpsCost is the maximum number of signature operations
# allowed for a block. It is calculated via a weighted algorithm which
# weights segregated witness sig ops lower than regular sig ops.
MaxBlockSigOpsCost = 80000

# WitnessScaleFactor determines the level of "discount" witness data
# receives compared to "base" data. A scale factor of 4, denotes that
# witness data is 1/4 as cheap as regular non-witness data.
WitnessScaleFactor = 4

# MinTxOutputWeight is the minimum possible weight for a transaction
# output.
MinTxOutputWeight = WitnessScaleFactor * wire.MinTxOutPayload

# MaxOutputsPerBlock is the maximum number of transaction outputs there
# can be in a block of max weight size.
MaxOutputsPerBlock = MaxBlockWeight // MinTxOutputWeight
