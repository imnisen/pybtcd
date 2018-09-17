from enum import Enum

# ProtocolVersion is the latest protocol version this package supports.
ProtocolVersion = 70013

# MultipleAddressVersion is the protocol version which added multiple
# addresses per message (pver >= MultipleAddressVersion).
MultipleAddressVersion = 209

# NetAddressTimeVersion is the protocol version which added the
# timestamp field (pver >= NetAddressTimeVersion).
NetAddressTimeVersion = 31402

# BIP0031Version is the protocol version AFTER which a pong message
# and nonce field in ping were added (pver > BIP0031Version).
BIP0031Version = 60000

# BIP0035Version is the protocol version which added the mempool
# message (pver >= BIP0035Version).
BIP0035Version = 60002

# BIP0037Version is the protocol version which added new connection
# bloom filtering related messages and extended the version message
# with a relay flag (pver >= BIP0037Version).
BIP0037Version = 70001


# BitcoinNet represents which bitcoin network a message belongs to.
class BitcoinNet(Enum):
    # MainNet represents the main bitcoin network.
    MainNet = (0xd9b4bef9, "MainNet")

    # TestNet represents the regression test network.
    TestNet = (0xdab5bffa, "TestNet")

    # TestNet3 represents the test network (version 3).
    TestNet3 = (0x0709110b, "TestNet3")

    # SimNet represents the simulation test network.
    SimNet = (0x12141c16, "SimNet")

    def __str__(self):
        return self.value[1]

    @classmethod
    def from_string(cls, s):
        for bitcoin_net in cls:
            if bitcoin_net.value[1] == s:
                return bitcoin_net
        raise ValueError(cls.__name__ + ' has no value matching "' + s + '"')


# Enumerations support iteration, in definition order
# TODO Change this
class ServiceFlag(Enum):
    EMPTY = (0, "")

    # SFNodeNetwork is a flag used to indicate a peer is a full node.
    SFNodeNetwork = (1, "SFNodeNetwork")

    # SFNodeGetUTXO is a flag used to indicate a peer supports the
    # getutxos and utxos commands (BIP0064).
    SFNodeGetUTXO = (1 << 2, "SFNodeGetUTXO")

    # SFNodeBloom is a flag used to indicate a peer supports bloom
    # filtering.
    SFNodeBloom = (1 << 3, "SFNodeBloom")

    # SFNodeWitness is a flag used to indicate a peer supports blocks
    # and transactions including witness data (BIP0144).
    SFNodeWitness = (1 << 4, "SFNodeWitness")

    # SFNodeXthin is a flag used to indicate a peer supports xthin blocks.
    SFNodeXthin = (1 << 5, "SFNodeXthin")

    # SFNodeBit5 is a flag used to indicate a peer supports a service
    # defined by bit 5.
    SFNodeBit5 = (1 << 6, "SFNodeBit5")

    # SFNodeCF is a flag used to indicate a peer supports committed
    # filters (CFs).
    SFNodeCF = (1 << 7, "SFNodeCF")

    # SFNode2X is a flag used to indicate a peer is running the Segwit2X
    # software.
    SFNode2X = (1 << 8, "SFNode2X")

    def __str__(self):
        return self.value[1]

    @classmethod
    def from_int(cls, i):
        for flagService in cls:
            if flagService.value[0] == i:
                return flagService
        raise ValueError(cls.__name__ + ' has no value matching "' + str(i) + '"')


class Services:
    def __init__(self, service=None):
        """Try to make caller simple"""
        if type(service) is ServiceFlag:
            self._data = service.value[0]
        elif type(service) is int:
            self._data = service
        elif type(service) is Services:
            self._data = service.value
        else:
            self._data = 0

    def add_service(self, service: ServiceFlag):
        self._data |= service.value[0]

    def has_service(self, service: ServiceFlag):
        return (self._data & service.value[0]) == service.value[0]

    def __eq__(self, other):
        if type(other) is int:
            return self._data == other
        elif type(other) is ServiceFlag:
            return self._data == other.value[0]
        elif type(other) is Services:
            return self._data == other.value
        else:
            raise Exception('Error compare')

    @property
    def value(self):
        return self._data
