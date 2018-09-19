from .netaddress import *

# MaxAddrPerMsg is the maximum number of addresses that can be in a single
# bitcoin addr message (MsgAddr).
MaxAddrPerMsg = 1000



class MsgAddr(Message):
    def __init__(self, addr_list=None):
        self.addr_list = addr_list or []

    def __eq__(self, other):
        if type(other) is MsgAddr and \
                        len(self.addr_list) == len(other.addr_list):
            all_equal = True
            for i, m in enumerate(self.addr_list):
                if m != other.addr_list[i]:
                    all_equal = False
            return all_equal
        else:
            return False

    def btc_decode(self, s, pver, message_encoding):
        count = read_var_int(s, pver)
        if count > MaxAddrPerMsg:
            raise MsgAddrTooManyErr

        for i in range(count):
            na = read_netaddress(s, pver, True)
            self.add_address(na)
        return

    # TOCHECK
    # https://en.bitcoin.it/wiki/Protocol_documentation#addr
    # Why doesn't check  version 31402, and not timestamp, don't relay to others
    def btc_encode(self, s, pver, message_encoding):
        count = len(self.addr_list)
        if pver < MultipleAddressVersion and count > 1:
            raise MsgAddrTooManyErr

        if count > MaxAddrPerMsg:
            raise MsgAddrTooManyErr

        write_var_int(s, pver, count)
        for na in self.addr_list:
            write_netaddress(s, pver, na, True)
        return

    def command(self) -> str:
        return Commands.CmdAddr

    def max_payload_length(self, pver: int) -> int:
        if pver < MultipleAddressVersion:
            return MaxVarIntPayload + max_netaddress_payload(pver)
        else:
            return MaxVarIntPayload + MaxAddrPerMsg * max_netaddress_payload(pver)

    def add_address(self, na: NetAddress):
        """AddAddress adds a known active peer to the message."""
        if len(self.addr_list) + 1 > MaxAddrPerMsg:
            raise MsgAddrTooManyErr

        self.addr_list.append(na)
        return

    def add_addresses(self, nas: list):
        """AddAddresses adds multiple known active peers to the message."""
        for na in nas:
            self.add_address(na)
        return

    def clear_addresses(self):
        """ClearAddresses removes all addresses from the message."""
        self.addr_list = []
        return
