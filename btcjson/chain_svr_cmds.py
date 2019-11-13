import collections
import wire
from .utils import *


###
# These class should be generate by code, not by hand.
# However, I have tried to write the dsl before, to define the struct and handle the default case, which no success.
# when write in the class form, it becomes clear in semantic while verbose in syntax.
# The origin go struct work with some filed tag is a great demo of dsl.
# let's write these class first, then optimise them latter.
###

###
# TODO to_params and from_params methods are too similar. Let's try remove the duplicate code
# when we finish this file, let's do it
# Also it seems also need some customization mechanism.
###

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

    def to_params(self):
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
        if not isinstance(other, DecodeScriptCmd):
            return False
        return self.hex_script == other.hex_script


# GetAddedNodeInfoCmd defines the getaddednodeinfo JSON-RPC command.
@register_name("getaddednodeinfo")
class GetAddedNodeInfoCmd:
    def __init__(self, dns: bool, node: str or None = None):
        self.dns = dns
        self.node = node

    def to_params(self):
        if self.node:
            return [self.dns, self.node]
        return [self.dns]

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


###
# some notes of class definition
# 1. default value  =  None in `def __init__` is used when `GetBlockCmd()` can leave the param empty.
# if leave empty, set the default value. which should not be set like `self.verbose = verbose or None`,
# because `or` is not correct.
#
# 2.the jsonrpc default value should be set in the `to_params` and `from_params` methods.
# Because these two handles jsonserialize format and default. which should not be set in `__init__`.
#
###

# GetBlockCmd defines the getblock JSON-RPC command.
@register_name("getblock")
class GetBlockCmd:
    def __init__(self, hash: str, verbose: bool or None = None,
                 verbose_tx: bool or None = None):  # default value to None make the
        self.hash = hash
        self.verbose = verbose
        self.verbose_tx = verbose_tx

    def to_params(self):
        res = [self.hash]
        if self.verbose is not None:
            res.append(self.verbose)
        if self.verbose_tx is not None:
            res.append(self.verbose_tx)
        return res

    @classmethod
    def from_params(cls, params):
        require_length(params, [1, 3], "getblock should have [1,3] params")

        require_type(params[0], str, "hash should be str")
        hash = params[0]

        if len(params) > 1:
            require_type(params[1], bool, "verbose should be boolean")
            verbose = params[1]
        else:
            verbose = True

        if len(params) > 2:
            require_type(params[2], bool, "verbose_tx should be boolean")
            verbose_tx = params[2]
        else:
            verbose_tx = False

        return cls(hash, verbose, verbose_tx)

    def __eq__(self, other):
        if not isinstance(other, GetBlockCmd):
            return False

        return self.hash == other.hash and \
               self.verbose == other.verbose and \
               self.verbose_tx == other.verbose_tx


# GetBlockChainInfoCmd defines the getblockchaininfo JSON-RPC command.
@register_name("getblockchaininfo")
class GetBlockChainInfoCmd:
    def __init__(self):
        pass

    def to_params(self):
        return []

    @classmethod
    def from_params(cls, params):
        require_length(params, 0, "getblockchaininfo should have 0 params")
        return cls()

    def __eq__(self, other):
        return isinstance(other, GetBlockChainInfoCmd)


# GetBlockCountCmd defines the getblockcount JSON-RPC command.
@register_name("getblockcount")
class GetBlockCountCmd:
    def __init__(self):
        pass

    def to_params(self):
        return []

    @classmethod
    def from_params(cls, params):
        require_length(params, 0, "getblockcount should have 0 params")
        return cls()

    def __eq__(self, other):
        return isinstance(other, GetBlockCountCmd)


# GetBlockHashCmd defines the getblockhash JSON-RPC command.
@register_name("getblockhash")
class GetBlockHashCmd:
    def __init__(self, index: int):
        self.index = index

    def to_params(self):
        return [self.index]

    @classmethod
    def from_params(cls, params):
        require_length(params, 1, "getblockhash should have 1 param")
        require_type(params[0], int, "index should be str")
        index = params[0]
        return cls(index=index)

    def __eq__(self, other):
        if not isinstance(other, GetBlockHashCmd):
            return False

        return self.index == other.index


# GetBlockHeaderCmd defines the getblockheader JSON-RPC command.
@register_name("getblockheader")
class GetBlockHeaderCmd:
    def __init__(self, hash: str, verbose: bool or None):
        self.hash = hash
        self.verbose = verbose

    def to_params(self):
        res = [self.hash]
        if self.verbose is not None:
            res.append(self.verbose)

        return res

    @classmethod
    def from_params(cls, params):
        require_length(params, [1, 2], "getblockheader should have [1,2] param")

        require_type(params[0], str, "hash should be str")
        hash = params[0]

        if len(params) > 1:
            require_type(params[1], bool, "verbose should be bool")
            verbose = params[1]
        else:
            verbose = True

        return cls(hash=hash, verbose=verbose)

    def __eq__(self, other):
        if not isinstance(other, GetBlockHeaderCmd):
            return False

        return self.hash == other.hash and \
               self.verbose == other.verbose


