# TODO the error message is a mess

#
# def require_length(cmd_name, params, n):
#     if len(params) != n:
#         raise Exception("%s unmarshal_json error: length is not %s" % (cmd_name, n))
#
#
# def require_length_range(cmd_name, params, m, n):
#     if not m <= len(params) <= n:
#         raise Exception("%s unmarshal_json error: length is not in range [%s,%s]" % (cmd_name, m, n))
#

def require_length(params, ran, err_msg):
    if type(ran) is list:
        if not ran[0] <= len(params) <= ran[1]:
            raise Exception(err_msg)

    elif type(ran) is int:
        if len(params) != ran:
            raise Exception(err_msg)

    else:
        raise Exception("should not happen")


# def require_type(cmd_name, param_name, param, typ):
#     if type(param) is not typ:
#         raise Exception("%s unmarshal_json error: %s should be %s" % (cmd_name, param_name, typ))


def require_type(param, typ, err_msg):
    if type(param) is not typ:
        raise Exception(err_msg)


def list_equal(l1, l2):
    if len(l1) != len(l2):
        return False

    for i in range(len(l1)):
        if l1[i] != l2[i]:
            return False

    return True


def dict_equal(d1: dict, d2: dict):
    if len(d1) != len(d2):
        return False

    for k, v in d1.items():
        if k not in d2:
            return False

        if d2[k] != v:
            return False

    return True
