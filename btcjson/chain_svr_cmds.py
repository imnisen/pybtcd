import collections
from .utils import *


# AddNodeSubCmd defines the type used in the addnode JSON-RPC command for the
# sub command field.
class AddNodeSubCmd(str):
    pass


# ANAdd indicates the specified host should be added as a persistent
# peer.
ANAdd = AddNodeSubCmd("add")

# ANRemove indicates the specified peer should be removed.
ANRemove = AddNodeSubCmd("remove")

# ANOneTry indicates the specified host should try to connect once,
# but it should not be made persistent.
ANOneTry = AddNodeSubCmd("onetry")


# AddNodeCmd defines the addnode JSON-RPC command.
@register_name("addnode")
class AddNodeCmd:
    def __init__(self, addr: str, sub_cmd: AddNodeSubCmd):
        self.addr = addr
        self.sub_cmd = sub_cmd

    def marshal_json(self):
        return [self.addr, str(self.sub_cmd)]

    @classmethod
    def from_params(cls, params):
        # check length is 2
        require_length(params, 2, "addnode params length should be 2")

        # check the first param string
        require_type(params[0], str, "addr should be str")
        addr = params[0]

        # check the second param string
        require_type(params[1], str, "sub command should be str")
        sub_cmd = AddNodeSubCmd(params[1])

        # check the second param one of avaiable options
        return cls(addr, sub_cmd)

    def __eq__(self, other):
        if isinstance(other, AddNodeCmd):
            return self.addr == other.addr and str(self.sub_cmd) == str(other.sub_cmd)
        return False


# TransactionInput represents the inputs to a transaction.  Specifically a
# transaction hash and output number pair.
class TransactionInput:
    def __init__(self, txid: str, vout: int):
        self.txid = txid
        self.vout = vout  # uint32

    def to_params(self):
        return collections.OrderedDict(txid=self.txid, vout=self.vout)

    def __eq__(self, other):
        if not isinstance(other, TransactionInput):
            return False

        return self.txid == other.txid and self.vout == other.vout

    @classmethod
    def from_params(cls, params):
        # check params is a dict
        require_type(params, dict, "transction input should be dict")

        if "txid" not in params:
            raise Exception("transaction input should have 'txid' key")

        require_type(params["txid"], str, "txid should be str")
        txidx = params["txid"]

        if "vout" not in params:
            raise Exception("transaction input should have 'vout' key")
        require_type(params["vout"], int, "vout should be int")
        vout = params["vout"]

        return cls(txid=txidx, vout=vout)


# CreateRawTransactionCmd defines the createrawtransaction JSON-RPC command.
@register_name("createrawtransaction")
class CreateRawTransactionCmd:
    def __init__(self, inputs: [TransactionInput], amounts: dict, lock_time: int or None = None):
        self.inputs = inputs
        self.amounts = amounts
        self.lock_time = lock_time

    def to_params(self):
        res = [[i.to_params() for i in self.inputs], self.amounts]
        if self.lock_time is not None:
            res.append(self.lock_time)
        return res

    @classmethod
    def from_params(cls, params):
        # length >=2
        require_length(params, [2, 3], "createrawtransaction params length should be [2,3]")

        # first is a list
        require_type(params[0], list, "transaction inputs should be list")
        inputs = [TransactionInput.from_params(each) for each in params[0]]

        # second is a dict
        require_type(params[1], dict, "amounts should be dict")
        amounts = params[1]

        # if have third param, it is a int64
        lock_time = None
        if len(params) > 2:
            require_type(params[2], int, "lock time should be int")
            lock_time = params[2]

        return cls(inputs, amounts, lock_time)

    def __eq__(self, other):
        if isinstance(other, CreateRawTransactionCmd):
            return list_equal(self.inputs, other.inputs) and \
                   dict_equal(self.amounts, other.amounts) and \
                   self.lock_time == other.lock_time

        return False


# DecodeRawTransactionCmd defines the decoderawtransaction JSON-RPC command.
@register_name("decoderawtransaction")
class DecodeRawTransactionCmd:
    def __init__(self, hex_tx: str):
        self.hex_tx = hex_tx

    def to_params(self):
        return [self.hex_tx]

    @classmethod
    def from_params(cls, params):
        require_length(params, 1, "decoderawtransaction should have 1 param")
        require_type(params[0], str, "hex tx should be str")
        hex_tx = params[0]
        return cls(hex_tx=hex_tx)

    def __eq__(self, other):
        if isinstance(other, DecodeRawTransactionCmd):
            return self.hex_tx == other.hex_tx

        return False


# DecodeScriptCmd defines the decodescript JSON-RPC command.
@register_name("decodescript")
class DecodeScriptCmd:
    def __init__(self, hex_script: str):
        self.hex_script = hex_script

    def to_params(self):
        return [self.hex_script]

    @classmethod
    def from_params(cls, params):
        require_length(params, 1, "decodescript should have 1 param")
        require_type(params[0], str, "hex tx should be str")
        hex_script = params[0]
        return cls(hex_script=hex_script)

    def __eq__(self, other):
        if isinstance(other, DecodeRawTransactionCmd):
            return self.hex_script == other.hex_script

        return False


# GetAddedNodeInfoCmd defines the getaddednodeinfo JSON-RPC command.
@register_name("getaddednodeinfo")
class GetAddedNodeInfoCmd:
    def __init__(self, dns: bool, node: str or None = None):
        self.dns = dns
        self.node = node

    def to_params(self):
        return [self.dns, self.node]

    @classmethod
    def from_params(cls, params):
        require_length(params, [1, 2], "getaddednodeinfo should have [1,2] params")
        require_type(params[0], bool, "dns should be str")
        dns = params[0]

        node = None
        if len(params) > 1:
            require_type(params[1], str, "node should be str")
            node = params[1]

        return cls(dns=dns, node=node)

    def __eq__(self, other):
        if isinstance(other, GetAddedNodeInfoCmd):
            return self.dns == other.dns and \
                   self.node == other.node

        return False


# GetBestBlockHashCmd defines the getbestblockhash JSON-RPC command.
@register_name("getbestblockhash")
class GetBestBlockHashCmd:
    def __init__(self):
        pass

    def to_params(self):
        return []

    @classmethod
    def from_params(cls, params):
        require_length(params, 0, "getbestblockhash should have 0 params")
        return cls()

    def __eq__(self, other):
        return isinstance(other, GetBestBlockHashCmd)



