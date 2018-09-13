# Refer to https://en.bitcoin.it/wiki/Protocol_documentation#Network_address
import time
from .protocol import *
from .common import *


# import ipaddress

class NetAddress:
    def __init__(self, services: ServiceFlag = None, ip=None, port: int = None, timestamp: int = int(time.time()), ):
        # Last time the address was seen.  This is, unfortunately, encoded as a
        # uint32 on the wire and therefore is limited to 2106.  This field is
        # not present in the bitcoin version message (MsgVersion) nor was it
        # added until protocol version >= NetAddressTimeVersion.
        self.timestamp = timestamp

        # Bitfield which identifies the services supported by the address.
        self.services = services

        # IP address of the peer.
        self.ip = ip  # IPv4 or IPv6

        # Port the peer is using.  This is encoded in big endian on the wire
        # which differs from most everything else.
        self.port = port

    def has_service(self, service: ServiceFlag) -> bool:
        # TOCHECK  I don't know what the source code `na.Services&service == service` mean?
        # So here is my understand
        return self.services & service == service

    def add_service(self, service: ServiceFlag):
        self.services |= service

    def __eq__(self, other):
        # TODO
        pass


# maxNetAddressPayload returns the max payload size for a bitcoin NetAddress
# based on the protocol version.
def max_netaddress_payload(pver: int) -> int:
    # Services 8 bytes + ip 16 bytes + port 2 bytes.
    plen = 26

    if pver >= NetAddressTimeVersion:
        plen += 4

    return plen


# readNetAddress reads an encoded NetAddress from r depending on the protocol
# version and whether or not the timestamp is included per ts.  Some messages
# like version do not include the timestamp.
def read_netaddress(s, pver, ts):
    if ts and pver >= NetAddressTimeVersion:
        timestamp = read_element(s, "uint32Time")
    else:
        timestamp = 0

    services = read_element(s, "ServiceFlag")
    ip = read_element(s, "[16]byte")

    port = read_variable_bytes_as_integer(s, 8, BigEndian)
    return NetAddress(services=services,
                      ip=ip,
                      port=port,
                      timestamp=timestamp)


# writeNetAddress serializes a NetAddress to w depending on the protocol
# version and whether or not the timestamp is included per ts.  Some messages
# like version do not include the timestamp.
def write_netaddress(s, pver, na, ts):
    pass
