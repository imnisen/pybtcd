# Not pythonic now
# I don't know whether these class is useful now
# just make them, then check.


class GetBlockHeaderVerboseResult:
    def __init__(self, hash, confirmations, height, version, version_hex,
                 merkle_root, time, nonce, bits, difficulty, previous_hash, next_hash):
        self.hash = hash
        self.confirmations = confirmations
        self.height = height
        self.version = version
        self.version_hex = version_hex
        self.merkle_root = merkle_root
        self.time = time
        self.nonce = nonce
        self.bits = bits
        self.difficulty = difficulty
        self.previous_hash = previous_hash
        self.next_hash = next_hash


class GetBlockVerboseResult:
    def __init__(self, hash, confirmations, height, version, version_hex,
                 merkle_root, time, nonce, bits, difficulty, previous_hash, next_hash):
        self.hash = hash
        self.confirmations = confirmations
        self.height = height
        self.version = version
        self.version_hex = version_hex
        self.merkle_root = merkle_root
        self.time = time
        self.nonce = nonce
        self.bits = bits
        self.difficulty = difficulty
        self.previous_hash = previous_hash
        self.next_hash = next_hash


class CreateMultiSigResult:
    def __init__(self, address, redeem_script):
        self.address = address
        self.redeem_script = redeem_script


class DecodeScriptResult:
    def __init__(self, asm, req_sigs, type, addresses, p2sh):
        self.asm = asm
        self.req_sigs = req_sigs
        self.type = type
        self.addresses = addresses
        self.p2sh = p2sh


class GetAddedNodeInfoResultAddr:
    def __init__(self, address, connected):
        self.address = address
        self.connected = connected


class GetAddedNodeInfoResult:
    def __init__(self, added_node, connected, addresses):
        self.added_node = added_node
        self.connected = connected
        self.addresses = addresses


class GetBlockChainInfoResult:
    def __init__(self, chain, blocks, headers, best_block_hash, difficulty,
                 median_time, verification_progress, pruned, pruned_height, chain_work,
                 soft_forks, bip9_soft_forks):
        self.chain = chain
        self.blocks = blocks
        self.headers = headers
        self.best_block_hash = best_block_hash
        self.difficulty = difficulty
        self.median_time = median_time
        self.verification_progress = verification_progress
        self.pruned = pruned
        self.pruned_height = pruned_height
        self.chain_work = chain_work
        self.soft_forks = soft_forks
        self.bip9_soft_forks = bip9_soft_forks


class GetBlockTemplateResultTx:
    def __init__(self, data, hash, depends, fee, sig_ops, weight):
        self.data = data
        self.hash = hash
        self.depends = depends
        self.fee = fee
        self.weight = sig_ops
        self.depends = weight


class GetBlockTemplateResult:
    def __init__(self, data, hash, depends, fee, sig_ops, weight):
        self.data = data


class GetMempoolEntryResult:
    def __init__(self, size, fee, modified_fee, time, height, starting_priority, current_priority, descendant_count,
                 descendant_size, descendant_fees, ancestor_count, ancestor_size, ancestor_fees, depends):
        self.size = size
        self.fee = fee
        self.modified_fee = modified_fee
        self.time = time
        self.height = height
        self.starting_priority = starting_priority
        self.current_priority = current_priority
        self.descendant_count = descendant_count
        self.descendant_size = descendant_size
        self.descendant_fees = descendant_fees
        self.ancestor_count = ancestor_count
        self.ancestor_size = ancestor_size
        self.ancestor_fees = ancestor_fees
        self.depends = depends


class GetMempoolInfoResult:
    def __init__(self, size, bytes):
        self.size = size
        self.bytes = bytes


class NetworksResult:
    def __init__(self, name, limited, reachable, proxy, proxy_randomize_credentials):
        self.name = name
        self.limited = limited
        self.reachable = reachable
        self.proxy = proxy
        self.proxy_randomize_credentials = proxy_randomize_credentials


class LocalAddressesResult:
    def __init__(self, address, port, score):
        self.address = address
        self.port = port
        self.score = score


class GetNetworkInfoResult:
    def __init__(self, version, sub_version, protocol_version, local_services, local_relay, time_offset, connections,
                 network_active, networks, relay_fee, incremental_fee, local_addresses, warnings):
        self.version = version
        self.sub_version = sub_version
        self.protocol_version = protocol_version
        self.local_services = local_services
        self.local_relay = local_relay
        self.time_offset = time_offset
        self.connections = connections
        self.network_active = network_active
        self.networks = networks
        self.relay_fee = relay_fee
        self.incremental_fee = incremental_fee
        self.local_addresses = local_addresses
        self.warnings = warnings


