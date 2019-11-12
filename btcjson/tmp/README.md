# This is the old files. not used now. Just some former try.


# 规则
这里定义不同结构体和字段的规则,供定义和解析时使用

```
# Simple case

GetBlockCmd = {
    "method": "getblock", # 这里是序列化后方法的名称
    "fields": [
        {
            "name": "Hash",  # 字段名称，目前无实际序列化用处，供语义识别该字段含义
            "marshal": ["array"],  # ["array"]表示该字段序列化后，只存储其值，而不存储其字段的名称
            "type": ["string"], # 字段的类型

            "empty": [True, False, ""],
            # 语义
            "empty": {
                "can_empty": True/False,  # new_cmd是否可以留空
                "omit_if_empty": True/False, # 留空的时候，dumps时是否忽略字段
                "default_value": ""   # 如果可以留空，且留空的时候不忽略，那么默认值是什么
            }
        },
        {
            "name": "Verbose",
            "marshal": ["array"],
            "type": ["bool"],
        },
        {
            "name": "VerboseTx",
            "marshal": ["array"],
            "type": ["bool"],
        },

    ]
}


# Another combination case

TransactionInput = {
    "method": "TransactionInput",
    "fields": [
        {
            "name": "Txid",
            "marshal": ["dict", "txid"],
            "type": ["string"],
            "empty": [False]
        },
        {
            "name": "Vout",
            "marshal": ["dict", "vout"],
            "type": ["uint32"],
            "empty": [False]
        },
    ],
}

CreateRawTransactionCmd = {
    "method": "createrawtransaction",
    "fields": [
        {
            "name": "Inputs",
            "marshal": ["array"],
            "type": ["list", "combination", "TransactionInput"],  # list 表示这是个list类型，combination 表示list里的元素是指代其他复合类型
            "empty": [False]
        },
        {
            "name": "Amounts",
            "marshal": ["array"],
            "type": ["map", "string", "float64"],  # map 表示 该值是一个dict，string->float64类型
            "empty": [False],
        },
        {
            "name": "LockTime",
            "marshal": ["array"],
            "type": ["int64"],
            "empty": [True, True],
        },
    ],

}
```



```
Data transfer flow


value --{new_cmd}--> cmd with value --{btcjson_dumps}--> str/bytes


str/bytes --{btcjson_loads}--> cmd with value
```

# TODO
- [X] empty case 处理
- [X] default值处理
- [ ] marshal:dict的处理
- [ ] 复合类型处理
