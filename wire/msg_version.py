from .message import *
from .netaddress import *

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

    def btc_decode(self):
        # TOADD
        raise NotImplementedError

    def btc_encode(self):
        # TOADD
        raise NotImplementedError

    def max_payload_length(self) -> int:
        raise NotImplementedError

    def add_user_agent(self):
        pass

    def valid_user_agent(self):
        pass
