import unittest
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