# TemplateRequest is a request object as defined in BIP22
# (https:#en.bitcoin.it/wiki/BIP_0022), it is optionally provided as an
# pointer argument to GetBlockTemplateCmd.
class TemplateRequest:
    def __init__(self, mode: str or None = None,
                 capabilities: [str] or None = None,
                 long_pool_id: str or None = None,
                 sig_op_limit: int or bool or None = None,
                 size_limit: int or bool or None = None,
                 max_version: int or None = None,
                 target: str or None = None,
                 data: str or None = None,
                 work_id: str or None = None,
                 ):
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

    def to_params(self):
        d = collections.OrderedDict()
        if self.mode is not None:
            d['mode'] = self.mode

        if self.capabilities is not None:
            d['capabilities'] = self.capabilities

        if self.long_pool_id is not None:
            d['longpollid'] = self.long_pool_id

        if self.sig_op_limit is not None:
            d['sigoplimit'] = self.sig_op_limit

        if self.size_limit is not None:
            d['sizelimit'] = self.size_limit

        if self.max_version is not None:
            d['maxversion'] = self.max_version

        if self.target is not None:
            d['target'] = self.target

        if self.data is not None:
            d['data'] = self.data

        if self.work_id is not None:
            d['workid'] = self.work_id

        return d

    def __eq__(self, other):
        if not isinstance(other, TemplateRequest):
            return False

        return self.mode == other.mode and \
               self.capabilities == other.capabilities and \
               self.long_pool_id == other.long_pool_id and \
               self.sig_op_limit == other.sig_op_limit and \
               self.size_limit == other.size_limit and \
               self.max_version == other.max_version and \
               self.target == other.target and \
               self.data == other.data and \
               self.work_id == other.work_id

    @classmethod
    def from_params(cls, params):
        require_type(params, dict, "template request should be dict")

        request = cls()
        if 'mode' in params:
            request.mode = params['mode']

        if 'capabilities' in params:
            request.capabilities = params['capabilities']

        if 'longpollid' in params:
            request.long_pool_id = params['longpollid']

        if 'sigoplimit' in params:
            request.sig_op_limit = params['sigoplimit']

        if 'sizelimit' in params:
            request.size_limit = params['sizelimit']

        if 'maxversion' in params:
            request.max_version = params['maxversion']

        if 'target' in params:
            request.target = params['target']

        if 'data' in params:
            request.data = params['data']

        if 'workid' in params:
            request.work_id = params['workid']

        return request


# GetBlockTemplateCmd defines the getblocktemplate JSON-RPC command.
@register_name("getblocktemplate")
class GetBlockTemplateCmd:
    def __init__(self, request: TemplateRequest or None = None):
        self.request = request

    def to_params(self):
        if self.request is None:
            return []

        return [self.request.to_params()]

    @classmethod
    def from_params(cls, params):
        require_length(params, [0, 1], "template request should have [0,1] params")

        if len(params) == 0:
            return cls()

        return cls(request=TemplateRequest.from_params(params[0]))

    def __eq__(self, other):
        if not isinstance(other, GetBlockTemplateCmd):
            return False
        return self.request == other.request


# GetCFilterCmd defines the getcfilter JSON-RPC command.
@register_name("getcfilter")
class GetCFilterCmd:
    def __init__(self, hash: str, filter_type: wire.FilterType):
        self.hash = hash
        self.filter_type = filter_type

    def to_params(self):
        return [self.hash, int(self.filter_type)]

    @classmethod
    def from_params(cls, params):
        require_length(params, 2, "getcfilter should have 2 params")
        require_type(params[0], str, "hash should be str")
        hash = params[0]
        require_type(params[1], int, "FilterType should be int")
        filter_type = wire.FilterType(params[1])
        return cls(hash=hash, filter_type=filter_type)

    def __eq__(self, other):
        if not isinstance(other, GetCFilterCmd):
            return False
        return self.hash == other.hash and self.filter_type == other.filter_type


# GetCFilterHeaderCmd defines the getcfilterheader JSON-RPC command.
@register_name("getcfilterheader")
class GetCFilterHeaderCmd:
    def __init__(self, hash: str, filter_type: wire.FilterType):
        self.hash = hash
        self.filter_type = filter_type

    def to_params(self):
        return [self.hash, int(self.filter_type)]

    @classmethod
    def from_params(cls, params):
        require_length(params, 2, "getcfilter should have 2 params")
        require_type(params[0], str, "hash should be str")
        hash = params[0]
        require_type(params[1], int, "FilterType should be int")
        filter_type = wire.FilterType(params[1])
        return cls(hash=hash, filter_type=filter_type)

    def __eq__(self, other):
        if not isinstance(other, GetCFilterHeaderCmd):
            return False
        return self.hash == other.hash and self.filter_type == other.filter_type
