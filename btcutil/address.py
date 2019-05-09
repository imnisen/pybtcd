from enum import Enum
import btcec
import chaincfg
from .error import *
import copy


# UnsupportedWitnessVerError describes an error where a segwit address being
# decoded has an unsupported witness version.
class UnsupportedWitnessVerError(Exception):
    def __init__(self, data=None):
        self.data = data

    def __str__(self):
        return "unsupported witness version: " + str(self.data)


# UnsupportedWitnessProgLenError describes an error where a segwit address
# being decoded has an unsupported witness program length.
class UnsupportedWitnessProgLenError(Exception):
    def __init__(self, data=None):
        self.data = data

    def __str__(self):
        return "unsupported witness program length: " + str(self.data)


# Address is an interface type for any type of destination a transaction
# output may spend to.  This includes pay-to-pubkey (P2PK), pay-to-pubkey-hash
# (P2PKH), and pay-to-script-hash (P2SH).  Address is designed to be generic
# enough that other kinds of addresses may be added in the future without
# changing the decoding and encoding API.
class Address:
    # String returns the string encoding of the transaction output
    # destination.
    #
    # Please note that String differs subtly from EncodeAddress: String
    # will return the value as a string without any conversion, while
    # EncodeAddress may convert destination types (for example,
    # converting pubkeys to P2PKH addresses) before encoding as a
    # payment address string.
    def __str__(self):
        pass

    # EncodeAddress returns the string encoding of the payment address
    # associated with the Address value.  See the comment on String
    # for how this method differs from String.
    def encode_address(self):
        pass

    # ScriptAddress returns the raw bytes of the address to be used
    # when inserting the address into a txout's script.
    def script_address(self):
        pass

    # IsForNet returns whether or not the address is associated with the
    # passed bitcoin network.
    def is_for_net(self, net: chaincfg.Params):
        pass

        # @classmethod
        # def new_from_params(cls, pk_hash, net):
        #     pass


# AddressPubKeyHash is an Address for a pay-to-pubkey-hash (P2PKH)
# transaction.
class AddressPubKeyHash(Address):
    def __init__(self, hash, net_id):
        # TOCHECK here hash use []byte or Hash() type
        self.hash = hash
        self.net_id = net_id

    def __eq__(self, other):
        return self.hash == other.hash and \
               self.net_id == other.net_id

    # EncodeAddress returns the string encoding of a pay-to-pubkey-hash
    # address.  Part of the Address interface.
    def encode_address(self):
        return encode_address(self.hash, self.net_id)

    # ScriptAddress returns the bytes to be included in a txout script to pay
    # to a pubkey hash.  Part of the Address interface.
    def script_address(self):
        return self.hash

    # IsForNet returns whether or not the pay-to-pubkey-hash address is associated
    # with the passed bitcoin network.
    def is_for_net(self, net: chaincfg.Params):
        return self.net_id == net.pub_key_hash_addr_id

    def __str__(self):
        return self.encode_address()

    # Hash160 returns the underlying array of the pubkey hash.  This can be useful
    # when an array is more appropiate than a slice (for example, when used as map
    # keys).
    def hash160(self):
        return self.hash


def new_address_pub_key_hash(pk_hash, net):
    """

    :param []byte pk_hash:
    :param chaincfg.Params net:
    :return:
    """
    if len(pk_hash) != 20:
        raise PubKeyHashSizeErr
    return AddressPubKeyHash(hash=copy.deepcopy(pk_hash), net_id=net.pub_key_hash_addr_id)


# AddressScriptHash is an Address for a pay-to-script-hash (P2SH)
# transaction.
class AddressScriptHash(Address):
    def __init__(self, hash, net_id):
        self.hash = hash
        self.net_id = net_id

    def __eq__(self, other):
        return self.hash == other.hash and self.net_id == other.net_id

    # EncodeAddress returns the string encoding of a pay-to-script-hash
    # address.  Part of the Address interface.
    def encode_address(self):
        return encode_address(self.hash, self.net_id)

    # ScriptAddress returns the bytes to be included in a txout script to pay
    # to a script hash.  Part of the Address interface.
    def script_address(self):
        return self.hash

    # IsForNet returns whether or not the pay-to-script-hash address is associated
    # with the passed bitcoin network.
    def is_for_net(self, net: chaincfg.Params):
        return self.net_id == net.script_hash_addr_id

    def __str__(self):
        return self.encode_address()

    # Hash160 returns the underlying array of the script hash.  This can be useful
    # when an array is more appropiate than a slice (for example, when used as map
    # keys).
    def hash160(self):
        return self.hash


def new_address_script_hash_from_hash(script_hash, net):
    """

    :param []byte script_hash:
    :param chaincfg.Params net:
    :return:
    """
    if len(script_hash) != 20:
        raise ScriptHashSizeErr

    return AddressScriptHash(hash=copy.deepcopy(script_hash), net_id=net.script_hash_addr_id)


# PubKeyFormat describes what format to use for a pay-to-pubkey address.
class PubKeyFormat(Enum):
    # PKFUncompressed indicates the pay-to-pubkey address format is an
    # uncompressed public key.
    PKFUncompressed = 0

    # PKFCompressed indicates the pay-to-pubkey address format is a
    # compressed public key.
    PKFCompressed = 1

    # PKFHybrid indicates the pay-to-pubkey address format is a hybrid
    # public key.
    PKFHybrid = 2


