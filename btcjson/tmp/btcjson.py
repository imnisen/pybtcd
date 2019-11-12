import json
import copy


def btcjson_dumps(the_id: int, cmd_data: dict) -> bytes:
    jsonrpc = "1.0"

    method_name = cmd_data["method"]

    # generate params str

    params_str = "["
    for i in range(len(cmd_data['fields'])):
        marshal_type = cmd_data['fields'][i]['marshal'][0]
        field_value = cmd_data['fields'][i]['value']

        if marshal_type == "array":

            if field_value is None:
                # if the value is None, then the can_empty must be True
                # as we have check this in new_cmd, we just assert here
                assert cmd_data['fields'][i]['empty'][0] == True

                if cmd_data['fields'][i]['empty'][1] is True:
                    # can leave empty
                    continue
                else:
                    # cannot leave empty, so we get the default value
                    field_value = cmd_data['fields'][i]['empty'][2]

            params_str += json.dumps(field_value) + ","


        elif marshal_type == "dict":
            pass  # TODO
        else:
            pass  # TODO

    params_str = params_str[:-1]
    params_str += "]"

    ret = '{"jsonrpc":"%s","method":"%s","params":%s,"id":%d}' % (jsonrpc, method_name, params_str, the_id)
    return ret.encode('utf-8')


# some assumption(that need to be check latter)
# loads case that can't handle
# -> 1，1，1, 1
# -> can empty: false, true, true, true, true
#
# so let's define, if a field can be empty, the fields after it can also be empty.
# so follow this rule, the parse process can be simple, one to one until not found
#
# btcjson_loads get a marshaled bytes as input, returns a dict cmd with value insert in it
def btcjson_loads(b: bytes) -> dict:
    cmd_str = b.decode('utf-8')
    cmd_dict = json.loads(cmd_str)

    # get method name
    method_str = cmd_dict.get('method')
    if method_str is None:
        raise Exception("don't have a method in bytes")

    # get cmd
    cmd = get_cmd(method_str)

    # get params list
    params_list = cmd_dict.get('params')
    if params_list is None:
        raise Exception("don't have a params in bytes")

    # According to cmd structure, parse the params list
    # first, check the length
    pass_length_check(cmd, params_list)

    for i in range(len(cmd['fields'])):

        # when no params supply, we set the field to None
        if i > len(params_list) - 1:
            cmd['fields'][i]['value'] = None
            continue

        # As follow the assumption, we don't need to check the 'empty' of field
        # just to do `one to one` parse

        field = cmd['fields'][i]

        # check the value type is as expected
        if not pass_type_check(params_list[i], field['type']):
            raise Exception("params %s is not as expected %s" % (params_list[i], field['type']))


        if field['marshal'][0] == 'array':

            # insert the value to cmd
            cmd['fields'][i]['value'] = params_list[i]

        elif field['marshal'][0] == 'dict':
            # TODO
            raise

        else:
            # TODO
            raise
    return cmd




# this is for str->cmd search
all_cmds = {}  # make this global?


def register_cmd(d: dict):
    all_cmds[d['method']] = d
    return d


# This list is type collection, include python type and type string used in definition of cmd
type_list = [
    (str, "string"),
    (int, "int", "int32", "int64", "uint32"),
    (bool, "bool"),
]


# TODO should also handle null type can any other type check
#
def pass_type_check(value, expected_type) -> bool:
    # value:  "abcde"
    # expected_type_list: 'string'

    # value:  False
    # expected_type_list: 'bool'

    # value:  [False, False]
    # expected_type_list:['list', 'bool']

    # value:  [{"txid":"123", "vout":1}]
    # expected_type_list: ["list", ["refer", "TransactionInput"]]# here we use tuple as a special notation of refer type

    # value:  {"txid":"123", "vout":1}  # 当btcjson_loads时是这样传入值的
    # expected_type_list: ["refer", "TransactionInput"]

    # value: [1,2,3]
    # expected_type_list: ["list", "int64"]

    # value:  {"456": 0.0123}
    # expected_type_list: ["map", "string", "float64"]

    # value:  {"456": {"txid":"123", "vout":1}}
    # expected_type_list: ["map", "string", ["refer", "TransactionInput"]]

    if value is None:
        return True

    if type(expected_type) is list:
        # could be list or map
        pass

    elif type(expected_type) is tuple:  # single refer type

        # now, the first should be "refer"
        assert expected_type[0] == 'refer'

        refer_type = all_cmds.get(expected_type[1])
        if refer_type is None:
            raise Exception("refer type %s is not registered" % expected_type[1])

        if type(value) is not tuple:  # when refer type, value should pass as () tuple
            return False

        # check length (TODO why check length again here?)


        # 目前遇到的一个问题就是
        # 当new_cmd的时候，参数和fileds数量一定相等，没有的传None，
        # 而当btcjson_loads的时候，参数可以唯恐，按照从前到后一对一解析
        # 这导致了这递归check_type的时候，



        for i in range(len(refer_type['fields'])):
            pass_type_check()





    else: # single case type
        for t in type_list:
            if type(expected_type) in t and expected_type in t:
                return True
        return False


# get cmd from str
# each time return a new instance
def get_cmd(cmd_str):
    cmd = all_cmds.get(cmd_str)
    if cmd is None:
        raise Exception('name: %s can\'t find register cmd' % cmd_str)
    return copy.deepcopy(cmd)

