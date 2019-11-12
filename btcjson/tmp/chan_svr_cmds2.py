from btcjson import register_cmd
# AddNodeCmd = {
#     "method": "addnode",
#     "fields": [
#         {
#             "name": "addr",
#             "marshal": ["array"],
#             "type": ["string"],  # 这里的列表是考虑有时候有复合格式， [], {} 这样的
#         },
#         {
#             "name": "addr",
#             "marshal": ["array"],
#             "type": ["string"],
#             # TODO 这里还有个它本身是3个可选值的逻辑，后续再添加吧
#         },
#     ]
#
# }
#
TransactionInput = register_cmd({
    "method": "TransactionInput",
    "fields": [
        {
            "name": "Txid",
            "marshal": ["dict", "txid"],
            "type": "string",
            "empty": [False]
        },
        {
            "name": "Vout",
            "marshal": ["dict", "vout"],
            "type": "uint32",
            "empty": [False]
        },
    ],
})

CreateRawTransactionCmd = register_cmd({
    "method": "createrawtransaction",
    "fields": [
        {
            "name": "Inputs",
            "marshal": ["array"],
            "type": ["list", ["refer", "TransactionInput"]],
            "empty": [False]
        },
        {
            "name": "Amounts",
            "marshal": ["array"],
            "type": ["map", "string", "float64"],
            "empty": [False],
        },
        {
            "name": "LockTime",
            "marshal": ["array"],
            "type": "int64",
            "empty": [True, True],
        },
    ],

})
#
# DecodeRawTransactionCmd = {
#     "method": "decoderawtransaction",
#     "fields": [
#         {
#             "name": "HexTx",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ],
# }
#
# DecodeScriptCmd = {
#     "method": "decodescript",
#     "fields": [
#         {
#             "name": "HexScript",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ],
# }
#
# GetAddedNodeInfoCmd = {
#     "method": "getaddednodeinfo",
#     "fields": [
#         {
#             "name": "DNS",
#             "marshal": ["array"],
#             "type": ["bool"],
#         },
#         {
#             "name": "Node",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ],
# }
#
# GetBestBlockHashCmd = {
#     "method": "getbestblockhash",
#     "fields": []
# }

GetBlockCmd = register_cmd({
    "method": "getblock",
    "fields": [
        {
            "name": "Hash",
            "marshal": ["array"],
            "type": "string",
            "empty": [False],

        },
        {
            "name": "Verbose",
            "marshal": ["array"],
            "type": "bool",
            "empty": [True, True],
        },
        {
            "name": "VerboseTx",
            "marshal": ["array"],
            "type": "bool",
            "empty": [True, True],
        },

    ]
})

