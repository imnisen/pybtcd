import io
from .common import *

# MsgAlert contains a payload and a signature:
#
#        ===============================================
#        |   Field         |   Data Type   |   Size    |
#        ===============================================
#        |   payload       |   []uchar     |   ?       |
#        -----------------------------------------------
#        |   signature     |   []uchar     |   ?       |
#        -----------------------------------------------
#
# Here payload is an Alert serialized into a byte array to ensure that
# versions using incompatible alert formats can still relay
# alerts among one another.
#
# An Alert is the payload deserialized as follows:
#
#        ===============================================
#        |   Field         |   Data Type   |   Size    |
#        ===============================================
#        |   Version       |   int32       |   4       |
#        -----------------------------------------------
#        |   RelayUntil    |   int64       |   8       |
#        -----------------------------------------------
#        |   Expiration    |   int64       |   8       |
#        -----------------------------------------------
#        |   ID            |   int32       |   4       |
#        -----------------------------------------------
#        |   Cancel        |   int32       |   4       |
#        -----------------------------------------------
#        |   SetCancel     |   set<int32>  |   ?       |
#        -----------------------------------------------
#        |   MinVer        |   int32       |   4       |
#        -----------------------------------------------
#        |   MaxVer        |   int32       |   4       |
#        -----------------------------------------------
#        |   SetSubVer     |   set<string> |   ?       |
#        -----------------------------------------------
#        |   Priority      |   int32       |   4       |
#        -----------------------------------------------
#        |   Comment       |   string      |   ?       |
#        -----------------------------------------------
#        |   StatusBar     |   string      |   ?       |
#        -----------------------------------------------
#        |   Reserved      |   string      |   ?       |
#        -----------------------------------------------
#        |   Total  (Fixed)                |   45      |
#        -----------------------------------------------
#
# NOTE:
#      * string is a VarString i.e VarInt length followed by the string itself
#      * set<string> is a VarInt followed by as many number of strings
#      * set<int32> is a VarInt followed by as many number of ints
#      * fixedAlertSize = 40 + 5*min(VarInt)  = 40 + 5*1 = 45
#
# Now we can define bounds on Alert size, SetCancel and SetSubVer

# Fixed size of the alert payload
fixedAlertSize = 45

# maxSignatureSize is the max size of an ECDSA signature.
# NOTE: Since this size is fixed and < 255, the size of VarInt required = 1.
maxSignatureSize = 72

# TOCHECK  maxAlertSize doesn't come from when VarInt->min, SignatureSize->min? not max.

# maxAlertSize is the maximum size an alert.
#
# MessagePayload = VarInt(Alert) + Alert + VarInt(Signature) + Signature
# MaxMessagePayload = maxAlertSize + max(VarInt) + maxSignatureSize + 1
maxAlertSize = MaxMessagePayload - maxSignatureSize - MaxVarIntPayload - 1

# maxCountSetCancel is the maximum number of cancel IDs that could possibly
# fit into a maximum size alert.
#
# maxAlertSize = fixedAlertSize + max(SetCancel) + max(SetSubVer) + 3*(string)
# for caculating maximum number of cancel IDs, set all other var  sizes to 0
# maxAlertSize = fixedAlertSize + (MaxVarIntPayload-1) + x*sizeOf(int32)
# x = (maxAlertSize - fixedAlertSize - MaxVarIntPayload + 1) / 4
maxCountSetCancel = (maxAlertSize - fixedAlertSize - MaxVarIntPayload + 1) / 4

# maxCountSetSubVer is the maximum number of subversions that could possibly
# fit into a maximum size alert.
#
# maxAlertSize = fixedAlertSize + max(SetCancel) + max(SetSubVer) + 3*(string)
# for caculating maximum number of subversions, set all other var sizes to 0
# maxAlertSize = fixedAlertSize + (MaxVarIntPayload-1) + x*sizeOf(string)
# x = (maxAlertSize - fixedAlertSize - MaxVarIntPayload + 1) / sizeOf(string)
# subversion would typically be something like "/Satoshi:0.7.2/" (15 bytes)
# so assuming < 255 bytes, sizeOf(string) = sizeOf(uint8) + 255 = 256
maxCountSetSubVer = (maxAlertSize - fixedAlertSize - MaxVarIntPayload + 1) / 256