# todo latter
# 遇到问题，"是否留空" 和 "是否可以留空" 有差别
def get_fields_at_least_length(fields):
    length = 0
    for f in fields:
        if f['empty'][0] is True:
            if f['empty'][1] is True:
                continue
            else:
                length += 1
        else:
            length += 1
    return length


def pass_length_check(cmd: dict,  values: list) -> bool:
    if len(values) < get_fields_at_least_length(cmd['fields']):
        raise Exception('values length:%d is less than as cmd %s at least required length %d' % (
            len(values), cmd['method'], get_fields_at_least_length(cmd['fields'])))


def new_cmd(cmd_str, *args):
    # here when pack args, we need to inject the which arg the arg mean,
    # or just do like golang, use a lot of new methods to seperate them
    # suppose we pass all the arg, including `None` field.
    # now let's pack the arg data with its struct.
    # 8.18 update.
    # now, we change strategy, we parse one to one , until no arg, we inject None value

    # cmd_str -> cmd
    cmd = get_cmd(cmd_str)

    # # first check length
    # pass_length_check(cmd, list(args))

    # # TODO let's move empty check to type check?
    # # # second check empty
    # # for i in range(len(cmd['fields'])):
    # #     if cmd['fields'][i]['empty'][0] is False and args[i] is None:
    # #         raise Exception("field {} cannot leave None".format(cmd['fields'][i]['name']))
    #
    # # third check type[not completed now]
    # # 1. first let's check the basic type
    # for i in range(len(cmd['fields'])):
    #
    #     if not pass_type_check(args[i], cmd['fields'][i]['type']):
    #         raise Exception("field %s: %s, needs type %s" % (cmd['fields'][i]['name'], args[i], cmd['fields'][i]['type']))
    #
    # # last inject value  # TODO inject refer value should be different
    # cmd2 = copy.deepcopy(cmd)
    # for i in range(len(cmd2['fields'])):
    #     cmd2["fields"][i]['value'] = args[i]


    check_and_set(cmd, list(args))


    return cmd


# some assumption(that need to be check latter)
# loads case that can't handle
# -> 1，1，1, 1
# -> can empty: false, true, true, true, true
#
# so let's define, if a field can be empty, the fields after it can also be empty.
# so follow this rule, the parse process can be simple, one to one until not found
#
# btcjson_loads get a marshaled bytes as input, returns a dict cmd with value insert in it
def check_and_set(cmd: dict, values: list, is_dumps: bool, is_loads: bool):  # is_dumps,is_loads is a temp params.

    pass_length_check(cmd, values)

    # parse one to one
    for i in range(len(cmd['fields'])):
        # when no params supply, we set the field to None
        if i > len(values) - 1:
            cmd['fields'][i]['value'] = None
            continue

        # handle value is `None` case
        if values[i] is None:

            # check field can_empty
            if cmd['fields'][i]['empty'][0] is False:
                raise Exception("field: %s cannot leave empty" % cmd['fields'][i]['name'])

            # in btcjson_loads, when value is None, and it should use default value, let's raise exception
            # in new_cmd, we should allow this case
            if is_loads:
                if cmd['fields'][i]['empty'][1] is False and cmd['fields'][i]['empty'][2] is not None:
                    raise Exception("field: %s should use default value" % cmd['fields'][i]['name'])

            cmd['fields'][i]['value'] = None
            continue


        if type(cmd['fields'][i]['type']) is list:
            if cmd['fields'][i]['type'][0] == 'refer':  # this is a refer type

                refer_cmd = get_cmd(cmd['fields'][i][1])
                cmd['fields'][i]['value'] = check_and_set(refer_cmd, values[i], is_dumps=is_dumps, is_loads=is_loads)
                continue

            elif cmd['fields'][i]['type'][0] == 'map':  # this is a map type

                # TODO empty check?

                # refer to marshal, get the value
                # values could be `v` or `{'key': v}`.
                v = get_value_according_marshal_type(cmd['fields'][i]['marshal'], values[i])


                # key and value can be complex type too. my god.
                # 总觉得我这个递归写的不够common case.
                # 或者是我的抽象不够好，没办法直接递归调用自己
                # TODO



            elif cmd['fields'][i][0] == 'list':  # this is a list type
                pass


        else:
            # refer to marshal, get the value
            # values could be `v` or `{'key': v}`.
            v = get_value_according_marshal_type(cmd['fields'][i]['marshal'], values[i])

            # check type match
            match = False
            for each in type_list:
                if type(v) in each and cmd['fields'][i]['type'] in each:
                    match = True

            if not match:
                raise Exception("field:%s, with value:%s, not match: %s" % (
                    cmd['fields'][i]['name'], v,  cmd['fields'][i]['type']))

            # set value
            cmd['fields'][i]['value'] = v

            continue

    return cmd
        
        



def get_value_according_marshal_type(marsha_list, value):
    if marsha_list[0] == 'array':  # `v` type
        v = value
    else:  # `{'key': v}` type
        key = marsha_list[1]
        if key not in value:
            raise Exception("when marshal `dict`, field value should use key %s" % key)
        v = value[key]
    return v













    pass