# GetBlockChainInfoCmd = {
#     "method": "getblockchaininfo",
#     "fields": []
# }
#
# GetBlockCountCmd = {
#     "method": "getblockcount",
#     "fields": []
# }
#
# GetBlockHashCmd = {
#     "method": "getblockhash",
#     "fields": [
#         {
#             "name": "Index",
#             "marshal": ["array"],
#             "type": ["int64"],
#         },
#     ]
# }
#
# GetBlockHeaderCmd = {
#     "method": "getblockheader",
#     "fields": [
#         {
#             "name": "Hash",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "Verbose",
#             "marshal": ["array"],
#             "type": ["bool"],
#         },
#     ]
# }
#
# # TODO 这个结构自定义了UnmarshalJSON方法
# TemplateRequest = {
#     "method": "TemplateRequest",
#     "fields": [
#         {
#             "name": "Mode",
#             "marshal": ["dict", "mode"],
#             "type": ["string"],
#         },
#         {
#             "name": "Capabilities",
#             "marshal": ["dict", "capabilities"],
#             "type": ["list", "string"],
#         },
#         {
#             "name": "LongPollID",
#             "marshal": ["dict", "longpollid"],
#             "type": ["string"],
#         },
#         {
#             "name": "SigOpLimit",
#             "marshal": ["dict", "sigoplimit"],
#             "type": ["interface"],
#         },
#         {
#             "name": "SizeLimit",
#             "marshal": ["dict", "sizelimit"],
#             "type": ["interface"],
#         },
#         {
#             "name": "MaxVersion",
#             "marshal": ["dict", "maxversion"],
#             "type": ["uint32"],
#         },
#         {
#             "name": "Target",
#             "marshal": ["dict", "target"],
#             "type": ["string"],
#         },
#         {
#             "name": "Data",
#             "marshal": ["dict", "data"],
#             "type": ["bool"],
#         },
#         {
#             "name": "WorkID",
#             "marshal": ["dict", "workid"],
#             "type": ["string"],
#         },
#     ]
# }
#
# GetBlockTemplateCmd = {
#     "method": "getblocktemplate",
#     "fields": [
#         {
#             "name": "Request",
#             "marshal": ["array"],
#             "type": ["TemplateRequest"],
#         },
#     ]
# }
#
# FilterType = int  # TODO 这里怎么处理
# GetCFilterCmd = {
#     "method": "getcfilter",
#     "fields": [
#         {
#             "name": "Hash",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "FilterType",
#             "marshal": ["array"],
#             "type": ["FilterType"],
#         }
#     ]
# }
#
# GetCFilterHeaderCmd = {
#     "method": "getcfilterheader",
#     "fields": [
#         {
#             "name": "Hash",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "FilterType",
#             "marshal": ["array"],
#             "type": ["FilterType"],
#         }
#     ]
# }
#
# GetChainTipsCmd = {
#     "method": "getchaintips",
#     "fields": [],
# }
#
# GetConnectionCountCmd = {
#     "method": "getconnectioncount",
#     "fields": [],
# }
#
# GetDifficultyCmd = {
#     "method": "getdifficulty",
#     "fields": [],
# }
#
# GetGenerateCmd = {
#     "method": "getgenerate",
#     "fields": [],
# }
#
# GetHashesPerSecCmd = {
#     "method": "gethashespersec",
#     "fields": [],
# }
#
# GetInfoCmd = {
#     "method": "getinfo",
#     "fields": [],
# }
#
# GetMempoolEntryCmd = {
#     "method": "getmempoolentry",
#     "fields": [
#         {
#             "name": "TxID",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ],
# }
#
# GetMempoolInfoCmd = {
#     "method": "getmempoolinfo",
#     "fields": [],
# }
#
# GetNetworkInfoCmd = {
#     "method": "getnetworkinfo",
#     "fields": [],
# }
#
# GetNetTotalsCmd = {
#     "method": "getnettotals",
#     "fields": [],
# }
#
# GetNetworkHashPSCmd = {
#     "method": "getnetworkhashps",
#     "fields": [
#         {
#             "name": "Blocks",
#             "marshal": ["array"],
#             "type": ["int"],
#         },
#         {
#             "name": "Height",
#             "marshal": ["array"],
#             "type": ["int"],
#         },
#     ],
# }
#
# GetPeerInfoCmd = {
#     "method": "getpeerinfo",
#     "fields": [],
# }
#
# GetRawMempoolCmd = {
#     "method": "getmempool",
#     "fields": [
#         {
#             "name": "Verbose",
#             "marshal": ["array"],
#             "type": ["bool"],
#         },
#
#     ],
# }
#
# GetRawTransactionCmd = {
#     "method": "getrawtransaction",
#     "fields": [
#         {
#             "name": "Txid",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "Verbose",
#             "marshal": ["array"],
#             "type": ["int"],
#         },
#
#     ],
# }
#
# GetTxOutCmd = {
#     "method": "gettxout",
#     "fields": [
#         {
#             "name": "Txid",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "Vout",
#             "marshal": ["array"],
#             "type": ["uint32"],
#         },
#         {
#             "name": "IncludeMempool",
#             "marshal": ["array"],
#             "type": ["bool"],
#         },
#
#     ],
# }
#
# GetTxOutProofCmd = {
#     "method": "gettxoutproof",
#     "fields": [
#         {
#             "name": "TxIDs",
#             "marshal": ["array"],
#             "type": ["list", "string"],
#         },
#         {
#             "name": "BlockHash",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#
#     ],
# }
#
# GetTxOutSetInfoCmd = {
#     "method": "gettxoutsetinfo",
#     "fields": [],
# }
#
# GetWorkCmd = {
#     "method": "getwork",
#     "fields": [
#         {
#             "name": "Data",
#             "marshal": ["array"],
#             "type": ["string", ],
#         },
#     ],
# }
#
# HelpCmd = {
#     "method": "help",
#     "fields": [
#         {
#             "name": "Command",
#             "marshal": ["array"],
#             "type": ["string", ],
#         },
#     ],
# }
#
# InvalidateBlockCmd = {
#     "method": "invalidateblock",
#     "fields": [
#         {
#             "name": "BlockHash",
#             "marshal": ["array"],
#             "type": ["string", ],
#         },
#     ],
# }
#
# PingCmd = {
#     "method": "ping",
#     "fields": [],
# }
#
# PreciousBlockCmd = {
#     "method": "preciousblock",
#     "fields": [
#         {
#             "name": "BlockHash",
#             "marshal": ["array"],
#             "type": ["string", ],
#         },
#     ],
# }
#
# ReconsiderBlockCmd = {
#     "method": "reconsiderblock",
#     "fields": [
#         {
#             "name": "BlockHash",
#             "marshal": ["array"],
#             "type": ["string", ],
#         },
#     ],
# }
#
# SearchRawTransactionsCmd = {
#     "method": "searchrawtransactions",
#     "fields": [
#         {
#             "name": "Address",
#             "marshal": ["array"],
#             "type": ["string", ],
#         },
#
#         {
#             "name": "Verbose",
#             "marshal": ["array"],
#             "type": ["int", ],
#         },
#
#         {
#             "name": "Skip",
#             "marshal": ["array"],
#             "type": ["int", ],
#         },
#
#         {
#             "name": "Count",
#             "marshal": ["array"],
#             "type": ["int", ],
#         },
#
#         {
#             "name": "VinExtra",
#             "marshal": ["array"],
#             "type": ["int", ],
#         },
#
#         {
#             "name": "Reverse",
#             "marshal": ["array"],
#             "type": ["bool", ],
#         },
#
#         {
#             "name": "FilterAddrs",
#             "marshal": ["array"],
#             "type": ["list", "string"],
#         },
#     ],
# }
#
# SetGenerateCmd = {
#     "method": "setgenerate",
#     "fields": [
#         {
#             "name": "Generate",
#             "marshal": ["array"],
#             "type": ["bool"],
#         },
#         {
#             "name": "GenProcLimit",
#             "marshal": ["array"],
#             "type": ["int"],
#         },
#     ],
# }
#
# StopCmd = {
#     "method": "stop",
#     "fields": []
# }
#
# SubmitBlockOptions = {
#     "method": "SubmitBlockOptions",
#     "fields": [
#         {
#             "name": "WorkID",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ]
# }
#
# SubmitBlockCmd = {
#     "method": "submitblock",
#     "fields": [
#         {
#             "name": "HexBlock",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "Options",
#             "marshal": ["array"],
#             "type": ["SubmitBlockOptions"],
#         },
#     ]
# }
#
# UptimeCmd = {
#     "method": "uptime",
#     "fields": []
# }
#
# ValidateAddressCmd = {
#     "method": "validateaddress",
#     "fields": [
#         {
#             "name": "Address",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ]
# }
#
# VerifyChainCmd = {
#     "method": "verifychain",
#     "fields": [
#         {
#             "name": "CheckLevel",
#             "marshal": ["array"],
#             "type": ["int32"],
#         },
#         {
#             "name": "CheckDepth",
#             "marshal": ["array"],
#             "type": ["int32"],
#         },
#     ]
# }
# VerifyMessageCmd = {
#     "method": "verifychain",
#     "fields": [
#         {
#             "name": "Address",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "Signature",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#         {
#             "name": "Message",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#     ]
# }
#
# VerifyTxOutProofCmd = {
#     "method": "verifychain",
#     "fields": [
#         {
#             "name": "Proof",
#             "marshal": ["array"],
#             "type": ["string"],
#         },
#
#     ]
# }
