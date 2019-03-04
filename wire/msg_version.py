import pyutil
from .netaddress import *

# MaxUserAgentLen is the maximum allowed length for the user agent field in a
# version message (MsgVersion).
MaxUserAgentLen = 256

# DefaultUserAgent for wire in the stack
DefaultUserAgent = "/btcwire:0.5.0/"


class MsgVersion(Message):
    def __init__(self,
                 addr_you,
                 addr_me=None,
                 nonce=0,
                 last_block=0,
                 services=None,
                 timestamp: int = pyutil.now(),
                 protocol_version: int = ProtocolVersion,
                 user_agent: str = DefaultUserAgent,
                 disable_relay_tx: bool = False):
        self.protocol_version = protocol_version
        self.timestamp = timestamp
        self.services = Services(services)
        self.addr_you = addr_you
        self.addr_me = addr_me
        self.nonce = nonce
        self.user_agent = user_agent
        self.last_block = last_block
        self.disable_relay_tx = disable_relay_tx

        super(MsgVersion, self).__init__()

    def __eq__(self, other):
        return self.addr_you == other.addr_you \
               and self.addr_me == other.addr_me \
               and self.nonce == other.nonce \
               and self.last_block == other.last_block \
               and self.services == other.services \
               and self.timestamp == other.timestamp \
               and self.protocol_version == other.protocol_version \
               and self.user_agent == other.user_agent \
               and self.disable_relay_tx == other.disable_relay_tx

    def has_service(self, service: ServiceFlag) -> bool:
        return self.services.has_service(service)

    def add_service(self, service: ServiceFlag):
        self.services.add_service(service)

    def command(self):
        return Commands.CmdVersion

    # BtcDecode decodes r using the bitcoin protocol encoding into the receiver.
    # The version message is special in that the protocol version hasn't been
    # negotiated yet.  As a result, the pver field is ignored and any fields which
    # are added in new versions are optional.  This also mean that r must be a
    # *bytes.Buffer so the number of remaining bytes can be ascertained.
    #
    # This is part of the Message interface implementation.
    def btc_decode(self, s, pver, message_encoding):
        # TOCHECK Find length of stream
        s.seek(0, 2)
        eof_index = s.tell()
        s.seek(0, 0)

        self.protocol_version = read_element(s, "int32")
        self.services = read_element(s, "services")
        self.timestamp = read_element(s, "int64")
        self.addr_you = read_netaddress(s, pver, False)

        # Protocol versions >= 106 added a from address, nonce, and user agent
        # field and they are only considered present if there are bytes
        # remaining in the message.
        if s.tell() < eof_index:
            self.addr_me = read_netaddress(s, pver, False)
        if s.tell() < eof_index:
            self.nonce = read_element(s, "uint64")
        if s.tell() < eof_index:
            user_agent = read_var_string(s, pver)
            self.valid_user_agent(user_agent)
            self.user_agent = user_agent

        # Protocol versions >= 209 added a last known block field.  It is only
        # considered present if there are bytes remaining in the message.
        # TOCHECK don't see this in https://en.bitcoin.it/wiki/Protocol_documentation#version
        if s.tell() < eof_index:
            self.last_block = read_element(s, "int32")

        # There was no relay transactions field before BIP0037Version, but
        # the default behavior prior to the addition of the field was to always
        # relay transactions.
        if s.tell() < eof_index:
            self.disable_relay_tx = not read_element(s, "bool")

        return

    # BtcEncode encodes the receiver to w using the bitcoin protocol encoding.
    # This is part of the Message interface implementation.
    # me -> you: from -> recv
    def btc_encode(self, s, pver, message_encoding):
        self.valid_user_agent(self.user_agent)

        write_element(s, "int32", self.protocol_version)
        write_element(s, "services", self.services)
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

    def max_payload_length(self, pver: int) -> int:

        # XXX: <= 106 different

        # Protocol version 4 bytes + services 8 bytes + timestamp 8 bytes +
        # remote and local net addresses + nonce 8 bytes + length of user
        # agent (varInt) + max allowed useragent length + last block 4 bytes +
        # relay transactions flag 1 byte.

        return 33 + (max_netaddress_payload(pver) * 2) + MaxVarIntPayload + MaxUserAgentLen

    # AddUserAgent adds a user agent to the user agent string for the version
    # message.  The version string is not defined to any strict format, although
    # it is recommended to use the form "major.minor.revision" e.g. "2.6.41".
    def add_user_agent(self, name: str, version: str, comments: list = list()):
        comments_str = "{}".format("; ".join(comments))
        if comments_str:
            new_user_agent = "{}:{}({})".format(name, version, comments_str)
        else:
            new_user_agent = "{}:{}".format(name, version)
        new_user_agent = "{}{}/".format(self.user_agent, new_user_agent)
        self.valid_user_agent(new_user_agent)
        self.user_agent = new_user_agent

    # validateUserAgent checks userAgent length against MaxUserAgentLen
    def valid_user_agent(self, user_agent: str):
        if len(user_agent) > MaxUserAgentLen:
            raise MessageVersionLengthTooLong
        return
