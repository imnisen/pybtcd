import time
from .protocol import *
# import ipaddress

class NetAddress:
    def __init__(self, timestamp:int,  services: ServiceFlag, ip, port:int):

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
        self.services |=  service


def new_netaddres(addr, services: ServiceFlag) -> NetAddress:
    return NetAddress(int(time.time()), services, addr.ip, addr.port)

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
def read_netaddress():
    # TOADD
    pass

# writeNetAddress serializes a NetAddress to w depending on the protocol
# version and whether or not the timestamp is included per ts.  Some messages
# like version do not include the timestamp.
def write_netaddress():
    # TOADD
    pass