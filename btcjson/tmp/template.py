# None params
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

# One params
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
        if isinstance(other, DecodeScriptCmd):
            return self.hex_script == other.hex_script

        return False