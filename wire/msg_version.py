from .message import *
from .netaddress import *
from .common import *

# MaxUserAgentLen is the maximum allowed length for the user agent field in a
# version message (MsgVersion).
MaxUserAgentLen = 256


# DefaultUserAgent for wire in the stack
DefaultUserAgent = "/btcwire:0.5.0/"


TimeNow = int(time.time())

class MsgVersion(Message):
    def __init__(self,
                 addr_you: NetAddress,
                 addr_me: NetAddress,
                 nonce: int,
                 last_block: int,
                 timestamp: int = TimeNow,
                 protocol_version: int = ProtocolVersion,
                 user_agent: str = DefaultUserAgent,
                 services: ServiceFlag = 0,
                 disable_relay_tx: bool = False):
        self.protocol_version = protocol_version
        self.timestamp = timestamp
        self.services = services
        self.addr_you = addr_you
        self.addr_me = addr_me
        self.nonce = nonce
        self.user_agent = user_agent
        self.last_block = last_block
        self.disable_relay_tx = disable_relay_tx

        super(MsgVersion, self).__init__()

    def has_service(self, service: ServiceFlag) -> bool:
        return self.services & service == service

    def add_service(self, service: ServiceFlag):
        self.services |= service

    def command(self):
        return Commands.CmdVersion

    # BtcDecode decodes r using the bitcoin protocol encoding into the receiver.
    # The version message is special in that the protocol version hasn't been
    # negotiated yet.  As a result, the pver field is ignored and any fields which
    # are added in new versions are optional.  This also mean that r must be a
    # *bytes.Buffer so the number of remaining bytes can be ascertained.
    #
    # This is part of the Message interface implementation.
    def btc_decode(self, s , pver, message_encoding):
        read_element()
        # TODO





    # BtcEncode encodes the receiver to w using the bitcoin protocol encoding.
    # This is part of the Message interface implementation.
    # me -> you: from -> recv
    def btc_encode(self, s, pver, message_encoding):
        self.valid_user_agent(self.user_agent)

        write_element(s, "int32", self.protocol_version)
        write_element(s, "ServiceFlag", self.services)
        write_element(s, "int64", self.timestamp)
        write_netaddress(s, pver, self.addr_you, False)

        # TOCHECK as protocol say: Fields below require version ≥ 106
        # So why origin don't check it?

        write_netaddress(s, pver, self.addr_me, False)
        write_element(s, "uint64", self.nonce)
        write_var_string(s, pver, self.user_agent)
        write_element(s, "int32", self.last_block)

        if pver >= BIP0037Version:
            write_element(s, "bool", not self.disable_relay_tx)
        return

    def max_payload_length(self) -> int:
        raise NotImplementedError

    def add_user_agent(self):
        pass

    def valid_user_agent(self, user_agent):
        # TODO
        pass