class Alert:
    def __init__(self, version=None, relay_until=None, expiration=None, id=None,
                 cancel=None, set_cancel=None, min_ver=None, max_ver=None,
                 set_sub_ver=None, priority=None, comment=None, status_bar=None, reserved=None):
        """

        :param int32 version:
        :param int64 relay_until:
        :param int64 expiration:
        :param int32 id:
        :param int32 cancel:
        :param []int32 set_cancel:
        :param int32 min_ver:
        :param int32 max_ver:
        :param []string set_sub_ver:
        :param int32 priority:
        :param string comment:
        :param string status_bar:
        :param string reserved:
        """
        self.version = version or 0
        self.relay_until = relay_until or 0
        self.expiration = expiration or 0
        self.id = id or 0
        self.cancel = cancel or 0
        self.set_cancel = set_cancel or []
        self.min_ver = min_ver or 0
        self.max_ver = max_ver or 0
        self.set_sub_ver = set_sub_ver or []
        self.priority = priority or 0
        self.comment = comment or ""
        self.status_bar = status_bar or ""
        self.reserved = reserved or ""

    def __eq__(self, other):
        return self.version == other.version and \
               self.relay_until == other.relay_until and \
               self.expiration == other.expiration and \
               self.id == other.id and \
               self.cancel == other.cancel and \
               self.set_cancel == other.set_cancel and \
               self.min_ver == other.min_ver and \
               self.max_ver == other.max_ver and \
               self.set_sub_ver == other.set_sub_ver and \
               self.priority == other.priority and \
               self.comment == other.comment and \
               self.status_bar == other.status_bar and \
               self.reserved == other.reserved

    # TOCHECK should these two method name to btc_encode and btc_decode?
    def serialize(self, s, pver):
        write_element(s, "int32", self.version)
        write_element(s, "int64", self.relay_until)
        write_element(s, "int64", self.expiration)
        write_element(s, "int32", self.id)
        write_element(s, "int32", self.cancel)

        # write set_cancel
        count = len(self.set_cancel)
        if count > maxCountSetCancel:
            raise MaxCountSetCancelMsgErr

        write_var_int(s, pver, count)
        for each in self.set_cancel:
            write_element(s, "int32", each)

        write_element(s, "int32", self.min_ver)
        write_element(s, "int32", self.max_ver)

        # write set_sub_ver
        count = len(self.set_sub_ver)
        if count > maxCountSetSubVer:
            raise MaxCountSetSubVerlMsgErr

        write_var_int(s, pver, count)
        for each in self.set_sub_ver:
            write_var_string(s, pver, each)

        write_element(s, "int32", self.priority)
        write_var_string(s, pver, self.comment)
        write_var_string(s, pver, self.status_bar)
        write_var_string(s, pver, self.reserved)
        return

    def deserialize(self, s, pver):
        self.version = read_element(s, "int32")
        self.relay_until = read_element(s, "int64")
        self.expiration = read_element(s, "int64")
        self.id = read_element(s, "int32")
        self.cancel = read_element(s, "int32")

        # read set_cancel
        count = read_var_int(s, pver)
        if count > maxCountSetCancel:
            raise MaxCountSetCancelMsgErr

        for _ in range(count):
            self.set_cancel.append(read_element(s, "int32"))

        self.min_ver = read_element(s, "int32")
        self.max_ver = read_element(s, "int32")

        # read set_sub_ver
        count = read_var_int(s, pver)
        if count > maxCountSetSubVer:
            raise MaxCountSetSubVerlMsgErr

        for _ in range(count):
            self.set_sub_ver.append(read_var_string(s, pver))

        self.priority = read_element(s, "int32")
        self.comment = read_var_string(s, pver)
        self.status_bar = read_var_string(s, pver)
        self.reserved = read_var_string(s, pver)
        return

    @classmethod
    def from_payload(cls, serialized_payload, pver):
        alert = cls()
        s = io.BytesIO(serialized_payload)
        alert.deserialize(s, pver)
        return alert


class MsgAlert(Message):
    def __init__(self, serialized_payload=None, signature=None, payload=None):
        """

        :param []byte serialized_payload:
        :param []byte signature:
        :param Alert payload:
        """

        # SerializedPayload is the alert payload serialized as a string so that the
        # version can change but the Alert can still be passed on by older
        # clients.
        self.serialized_payload = serialized_payload or bytes()

        # Signature is the ECDSA signature of the message.
        self.signature = signature or bytes()

        # Deserialized Payload
        self.payload = payload or Alert()

    def __eq__(self, other):
        return self.serialized_payload == other.serialized_payload and \
               self.signature == other.signature and \
               self.payload == other.payload

    def btc_decode(self, s, pver, message_encoding):
        self.serialized_payload = read_var_bytes(s, pver, MaxMessagePayload, "alert serialized payload")

        self.payload = Alert.from_payload(self.serialized_payload, pver)

        self.signature = read_var_bytes(s, pver, MaxMessagePayload, "alert signature")

    def btc_encode(self, s, pver, message_encoding):
        if self.payload:
            try:
                buf = io.BytesIO()
                self.payload.serialize(buf, pver)
                serialized_payload = buf.getvalue()
            except Exception as e:
                serialized_payload = self.serialized_payload
        else:
            serialized_payload = self.serialized_payload

        if len(serialized_payload) == 0:
            raise AlertSerializedPayloadEmptyMsgErr

        write_var_bytes(s, pver, serialized_payload)

        write_var_bytes(s, pver, self.signature)

    def command(self) -> str:
        return Commands.CmdAlert

    def max_payload_length(self, pver: int) -> int:
        return MaxMessagePayload