class GetPeerInfoResult:
    def __init__(self, i_d, addr, addr_local, services, relay_txes, last_send, last_recv, bytes_sent, bytes_recv,
                 conn_time, time_offset, ping_time, ping_wait, version, sub_ver, inbound, starting_height,
                 current_height, ban_score, fee_filter, sync_node):
        self.i_d = i_d
        self.addr = addr
        self.addr_local = addr_local
        self.services = services
        self.relay_txes = relay_txes
        self.last_send = last_send
        self.last_recv = last_recv
        self.bytes_sent = bytes_sent
        self.bytes_recv = bytes_recv
        self.conn_time = conn_time
        self.time_offset = time_offset
        self.ping_time = ping_time
        self.ping_wait = ping_wait
        self.version = version
        self.sub_ver = sub_ver
        self.inbound = inbound
        self.starting_height = starting_height
        self.current_height = current_height
        self.ban_score = ban_score
        self.fee_filter = fee_filter
        self.sync_node = sync_node


class GetRawMempoolVerboseResult:
    def __init__(self, size, vsize, fee, time, height, starting_priority, current_priority, depends):
        self.size = size
        self.vsize = vsize
        self.fee = fee
        self.time = time
        self.height = height
        self.starting_priority = starting_priority
        self.current_priority = current_priority
        self.depends = depends


class ScriptPubKeyResult:
    def __init__(self, asm, hex, req_sigs, type, addresses):
        self.asm = asm
        self.hex = hex
        self.req_sigs = req_sigs
        self.type = type
        self.addresses = addresses


class GetTxOutResult:
    def __init__(self, best_block, confirmations, value, script_pub_key, coinbase):
        self.best_block = best_block
        self.confirmations = confirmations
        self.value = value
        self.script_pub_key = script_pub_key
        self.coinbase = coinbase


class GetNetTotalsResult:
    def __init__(self, total_bytes_recv, total_bytes_sent, time_millis):
        self.total_bytes_recv = total_bytes_recv
        self.total_bytes_sent = total_bytes_sent
        self.time_millis = time_millis


class ScriptSig:
    def __init__(self, asm, hex):
        self.asm = asm
        self.hex = hex


class Vin:
    def __init__(self, coinbase, txid, vout, script_sig, sequence, witness):
        self.coinbase = coinbase
        self.txid = txid
        self.vout = vout
        self.script_sig = script_sig
        self.sequence = sequence
        self.witness = witness


class PrevOut:
    def __init__(self, addresses, value):
        self.addresses = addresses
        self.value = value


class VinPrevOut:
    def __init__(self, coinbase, txid, vout, script_sig, witness, prev_out, sequence):
        self.coinbase = coinbase
        self.txid = txid
        self.vout = vout
        self.script_sig = script_sig
        self.witness = witness
        self.prev_out = prev_out
        self.sequence = sequence


class Vout:
    def __init__(self, value, n, script_pub_key):
        self.value = value
        self.n = n
        self.script_pub_key = script_pub_key


class GetMiningInfoResult:
    def __init__(self, blocks, current_block_size, current_block_weight, current_block_tx, difficulty, errors, generate,
                 gen_proc_limit, hashes_per_sec, network_hash_p_s, pooled_tx, test_net):
        self.blocks = blocks
        self.current_block_size = current_block_size
        self.current_block_weight = current_block_weight
        self.current_block_tx = current_block_tx
        self.difficulty = difficulty
        self.errors = errors
        self.generate = generate
        self.gen_proc_limit = gen_proc_limit
        self.hashes_per_sec = hashes_per_sec
        self.network_hash_p_s = network_hash_p_s
        self.pooled_tx = pooled_tx
        self.test_net = test_net


class GetWorkResult:
    def __init__(self, data, hash1, midstate, target):
        self.data = data
        self.hash1 = hash1
        self.midstate = midstate
        self.target = target


class InfoChainResult:
    def __init__(self, version, protocol_version, blocks, time_offset, connections, proxy, difficulty, test_net,
                 relay_fee, errors):
        self.version = version
        self.protocol_version = protocol_version
        self.blocks = blocks
        self.time_offset = time_offset
        self.connections = connections
        self.proxy = proxy
        self.difficulty = difficulty
        self.test_net = test_net
        self.relay_fee = relay_fee
        self.errors = errors


class TxRawResult:
    def __init__(self, hex, txid, hash, size, vsize, version, lock_time, vin, vout, block_hash, confirmations, time,
                 blocktime):
        self.hex = hex
        self.txid = txid
        self.hash = hash
        self.size = size
        self.vsize = vsize
        self.version = version
        self.lock_time = lock_time
        self.vin = vin
        self.vout = vout
        self.block_hash = block_hash
        self.confirmations = confirmations
        self.time = time
        self.blocktime = blocktime


class SearchRawTransactionsResult:
    def __init__(self, hex, txid, hash, size, vsize, version, lock_time, vin, vout, block_hash, confirmations, time,
                 blocktime):
        self.hex = hex
        self.txid = txid
        self.hash = hash
        self.size = size
        self.vsize = vsize
        self.version = version
        self.lock_time = lock_time
        self.vin = vin
        self.vout = vout
        self.block_hash = block_hash
        self.confirmations = confirmations
        self.time = time
        self.blocktime = blocktime


class TxRawDecodeResult:
    def __init__(self, txid, version, locktime, vin, vout):
        self.txid = txid
        self.version = version
        self.locktime = locktime
        self.vin = vin
        self.vout = vout


class ValidateAddressChainResult:
    def __init__(self, is_valid, address):
        self.is_valid = is_valid
        self.address = address
