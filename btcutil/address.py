from enum import Enum


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
    def is_for_net(self):
        pass

    @classmethod
    def new_from_params(cls, pk_hash, net):
        pass


class AddressPubKeyHash(Address):
    def __init__(self, hash, net_id):
        self.hash = hash
        self.net_id = net_id



def new_address_pubkey_hash(pk_hash, net):
    pass


class AddressScriptHash(Address):
    def __init__(self, hash, net_id):
        self.hash = hash
        self.net_id = net_id


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
    def __init__(self, pubkey_format, pubkey, pubkey_hash_id):
        """

        :param PubKeyFormat pubkey_format:
        :param TODO pubkey:
        :param byte pubkey_hash_id:
        """
        self.pubkey_format = pubkey_format
        self.pubkey = pubkey
        self.pubkey_hash_id = pubkey_hash_id

# NewAddressPubKey returns a new AddressPubKey which represents a pay-to-pubkey
# address.  The serializedPubKey parameter must be a valid pubkey and can be
# uncompressed, compressed, or hybrid.
def new_address_pub_key(serialized_pub_key, net):
    pass



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
