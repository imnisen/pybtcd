from .common import *


class MsgReject(Message):
    def __init__(self, cmd=None, code=None, reason=None, hash=None):
        """

        :param Commands cmd:
        :param RejectCode code:
        :param string reason:
        :param chainhash.Hashhash:
        """
        # Cmd is the command for the message which was rejected such as
        # as CmdBlock or CmdTx.  This can be obtained from the Command function
        # of a Message.
        self.cmd = cmd or Commands.EMPTY

        # RejectCode is a code indicating why the command was rejected.  It
        # is encoded as a uint8 on the wire.
        self.code = code or RejectCode.EMPTY

        # Reason is a human-readable string with specific details (over and
        # above the reject code) about why the command was rejected.
        self.reason = reason or ""

        # Hash identifies a specific block or transaction that was rejected
        # and therefore only applies the MsgBlock and MsgTx messages.
        self.hash = hash or Hash()

    def __eq__(self, other):
        return self.cmd == other.cmd and \
               self.code == other.code and \
               self.reason == other.reason and \
               self.hash == other.hash

    def btc_decode(self, s, pver, message_encoding):
        if pver < RejectVersion:
            raise NotSupportBelowRejectVersionMsgErr

        # read message
        self.cmd = Commands.from_string(read_var_string(s, pver))

        # read ccode
        self.code = read_element(s, "RejectCode")

        # read reson
        self.reason = read_var_string(s, pver)

        # read data
        # CmdBlock and CmdTx messages have an additional hash field that
        # identifies the specific block or transaction.
        if self.cmd in (Commands.CmdBlock, Commands.CmdTx):
            self.hash = read_element(s, "chainhash.Hash")

        return

    def btc_encode(self, s, pver, message_encoding):
        if pver < RejectVersion:
            raise NotSupportBelowRejectVersionMsgErr

        # write message
        write_var_string(s, pver, str(self.cmd))

        # write ccode
        write_element(s, "RejectCode", self.code)

        # write reason
        write_var_string(s, pver, self.reason)

        # write data
        if self.cmd in (Commands.CmdBlock, Commands.CmdTx):
            write_element(s, "chainhash.Hash", self.hash)

        return

    def command(self) -> str:
        return Commands.CmdReject

    def max_payload_length(self, pver: int) -> int:
        # The reject message did not exist before protocol version
        # RejectVersion.
        if pver > RejectVersion:
            return MaxMessagePayload
        return 0
