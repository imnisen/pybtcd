import unittest
import wire
from btcjson.chain_svr_cmds import *
from btcjson.marshal_json import *


# TODO add new_cmd latter
class TestChainSvrCmds(unittest.TestCase):
    def test_btcjson(self):
        test_id = 1
        tests = [
            {
                "name": "addnode",
                # "new_cmd": new_cmd("addnode", "127.0.0.1", str(ANRemove)),
                "static_cmd": AddNodeCmd("127.0.0.1", ANRemove),
                "marshalled": '{"jsonrpc":"1.0","method":"addnode","params":["127.0.0.1","remove"],"id":1}',
                "unmarshalled": AddNodeCmd("127.0.0.1", ANRemove),
            },

            {
                "name": "createrawtransaction",
                # "new_cmd": new_cmd("createrawtransaction", '[{"txid":"123","vout":1}]', '{"456":0.0123}'),
                "static_cmd": CreateRawTransactionCmd([TransactionInput("123", 1)], {"456": .0123}),
                "marshalled": '{"jsonrpc":"1.0","method":"createrawtransaction","params":[[{"txid":"123","vout":1}],{"456":0.0123}],"id":1}',
                "unmarshalled": CreateRawTransactionCmd([TransactionInput("123", 1)], {"456": .0123}),
            },

            {
                "name": "createrawtransaction optional",
                # "new_cmd": new_cmd("createrawtransaction", '[{"txid":"123","vout":1}]', '{"456":0.0123}'),
                "static_cmd": CreateRawTransactionCmd([TransactionInput("123", 1)], {"456": .0123}, 12312333333),
                "marshalled": '{"jsonrpc":"1.0","method":"createrawtransaction","params":[[{"txid":"123","vout":1}],{"456":0.0123},12312333333],"id":1}',
                "unmarshalled": CreateRawTransactionCmd([TransactionInput("123", 1)], {"456": .0123}, 12312333333),
            },

            {
                "name": "decoderawtransaction",
                "static_cmd": DecodeRawTransactionCmd("123"),
                "marshalled": '{"jsonrpc":"1.0","method":"decoderawtransaction","params":["123"],"id":1}',
                "unmarshalled": DecodeRawTransactionCmd("123"),
            },

            {
                "name": "decodescript",
                "static_cmd": DecodeScriptCmd("00"),
                "marshalled": '{"jsonrpc":"1.0","method":"decodescript","params":["00"],"id":1}',
                "unmarshalled": DecodeScriptCmd("00"),
            },

            {
                "name": "getaddednodeinfo",
                "static_cmd": GetAddedNodeInfoCmd(True),
                "marshalled": '{"jsonrpc":"1.0","method":"getaddednodeinfo","params":[true],"id":1}',
                "unmarshalled": GetAddedNodeInfoCmd(True),
            },

            {
                "name": "getaddednodeinfo optional",
                "static_cmd": GetAddedNodeInfoCmd(True, "127.0.0.1"),
                "marshalled": '{"jsonrpc":"1.0","method":"getaddednodeinfo","params":[true,"127.0.0.1"],"id":1}',
                "unmarshalled": GetAddedNodeInfoCmd(True, "127.0.0.1"),
            },

            {
                "name": "getbestblockhash",
                "static_cmd": GetBestBlockHashCmd(),
                "marshalled": '{"jsonrpc":"1.0","method":"getbestblockhash","params":[],"id":1}',
                "unmarshalled": GetBestBlockHashCmd(),
            },

            {
                "name": "getblock",
                "static_cmd": GetBlockCmd("123", None, None),
                "marshalled": '{"jsonrpc":"1.0","method":"getblock","params":["123"],"id":1}',
                "unmarshalled": GetBlockCmd("123", True, False),
            },

            {
                "name": "getblock required optional1",
                "static_cmd": GetBlockCmd("123", True, None),
                "marshalled": '{"jsonrpc":"1.0","method":"getblock","params":["123",true],"id":1}',
                "unmarshalled": GetBlockCmd("123", True, False),
            },

            {
                "name": "getblock required optional2",
                "static_cmd": GetBlockCmd("123", True, True),
                "marshalled": '{"jsonrpc":"1.0","method":"getblock","params":["123",true,true],"id":1}',
                "unmarshalled": GetBlockCmd("123", True, True),
            },

            {
                "name": "getblockchaininfo",
                "static_cmd": GetBlockChainInfoCmd(),
                "marshalled": '{"jsonrpc":"1.0","method":"getblockchaininfo","params":[],"id":1}',
                "unmarshalled": GetBlockChainInfoCmd(),
            },

            {
                "name": "getblockcount",
                "static_cmd": GetBlockCountCmd(),
                "marshalled": '{"jsonrpc":"1.0","method":"getblockcount","params":[],"id":1}',
                "unmarshalled": GetBlockCountCmd(),
            },

            {
                "name": "getblockhash",
                "static_cmd": GetBlockHashCmd(123),
                "marshalled": '{"jsonrpc":"1.0","method":"getblockhash","params":[123],"id":1}',
                "unmarshalled": GetBlockHashCmd(123),
            },

            {
                "name": "getblockheader",
                "static_cmd": GetBlockHeaderCmd("123", None),
                "marshalled": '{"jsonrpc":"1.0","method":"getblockheader","params":["123"],"id":1}',
                "unmarshalled": GetBlockHeaderCmd("123", True),
            },

            {
                "name": "getblocktemplate",
                "static_cmd": GetBlockTemplateCmd(request=None),
                "marshalled": '{"jsonrpc":"1.0","method":"getblocktemplate","params":[],"id":1}',
                "unmarshalled": GetBlockTemplateCmd(request=None),
            },

            {
                "name": "getblocktemplate optional - template request",
                "static_cmd": GetBlockTemplateCmd(
                    request=TemplateRequest(
                        mode="template",
                        capabilities=["longpoll", "coinbasetxn"],
                    )
                ),
                "marshalled": '{"jsonrpc":"1.0","method":"getblocktemplate","params":[{"mode":"template","capabilities":["longpoll","coinbasetxn"]}],"id":1}',
                "unmarshalled": GetBlockTemplateCmd(
                    request=TemplateRequest(
                        mode="template",
                        capabilities=["longpoll", "coinbasetxn"],
                    )
                ),
            },

            {
                "name": "getblocktemplate optional - template request with tweaks",
                "static_cmd": GetBlockTemplateCmd(
                    request=TemplateRequest(
                        mode="template",
                        capabilities=["longpoll", "coinbasetxn"],
                        sig_op_limit=500,
                        size_limit=100000000,
                        max_version=2,
                    )
                ),
                "marshalled": '{"jsonrpc":"1.0","method":"getblocktemplate","params":[{"mode":"template","capabilities":["longpoll","coinbasetxn"],"sigoplimit":500,"sizelimit":100000000,"maxversion":2}],"id":1}',
                "unmarshalled": GetBlockTemplateCmd(
                    request=TemplateRequest(
                        mode="template",
                        capabilities=["longpoll", "coinbasetxn"],
                        sig_op_limit=500,
                        size_limit=100000000,
                        max_version=2,
                    )
                ),
            },

            {
                "name": "getblocktemplate optional - template request with tweaks 2",
                "static_cmd": GetBlockTemplateCmd(
                    request=TemplateRequest(
                        mode="template",
                        capabilities=["longpoll", "coinbasetxn"],
                        sig_op_limit=True,
                        size_limit=100000000,
                        max_version=2,
                    )
                ),
                "marshalled": '{"jsonrpc":"1.0","method":"getblocktemplate","params":[{"mode":"template","capabilities":["longpoll","coinbasetxn"],"sigoplimit":true,"sizelimit":100000000,"maxversion":2}],"id":1}',
                "unmarshalled": GetBlockTemplateCmd(
                    request=TemplateRequest(
                        mode="template",
                        capabilities=["longpoll", "coinbasetxn"],
                        sig_op_limit=True,
                        size_limit=100000000,
                        max_version=2,
                    )
                ),
            },

            {
                "name": "getcfilter",
                "static_cmd": GetCFilterCmd("123", wire.GCSFilterRegular),
                "marshalled": '{"jsonrpc":"1.0","method":"getcfilter","params":["123",0],"id":1}',
                "unmarshalled": GetCFilterCmd("123", wire.GCSFilterRegular),
            },

            {
                "name": "getcfilterheader",
                "static_cmd": GetCFilterHeaderCmd("123", wire.GCSFilterRegular),
                "marshalled": '{"jsonrpc":"1.0","method":"getcfilterheader","params":["123",0],"id":1}',
                "unmarshalled": GetCFilterHeaderCmd("123", wire.GCSFilterRegular),
            },

        ]

        for test in tests:
            marshalled = marshal_cmd(test_id, test["static_cmd"])
            self.assertEqual(marshalled, test["marshalled"])

            # cmd = test["new_cmd"]
            # marshalled = marshal_cmd(test_id, cmd)
            # self.assertEqual(marshalled, test["marshalled"])

            request = json.loads(test["marshalled"])
            cmd = unmarshal_cmd(request)
            self.assertEqual(cmd, test["unmarshalled"])
