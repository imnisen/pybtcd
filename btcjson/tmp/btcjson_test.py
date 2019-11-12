#
# This is a temp file during development. need to move test case to tests folder
#
from btcjson import *
from chain_svr_cmds import *

if __name__ == "__main__":

    # test for GetBlockCmd
    this_id = 1
    the_hash = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
    verbose = False
    verbose_tx = None
    gb_cmd = new_cmd("getblock", the_hash, verbose, verbose_tx)

    # infact output
    marshalled_bytes = btcjson_dumps(this_id, gb_cmd)
    # expected output
    output_str = '{"jsonrpc":"1.0","method":"getblock","params":["000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",false],"id":1}'

    assert marshalled_bytes == output_str.encode('utf-8')

    output_str2 = '{"jsonrpc":"1.0","method":"getblock","params":["000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",false],"id":1}'
    cmd2 = btcjson_loads(output_str2.encode('utf-8'))
    print(cmd2) # check by eye bow :)


    # test for CreateRawTransactionCmd
    # case 1

    this_id = 1
    tx_inputs = [
        {"txid": "123", "vout": 1}
    ]
    amounts = {"456": 0.0123}
    lock_time = None

    crt_cmd = new_cmd("createrawtransaction", tx_inputs, amounts, lock_time)
    marshalled_bytes = btcjson_dumps(this_id, crt_cmd)

    expected_marshalled_bytes = '{"jsonrpc":"1.0","method":"createrawtransaction","params":[[{"txid":"123","vout":1}],{"456":0.0123}],"id":1}'
    assert marshalled_bytes == expected_marshalled_bytes.encode('utf-8')

    # case 2
    this_id = 1
    tx_inputs = [
        {"txid": "123", "vout": 1}
    ]
    amounts = {"456": 0.0123}
    lock_time = 12312333333

    crt_cmd = new_cmd("createrawtransaction", tx_inputs, amounts, lock_time)
    marshalled_bytes = btcjson_dumps(this_id, crt_cmd)

    expected_marshalled_bytes = '{"jsonrpc":"1.0","method":"createrawtransaction","params":[[{"txid":"123","vout":1}],{"456":0.0123},12312333333],"id":1}'
    assert marshalled_bytes == expected_marshalled_bytes.encode('utf-8')
