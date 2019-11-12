import wire


# AddNodeSubCmd defines the type used in the addnode JSON-RPC command for the
# sub command field.
class AddNodeSubCmd(str):
    pass


# AddNodeCmd defines the addnode JSON-RPC command.
class AddNodeCmd:
    def __init__(self, addr: str, sub_cmd: AddNodeSubCmd):
        self.addr = addr
        self.sub_cmd = sub_cmd


# TransactionInput represents the inputs to a transaction.  Specifically a
# transaction hash and output number pair.
class TransactionInput:
    def __init__(self, txid: str, vout: int):
        self.txid = txid
        self.vout = vout  # uint32


# CreateRawTransactionCmd defines the createrawtransaction JSON-RPC command.
class CreateRawTransactionCmd:
    def __init__(self, inputs: [TransactionInput], amounts: dict, lock_time: int):
        self.inputs = inputs
        self.amounts = amounts
        self.lock_time = lock_time


# DecodeRawTransactionCmd defines the decoderawtransaction JSON-RPC command.
class DecodeRawTransactionCmd:
    def __init__(self, hex_tx: str):
        self.hex_tx = hex_tx


# DecodeScriptCmd defines the decodescript JSON-RPC command.
class DecodeScriptCmd:
    def __init__(self, hex_tx: str):
        self.hex_tx = hex_tx


# GetAddedNodeInfoCmd defines the getaddednodeinfo JSON-RPC command.
class GetAddedNodeInfoCmd:
    def __init__(self, dns: bool, node: str):
        self.dns = dns
        self.node = node


# GetBestBlockHashCmd defines the getbestblockhash JSON-RPC command.
class GetBestBlockHashCmd:
    pass


# GetBlockCmd defines the getblock JSON-RPC command.
class GetBlockCmd:
    def __init__(self, hash: str, verbose: bool, verbose_tx: bool):
        self.hash = hash
        self.verbose = verbose
        self.verbose_tx = verbose_tx


# GetBlockChainInfoCmd defines the getblockchaininfo JSON-RPC command.
class GetBlockChainInfoCmd:
    pass


# GetBlockCountCmd defines the getblockcount JSON-RPC command.
class GetBlockCountCmd:
    pass


# GetBlockHashCmd defines the getblockhash JSON-RPC command.
class GetBlockHashCmd:
    def __init__(self, index: int):
        self.index = index


# GetBlockHeaderCmd defines the getblockheader JSON-RPC command.
class GetBlockHeaderCmd:
    def __init__(self, hash: str, verbose: bool):
        self.hash = hash
        self.verbose = verbose


# TemplateRequest is a request object as defined in BIP22
# (https:#en.bitcoin.it/wiki/BIP_0022), it is optionally provided as an
# pointer argument to GetBlockTemplateCmd.
class TemplateRequest:
    def __init__(self, mode: str, capabilities: [str],
                 long_pool_id: str,
                 sig_op_limit, size_limit, max_version: int,
                 target: str,
                 data: str, work_id: str):
        self.mode = mode
        self.capabilities = capabilities

        # Optional long polling.
        self.long_pool_id = long_pool_id

        # Optional template tweaking.  SigOpLimit and SizeLimit can be int64
        # or bool.
        self.sig_op_limit = sig_op_limit
        self.size_limit = size_limit
        self.max_version = max_version

        # Basic pool extension from BIP 0023.
        self.target = target

        # Block proposal from BIP 0023.  Data is only provided when Mode is
        # "proposal".
        self.data = data
        self.work_id = work_id


# GetBlockTemplateCmd defines the getblocktemplate JSON-RPC command.
class GetBlockTemplateCmd:
    def __init__(self, request: TemplateRequest):
        self.request = request


# GetCFilterCmd defines the getcfilter JSON-RPC command.
class GetCFilterCmd:
    def __init__(self, hash: str, filter_type: wire.FilterType):
        self.hash = hash
        self.filter_type = filter_type


# GetCFilterHeaderCmd defines the getcfilterheader JSON-RPC command.
class GetCFilterHeaderCmd:
    def __init__(self, hash: str, filter_type: wire.FilterType):
        self.hash = hash
        self.filter_type = filter_type


# GetChainTipsCmd defines the getchaintips JSON-RPC command.
class GetChainTipsCmd:
    pass


# GetConnectionCountCmd defines the getchaintips JSON-RPC command.
class GetConnectionCountCmd:
    pass


# GetDifficultyCmd defines the getchaintips JSON-RPC command.
class GetDifficultyCmd:
    pass


# GetGenerateCmd defines the getchaintips JSON-RPC command.
class GetGenerateCmd:
    pass


# GetHashesPerSecCmd defines the gethashespersec JSON-RPC command.
class GetHashesPerSecCmd:
    pass


# GetInfoCmd defines the getinfo JSON-RPC command.
class GetInfoCmd:
    pass


# GetMempoolEntryCmd defines the getmempoolentry JSON-RPC command.
class GetMempoolEntryCmd:
    def __init__(self, tx_id: str):
        self.tx_id = tx_id


# GetMempoolInfoCmd defines the getmempoolinfo JSON-RPC command.
class GetMempoolInfoCmd:
    pass


