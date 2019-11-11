# TODO the error message is a mess

def require_length(params, ran, err_msg):
    if type(ran) is list:
        if not ran[0] <= len(params) <= ran[1]:
            raise Exception(err_msg)

    elif type(ran) is int:
        if len(params) != ran:
            raise Exception(err_msg)

    else:
        raise Exception("should not happen")


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


from .register import register_cmd_name


def register_name(name):
    def inner_fn(cls):
        register_cmd_name(name, cls)
        cls.name = name  # need or not here?
        return cls
