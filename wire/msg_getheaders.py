from .common import *
from .msg_getblocks import MaxBlockLocatorsPerMsg


class MsgGetHeaders(Message):
    def __init__(self, protocol_version=None, block_locator_hashes=None, hash_stop=None):
        self.protocol_version = protocol_version or ProtocolVersion
        self.block_locator_hashes = block_locator_hashes or []
        self.hash_stop = hash_stop or Hash()

    def __eq__(self, other):
        if type(other) is MsgGetHeaders:
            if self.protocol_version == other.protocol_version and self.hash_stop == other.hash_stop and len(
                    self.block_locator_hashes) == len(other.block_locator_hashes):
                all_same = True
                for i, x in enumerate(self.block_locator_hashes):
                    if x != other.block_locator_hashes[i]:
                        all_same = False
                return all_same
            else:
                return False
        else:
            return False

    def add_block_locator_hash(self, h: Hash):
        """AddBlockLocatorHash adds a new block locator hash to the message."""
        if len(self.block_locator_hashes) + 1 > MaxBlockLocatorsPerMsg:
            raise MaxBlockLocatorsPerMsgErr
        self.block_locator_hashes.append(h)

    def btc_decode(self, s, pver, message_encoding):
        self.protocol_version = read_element(s, "uint32")
        count = read_var_int(s, pver)
        if count > MaxBlockLocatorsPerMsg:
            raise MaxBlockLocatorsPerMsgErr

        for _ in range(count):
            h = read_element(s, "chainhash.Hash")
            self.add_block_locator_hash(h)

        self.hash_stop = read_element(s, "chainhash.Hash")

    def btc_encode(self, s, pver, message_encoding):
        write_element(s, "uint32", self.protocol_version)

        count = len(self.block_locator_hashes)
        if count > MaxBlockLocatorsPerMsg:
            raise MaxBlockLocatorsPerMsgErr

        write_var_int(s, pver, count)

        for locator in self.block_locator_hashes:
            write_element(s, "chainhash.Hash", locator)

        write_element(s, "chainhash.Hash", self.hash_stop)

    def command(self):
        return Commands.CmdGetHeaders

    def max_payload_length(self, pver: int):
        # Protocol version 4 bytes + num hashes (varInt) + max block locator
        # hashes + hash stop.
        return 4 + MaxVarIntPayload + (MaxBlockLocatorsPerMsg * HashSize) + HashSize