# GetMiningInfoCmd defines the getmininginfo JSON-RPC command.
class GetMiningInfoCmd:
    pass


# GetNetworkInfoCmd defines the getnetworkinfo JSON-RPC command.
class GetNetworkInfoCmd:
    pass


# GetNetTotalsCmd defines the getnettotals JSON-RPC command.
class GetNetTotalsCmd:
    pass


# GetNetworkHashPSCmd defines the getnetworkhashps JSON-RPC command.
class GetNetworkHashPSCmd:
    def __init__(self, blocks: int, height: int):
        self.blocks = blocks
        self.height = height


# GetPeerInfoCmd defines the getpeerinfo JSON-RPC command.
class GetPeerInfoCmd:
    pass


# GetRawMempoolCmd defines the getmempool JSON-RPC command.
class GetRawMempoolCmd:
    def __init__(self, verbose: bool):
        self.verbose = verbose


# GetRawTransactionCmd defines the getrawtransaction JSON-RPC command.
#
# NOTE: This field is an int versus a bool to remain compatible with Bitcoin
# Core even though it really should be a bool.
class GetRawTransactionCmd:
    def __init__(self, txid: str, verbose: int):
        self.txid = txid
        self.verbose = verbose


# GetTxOutCmd defines the gettxout JSON-RPC command.
class GetTxOutCmd:
    def __init__(self, txid: str, vout: int, include_mempool: bool):
        self.txid = txid
        self.vout = vout
        self.include_mempool = include_mempool


# GetTxOutProofCmd defines the gettxoutproof JSON-RPC command.
class GetTxOutProofCmd:
    def __init__(self, tx_ids: [str], block_hash: str):
        self.tx_ids = tx_ids
        self.block_hash = block_hash


# GetTxOutSetInfoCmd defines the gettxoutsetinfo JSON-RPC command.
class GetTxOutSetInfoCmd:
    pass


# GetWorkCmd defines the getwork JSON-RPC command.
class GetWorkCmd:
    pass


# HelpCmd defines the help JSON-RPC command.
class HelpCmd:
    def __init__(self, command: str):
        self.command = command


# InvalidateBlockCmd defines the invalidateblock JSON-RPC command.
class InvalidateBlockCmd:
    def __init__(self, block_hash: str):
        self.block_hash = block_hash


# PingCmd defines the ping JSON-RPC command.
class PingCmd:
    pass


# PreciousBlockCmd defines the preciousblock JSON-RPC command.
class PreciousBlockCmd:
    def __init__(self, block_hash: str):
        self.block_hash = block_hash


# ReconsiderBlockCmd defines the reconsiderblock JSON-RPC command.
class ReconsiderBlockCmd:
    def __init__(self, block_hash: str):
        self.block_hash = block_hash


# SearchRawTransactionsCmd defines the searchrawtransactions JSON-RPC command.
class SearchRawTransactionsCmd:
    def __init__(self, address: str, verbose: int, skip: int, count: int,
                 vin_extra: int, reverse: bool, filter_addrs: [str]):
        self.address = address
        self.verbose = verbose
        self.skip = skip
        self.count = count
        self.vin_extra = vin_extra
        self.reverse = reverse
        self.filter_addrs = filter_addrs


# SendRawTransactionCmd defines the sendrawtransaction JSON-RPC command.
class SendRawTransactionCmd:
    def __init__(self, hex_tx: str, allow_high_fees: bool):
        self.hex_tx = hex_tx
        self.allow_high_fees = allow_high_fees


# SetGenerateCmd defines the setgenerate JSON-RPC command.
class SetGenerateCmd:
    def __init__(self, generate: bool, gen_proc_limit: int):
        self.generate = generate
        self.gen_proc_limit = gen_proc_limit


# StopCmd defines the stop JSON-RPC command.
class StopCmd:
    pass


# SubmitBlockOptions represents the optional options struct provided with a
# SubmitBlockCmd command.
class SubmitBlockOptions:
    def __init__(self, work_id: str):
        self.work_id = work_id


# SubmitBlockCmd defines the submitblock JSON-RPC command.
class SubmitBlockCmd:
    def __init__(self, hex_block: str, options: SubmitBlockOptions):
        self.hex_block = hex_block
        self.options = options


# UptimeCmd defines the uptime JSON-RPC command.
class UptimeCmd:
    pass


# ValidateAddressCmd defines the validateaddress JSON-RPC command.
class ValidateAddressCmd:
    def __init__(self, address: str):
        self.address = address


# VerifyChainCmd defines the verifychain JSON-RPC command.
class VerifyChainCmd:
    def __init__(self, check_level: int, check_depth: int):
        self.check_level = check_level
        self.check_depth = check_depth


# VerifyMessageCmd defines the verifymessage JSON-RPC command.
class VerifyMessageCmd:
    def __init__(self, address: str, signature: str, message: str):
        self.address = address
        self.signature = signature
        self.message = message


# VerifyTxOutProofCmd defines the verifytxoutproof JSON-RPC command.
class VerifyTxOutProofCmd:
    def __init__(self, proof: str):
        self.proof = proof
