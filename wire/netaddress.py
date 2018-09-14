# Refer to https://en.bitcoin.it/wiki/Protocol_documentation#Network_address
import time
from .protocol import *
from .common import *
import ipaddress


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
        # alway convert to ipv6
        if type(ip) is ipaddress.IPv4Address:
            self.ip = ipv4_mapped_ipv6(ip)
        elif type(ip) is ipaddress.IPv6Address:
            self.ip = ip
        elif not ip:
            self.ip = None
        else:
            raise Exception('pass a ipaddress.IPv4Address or ipaddress.IPv6Address class ip')


        # Port the peer is using.  This is encoded in big endian on the wire
        # which differs from most everything else.
        self.port = port

    def has_service(self, service: ServiceFlag) -> bool:
        # TOCHECK  I don't know what the source code `na.Services&service == service` mean?
        # So here is my understand
        return (self.services.b & service.b) == service.b

    def add_service(self, service: ServiceFlag):
        self.services.b |= service.b

    def __eq__(self, other):
        return self.timestamp == other.timestamp \
            and self.services == other.services \
            and self.ip == other.ip \
            and self.port == other.port


########################################
# WTF rfc4038 ipv4-mapped-ipv6 or ipv4-compatible-ipv6[deprecated], or rfc3056 6to4 address !
# https://forums.he.net/index.php?topic=635.0
# https://forums.he.net/index.php?topic=635.0
# https://tools.ietf.org/html/rfc3056#section-2
# https://tools.ietf.org/html/rfc4291#section-2.5.5
# https://tools.ietf.org/html/rfc4038
def ipv4_mapped_ipv6(ipv4: ipaddress.IPv4Address) -> ipaddress.IPv6Address:
    return ipaddress.IPv6Address(bytes(10)+ bytes([0xff]*2) + ipv4.packed)

# def ipv4_compatible_ipv6(ipv4: ipaddress.IPv4Address) -> ipaddress.IPv6Address:
#     # convert ip4 to rfc 3056 IPv6 6to4 address
#     # http://tools.ietf.org/html/rfc3056#section-2
#     prefix6to4 = int(ipaddress.IPv6Address("2002::"))
#     return ipaddress.IPv6Address(prefix6to4 | (int(ipv4) << 80))
#
# def ipv6_to_ipv4_mapped(ipv6: ipaddress.IPv6Address) -> ipaddress.IPv4Address:
#     return ipv6.ipv4_mapped
#
# def ipv6_to_ipv4(ipv6: ipaddress.IPv6Address) -> ipaddress.IPv4Address:
#     return ipv6.sixtofour
########################################


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
    if ip:
        ip = ipaddress.ip_address(ip)

    port = read_variable_bytes_as_integer(s, 8, BigEndian)
    return NetAddress(services=services,
                      ip=ip,
                      port=port,
                      timestamp=timestamp)


# writeNetAddress serializes a NetAddress to w depending on the protocol
# version and whether or not the timestamp is included per ts.  Some messages
# like version do not include the timestamp.
def write_netaddress(s, pver, na, ts):
    if ts and pver >= NetAddressTimeVersion:
        # print('write ts')
        write_element(s, "uint32", na.timestamp)

    write_element(s, "ServiceFlag", na.services)

    # Ensure to always write 16 bytes even if the ip is nil.
    ip = bytearray(16)
    # refer to https://stackoverflow.com/questions/19750929/converting-ipv4-address-to-a-hex-ipv6-address-in-python
    if na.ip:
        ip = na.ip.packed
    write_element(s, "[16]byte", ip)

    write_variable_bytes_from_integer(s, 2, na.port, BigEndian)
    return