class AddressPubKey(Address):
    def __init__(self, pub_key_format, pub_key, pub_key_hash_id):
        """

        :param PubKeyFormat pub_key_format:
        :param PublicKey pub_key:
        :param byte pub_key_hash_id:
        """
        self.pub_key_format = pub_key_format
        self.pub_key = pub_key
        self.pub_key_hash_id = pub_key_hash_id

    def __eq__(self, other):
        return self.pub_key_format == other.pub_key_format and \
               self.pub_key == other.pub_key and \
               self.pub_key_hash_id == other.pub_key_hash_id

    # serialize returns the serialization of the public key according to the
    # format associated with the address.
    def serialize(self):
        if self.pub_key_format == PubKeyFormat.PKFUncompressed:
            return self.pub_key.serialize_uncompressed()
        elif self.pub_key_format == PubKeyFormat.PKFCompressed:
            return self.pub_key.serialize_compressed()
        elif self.pub_key_format == PubKeyFormat.PKFHybrid:
            return self.pub_key.serialize_hybrid()
        else:
            # should not go here
            return

    # EncodeAddress returns the string encoding of the public key as a
    # pay-to-pubkey-hash.  Note that the public key format (uncompressed,
    # compressed, etc) will change the resulting address.  This is expected since
    # pay-to-pubkey-hash is a hash of the serialized public key which obviously
    # differs with the format.  At the time of this writing, most Bitcoin addresses
    # are pay-to-pubkey-hash constructed from the uncompressed public key.
    #
    # Part of the Address interface.
    def encode_address(self):
        return encode_address(btcec.hash160(self.serialize()), self.pub_key_hash_id)

    # ScriptAddress returns the bytes to be included in a txout script to pay
    # to a public key.  Setting the public key format will affect the output of
    # this function accordingly.  Part of the Address interface.
    def script_address(self):
        return self.serialize()

    # IsForNet returns whether or not the pay-to-pubkey address is associated
    # with the passed bitcoin network.
    def is_for_net(self, net: chaincfg.Params):
        return self.pub_key_hash_id == net.pub_key_hash_addr_id

    # String returns the hex-encoded human-readable string for the pay-to-pubkey
    # address.  This is not the same as calling EncodeAddress.
    def __str__(self):
        return btcec.bytes_to_hex(self.serialize())

    # Format returns the format (uncompressed, compressed, etc) of the
    # pay-to-pubkey address.
    def get_format(self):
        return self.pub_key_format

    # SetFormat sets the format (uncompressed, compressed, etc) of the
    # pay-to-pubkey address.
    def set_format(self, pk_format: PubKeyFormat):
        self.pub_key_format = pk_format
        return

    # AddressPubKeyHash returns the pay-to-pubkey address converted to a
    # pay-to-pubkey-hash address.  Note that the public key format (uncompressed,
    # compressed, etc) will change the resulting address.  This is expected since
    # pay-to-pubkey-hash is a hash of the serialized public key which obviously
    # differs with the format.  At the time of this writing, most Bitcoin addresses
    # are pay-to-pubkey-hash constructed from the uncompressed public key.
    def address_pub_key_hash(self):
        return AddressPubKeyHash(hash=btcec.hash160(self.serialize()),
                                 net_id=self.pub_key_hash_id)

    # PubKey returns the underlying public key for the address.
    def get_pub_key(self):
        return self.pub_key


# NewAddressPubKey returns a new AddressPubKey which represents a pay-to-pubkey
# address.  The serializedPubKey parameter must be a valid pubkey and can be
# uncompressed, compressed, or hybrid.
def new_address_pub_key(serialized_pub_key: bytes, net: chaincfg.Params):
    """

    :param []byte serialized_pub_key:
    :param chaincfg.Params net:
    :return:
    """
    pub_key = btcec.parse_pub_key(serialized_pub_key, btcec.s256())

    # Set the format of the pubkey.  This probably should be returned
    # from btcec, but do it here to avoid API churn.  We already know the
    # pubkey is valid since it parsed above, so it's safe to simply examine
    # the leading byte to get the format
    if serialized_pub_key[0] in (0x02, 0x03):
        pk_format = PubKeyFormat.PKFCompressed
    elif serialized_pub_key[0] in (0x06, 0x07):
        pk_format = PubKeyFormat.PKFHybrid
    else:
        pk_format = PubKeyFormat.PKFUncompressed
    return AddressPubKey(pub_key_format=pk_format,
                         pub_key=pub_key,
                         pub_key_hash_id=net.pub_key_hash_addr_id)


class AddressWitnessPubKeyHash(Address):
    def __init__(self, hrp, witness_version, witness_program):
        """

        :param string hrp:
        :param byte witness_version:
        :param [20]byte witness_program:
        """
        self.hrp = hrp
        self.witness_version = witness_version
        self.witness_program = witness_program


def new_address_witness_pub_key_hash(witness_prog, net):
    """

    :param []byte witness_prog:
    :param net:
    :return:
    """
    pass


class AddressWitnessScriptHash(Address):
    def __init__(self, hrp, witness_version, witness_program):
        """

        :param string hrp:
        :param byte witness_version:
        :param [20]byte witness_program:
        """
        self.hrp = hrp
        self.witness_version = witness_version
        self.witness_program = witness_program


def new_address_witness_script_hash(witness_prog, net):
    """

    :param []byte witness_prog:
    :param net:
    :return:
    """
    pass


# TODO
def encode_address(hash160: bytes, net_id: int):
    pass
