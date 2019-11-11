import json
import collections
from .register import *


def marshal_cmd(id, cmd):
    d = collections.OrderedDict(
        jsonrpc="1.0",
        method=cmd.name,
        params=cmd.to_params(),
        id=id
    )
    return json.dumps(d, separators=(',', ':'))


def unmarshal_cmd(request: dict):
    method = request.get("method")
    if method is None:
        raise Exception("method not found in request")

    cmd = find_cmd(method)

    params = request.get("params")
    return cmd.from_params(params)
