from enum import Enum
from .opcode import *
from .script import *
from .script_builder import *
from btcutil.address import *

# MaxDataCarrierSize is the maximum number of bytes allowed in pushed
# data to be considered a nulldata transaction
MaxDataCarrierSize = 80


class ScriptClass(Enum):
    NonStandardTy = (0, "nonstandard")  # None of the recognized forms.
    PubKeyTy = (1, "pubkey")  # Pay pubkey.
    PubKeyHashTy = (2, "pubkeyhash")  # Pay pubkey hash.
    WitnessV0PubKeyHashTy = (3, "witness_v0_keyhash")  # Pay witness pubkey hash.
    ScriptHashTy = (5, "scripthash")  # Pay to script hash.
    WitnessV0ScriptHashTy = (6, "witness_v0_scripthash")  # Pay to witness script hash.
    MultiSigTy = (6, "multisig")  # Multi signature.
    NullDataTy = (7, "nulldata")  # Empty data-only (provably prunable).

    def __str__(self):
        return self.value[1]

    @classmethod
    def from_int(cls, i):
        for flagService in cls:
            if flagService.value[0] == i:
                return flagService
        raise ValueError(cls.__name__ + ' has no value matching "' + str(i) + '"')


# isPubkey returns true if the script passed is a pay-to-pubkey transaction,
# false otherwise.
def is_pub_key(pops) -> bool:
    # Valid pub_keys are either 33 or 65 bytes.
    return len(pops) == 2 and (len(pops[0].data) == 33 or len(pops[0].data) == 65) and \
           pops[1].opcode.value == OP_CHECKSIG


# isPubkeyHash returns true if the script passed is a pay-to-pub_key-hash
# transaction, false otherwise.
def is_pub_key_hash(pops) -> bool:
    return len(pops) == 5 and \
           pops[0].opcode.value == OP_DUP and \
           pops[1].opcode.value == OP_HASH160 and \
           pops[2].opcode.value == OP_DATA_20 and \
           pops[3].opcode.value == OP_EQUALVERIFY and \
           pops[4].opcode.value == OP_CHECKSIG




# isMultiSig returns true if the passed script is a multisig transaction, false
# otherwise.
def is_multi_sig(pops) -> bool:
    # The absolute minimum is 1 pubkey:
    # OP_0/OP_1-16 <pubkey> OP_1 OP_CHECKMULTISIG
    l = len(pops)
    if l < 4:
        return False

    if not is_small_int(pops[0]):
        return False

    if not is_small_int(pops[-2]):
        return False

    if pops[-1].opcode.value != OP_CHECKMULTISIG:
        return False

    # Verify the number of pubkeys specified matches the actual number
    # of pubkeys provided.
    if l - 2 - 1 != as_small_int(pops[-2].opcode):
        return False

    for pop in pops[1:-2]:
        # Valid pubkeys are either 33 or 65 bytes.
        if len(pop.data) != 33 and len(pop.data) != 65:
            return False

    return True


# isNullData returns true if the passed script is a null data transaction,
# false otherwise.
def is_null_data(pops) -> bool:
    l = len(pops)
    if l == 1 and pops[0].opcode.value == OP_RETURN:
        return True

    return l == 2 and (is_small_int(pops[1].opcode) or pops[1].opcode.value <= OP_PUSHDATA4) and \
           len(pops[1].data) <= MaxDataCarrierSize


# scriptType returns the type of the script being inspected from the known
# standard types.
def type_of_script(pops) -> ScriptClass:
    if is_pub_key(pops):
        return ScriptClass.PubKeyTy
    elif is_pub_key_hash(pops):
        return ScriptClass.PubKeyHashTy
    elif is_witness_pub_key_hash(pops):
        return ScriptClass.WitnessV0PubKeyHashTy
    elif is_script_hash(pops):
        return ScriptClass.ScriptHashTy
    elif is_witness_script_hash(pops):
        return ScriptClass.WitnessV0ScriptHashTy
    elif is_multi_sig(pops):
        return ScriptClass.MultiSigTy
    elif is_null_data(pops):
        return ScriptClass.NullDataTy
    return ScriptClass.NonStandardTy


def get_script_class(script: bytes):
    try:
        pops = parse_script(script)
        return type_of_script(pops)
    except:
        return ScriptClass.NonStandardTy


def get_expected_inputs(pops, klass: ScriptClass):
    if klass == ScriptClass.PubKeyTy:
        return 1
    if klass == ScriptClass.PubKeyHashTy:
        return 2
    if klass == ScriptClass.WitnessV0PubKeyHashTy:
        return 2
    if klass == ScriptClass.ScriptHashTy:
        # Not including script.  That is handled by the caller.
        return 1
    if klass == ScriptClass.WitnessV0ScriptHashTy:
        # Not including script.  That is handled by the caller.
        return 1
    if klass == ScriptClass.MultiSigTy:
        # Standard multisig has a push a small number for the number
        # of sigs and number of keys.  Check the first push instruction
        # to see how many arguments are expected. typeOfScript already
        # checked this so we know it'll be a small int.  Also, due to
        # the original bitcoind bug where OP_CHECKMULTISIG pops an
        # additional item from the stack, add an extra expected input
        # for the extra push that is required to compensate.
        return as_small_int(pops[0].opcode) + 1

    if klass == ScriptClass.NullDataTy:
        pass

    return -1


class ScriptInfo:
    def __init__(self, pk_script_class=None, num_inputs=None, expected_inputs=None, sig_ops=None):
        self.pk_script_class = pk_script_class or ScriptClass.from_int(0)
        self.num_inputs = num_inputs or 0
        self.expected_inputs = expected_inputs or 0
        self.sig_ops = sig_ops or 0


# TODO Rethink this
def cacl_script_info(sig_script, pk_script, witness, bip16: bool, segwit: bool):
    sig_pops = parse_script(sig_script)
    pk_pops = parse_script(pk_script)

    si = ScriptInfo()
    si.pk_script_class = type_of_script(pk_pops)

    # Can't have a signature script that doesn't just push data.
    if not is_push_only(sig_pops):
        desc = "signature script is not push only"
        raise ScriptError(ErrorCode.ErrNotPushOnly, desc=desc)

    si.expected_inputs = get_expected_inputs(pk_pops, si.pk_script_class)

    # Count sigops taking into account pay-to-script-hash.
    if si.pk_script_class == ScriptClass.ScriptHashTy and bip16 and not segwit:
        # The pay-to-hash-script is the final data push of the
        # signature script.
        script = sig_pops[-1]
        sh_pops = parse_script(script)
        sh_inputs = get_expected_inputs(sh_pops, type_of_script(sh_pops))

        if sh_inputs == -1:
            si.expected_inputs = -1
        else:
            si.expected_inputs += sh_inputs

        si.sig_ops = get_sig_op_count(sh_pops, precise=True)

        # All entries pushed to stack (or are OP_RESERVED and exec
        # will fail).
        si.num_inputs = len(sig_pops)

    # If segwit is active, and this is a regular p2wkh output, then we'll
    # treat the script as a p2pkh output in essence.
    elif si.pk_script_class == ScriptClass.WitnessV0PubKeyHashTy and segwit:
        si.sig_ops = get_witness_sig_op_count(sig_script, pk_script, witness)
        si.num_inputs = len(witness)

    # We'll attempt to detect the nested p2sh case so we can accurately
    # count the signature operations involved.
    elif si.pk_script_class == ScriptClass.ScriptHashTy and is_pops_witness_program(
            sig_script[1:]) and bip16 and segwit:
        # Extract the pushed witness program from the sigScript so we
        # can determine the number of expected inputs.
        pk_pops = parse_script(sig_script[1:])
        sh_inputs = get_expected_inputs(pk_pops, type_of_script(pk_pops))
        if sh_inputs == -1:
            si.expected_inputs = -1
        else:
            si.expected_inputs += sh_inputs

        si.sig_ops = get_witness_sig_op_count(sig_script, pk_script, witness)

        si.num_inputs = len(witness)
        si.num_inputs += len(sig_pops)

    # If segwit is active, and this is a p2wsh output, then we'll need to
    # examine the witness script to generate accurate script info.
    elif si.pk_script_class == ScriptClass.WitnessV0ScriptHashTy and segwit:
        # The witness script is the final element of the witness
        # stack.
        witness_script = witness[-1]
        pops = parse_script(witness_script)

        sh_inputs = get_expected_inputs(pops, type_of_script(pops))
        if sh_inputs == -1:
            si.expected_inputs = -1
        else:
            si.expected_inputs += sh_inputs

        si.sig_ops = get_witness_sig_op_count(sig_script, pk_script, witness)
        si.num_inputs = len(witness)
    else:
        si.sig_ops = get_sig_op_count(pk_pops, precise=True)

        # All entries pushed to stack (or are OP_RESERVED and exec
        # will fail).
        si.num_inputs = len(sig_pops)
    return si


# CalcMultiSigStats returns the number of public keys and signatures from
# a multi-signature transaction script.  The passed script MUST already be
# known to be a multi-signature script.
def calc_multi_sig_stats(script: bytes):
    pops = parse_script(script)

    # A multi-signature script is of the pattern:
    #  NUM_SIGS PUBKEY PUBKEY PUBKEY... NUM_PUBKEYS OP_CHECKMULTISIG
    # Therefore the number of signatures is the oldest item on the stack
    # and the number of pubkeys is the 2nd to last.  Also, the absolute
    # minimum for a multi-signature script is 1 pubkey, so at least 4
    # items must be on the stack per:
    #  OP_1 PUBKEY OP_1 OP_CHECKMULTISIG
    if len(pops) < 4:
        desc = "script %s is not a multisig script" % format_bytes(script)
        raise ScriptError(ErrorCode.ErrNotMultisigScript, desc=desc)

    mum_sigs = as_small_int(pops[0].opcode)
    mum_pubkeys = as_small_int(pops[-2].opcode)
    return mum_sigs, mum_pubkeys


# payToPubKeyHashScript creates a new script to pay a transaction
# output to a 20-byte pubkey hash. It is expected that the input is a valid
# hash.
def pay_to_pub_key_hash_script(pubkey_hash: bytes) -> bytes:
    return ScriptBuilder().add_op(OP_DUP).add_op(OP_HASH160).add_data(pubkey_hash).add_op(
        OP_EQUALVERIFY).add_op(OP_CHECKSIG).script  # TOCHECK OP_EQUALVERIFY or OP_EUQAL


# payToWitnessPubKeyHashScript creates a new script to pay to a version 0
# pubkey hash witness program. The passed hash is expected to be valid.
def pay_to_witness_pubkey_hash_script(pubkey_hash: bytes) -> bytes:
    return ScriptBuilder().add_op(OP_0).add_data(pubkey_hash).script


# payToScriptHashScript creates a new script to pay a transaction output to a
# script hash. It is expected that the input is a valid hash.
def pay_to_script_hash_script(script_hash: bytes) -> bytes:
    return ScriptBuilder().add_op(OP_HASH160).add_data(script_hash).add_op(OP_EQUAL).script


# payToWitnessPubKeyHashScript creates a new script to pay to a version 0
# script hash witness program. The passed hash is expected to be valid.
def pay_to_witness_script_hash_script(script_hash: bytes) -> bytes:
    return ScriptBuilder().add_op(OP_0).add_data(script_hash).script


# payToPubkeyScript creates a new script to pay a transaction output to a
# public key. It is expected that the input is a valid pubkey.
def pay_to_pub_key_script(serialized_pub_key: bytes) -> bytes:
    return ScriptBuilder().add_data(serialized_pub_key).add_op(OP_CHECKSIG).script


# PayToAddrScript creates a new script to pay a transaction output to a the
# specified address.
def pay_to_addr_script(addr):
    if not addr:
        desc = "unable to generate payment script for nil address"
        raise ScriptError(ErrorCode.ErrUnsupportedAddress, desc=desc)

    addr_type = type(addr)
    if addr_type == AddressPubKeyHash:
        return pay_to_pub_key_hash_script(addr.script_address())
    elif addr_type == AddressScriptHash:
        return pay_to_script_hash_script(addr.script_address())
    elif addr_type == AddressPubKey:
        return pay_to_pub_key_script(addr.script_address())
    elif addr_type == AddressWitnessPubKeyHash:
        return pay_to_witness_pub_key_hash_script(addr.script_address())
    elif addr_type == AddressWitnessScriptHash:
        return pay_to_witness_script_hash_script(addr.script_address())
    else:
        desc = "unable to generate payment script for unsupported address type %s" % addr_type
        raise ScriptError(ErrorCode.ErrUnsupportedAddress, desc=desc)


# NullDataScript creates a provably-prunable script containing OP_RETURN
# followed by the passed data.  An Error with the error code ErrTooMuchNullData
# will be returned if the length of the passed data exceeds MaxDataCarrierSize.
def null_data_script(data: bytes):
    if len(data) > MaxDataCarrierSize:
        desc = "data size %d is larger than max allowed size %d" % (len(data), MaxDataCarrierSize)
        raise ScriptBuilder().add_op(OP_RETURN).add_data(data).script


# MultiSigScript returns a valid script for a multisignature redemption where
# nrequired of the keys in pubkeys are required to have signed the transaction
# for success.  An Error with the error code ErrTooManyRequiredSigs will be
# returned if nrequired is larger than the number of keys provided.
def multi_sig_script(pub_keys, nrequired):
    """

    :param []btcutil.AddressPubKey pub_keys:
    :param int nrequired:
    :return:
    """
    if len(pub_keys) < nrequired:
        desc = "unable to generate multisig script with %d required signatures when there are only %d public keys available" % (
            nrequired, len(pub_keys))
        raise ScriptError(ErrorCode.ErrTooManyRequiredSigs, desc=desc)

    builder = ScriptBuilder().add_int64(nrequired)
    for key in pub_keys:
        builder.add_data(key.script_address())

    builder.add_int64(len(pub_keys))
    builder.add_op(OP_CHECKMULTISIG)
    return builder.script


# PushedData returns an array of byte slices containing any pushed data found
# in the passed script.  This includes OP_0, but not OP_1 - OP_16.
def pushed_data(script: bytes):
    pops = parse_script(script)

    data = []
    for pop in pops:
        if pop.data:
            data.append(pop.data)
        elif pop.opcode.value == OP_0:
            data.append(bytes())
        else:
            pass

    return data


# ExtractPkScriptAddrs returns the type of script, addresses and required
# signatures associated with the passed PkScript.  Note that it only works for
# 'standard' transaction script types.  Any data such as public keys which are
# invalid are omitted from the results.
def extract_pk_script_addrs(pk_script, chain_params):
    addrs = []
    required_sigs = 0

    pops = parse_script(pk_script)

    script_class = type_of_script(pops)

    if script_class == ScriptClass.PubKeyHashTy:
        # A pay-to-pubkey-hash script is of the form:
        #  OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG
        # Therefore the pubkey hash is the 3rd item on the stack.
        # Skip the pubkey hash if it's invalid for some reason.
        required_sigs = 1
        addr = AddressPubKeyHash.new_from_params(pops[2].data, chain_params)
        addrs.append(addr)
    elif script_class == ScriptClass.WitnessV0PubKeyHashTy:
        # A pay-to-witness-pubkey-hash script is of the form:
        #  OP_0 <20-byte hash>
        # Therefore, the pubkey hash is the second item on the stack.
        # Skip the pubkey hash if it's invalid for some reason.
        required_sigs = 1
        addr = AddressWitnessPubKeyHash.new_from_params(pops[1].data, chain_params)
        addrs.append(addr)
    elif script_class == ScriptClass.PubKeyTy:
        # A pay-to-pubkey script is of the form:
        #  <pubkey> OP_CHECKSIG
        # Therefore the pubkey is the first item on the stack.
        # Skip the pubkey if it's invalid for some reason.
        required_sigs = 1
        addr = AddressPubKey.new_from_params(pops[0].data, chain_params)
        addrs.append(addr)
    elif script_class == ScriptClass.ScriptHashTy:
        # A pay-to-script-hash script is of the form:
        #  OP_HASH160 <scripthash> OP_EQUAL
        # Therefore the script hash is the 2nd item on the stack.
        # Skip the script hash if it's invalid for some reason.
        required_sigs = 1
        addr = AddressScriptHash.new_from_params(pops[1].data, chain_params)
        addrs.append(addr)
    elif script_class == ScriptClass.WitnessV0ScriptHashTy:
        # A pay-to-witness-script-hash script is of the form:
        #  OP_0 <32-byte hash>
        # Therefore, the script hash is the second item on the stack.
        # Skip the script hash if it's invalid for some reason.
        required_sigs = 1
        addr = AddressWitnessScriptHash.new_from_params(pops[1].data, chain_params)
        addrs.append(addr)
    elif script_class == ScriptClass.MultiSigTy:
        # A multi-signature script is of the form:
        #  <numsigs> <pubkey> <pubkey> <pubkey>... <numpubkeys> OP_CHECKMULTISIG
        # Therefore the number of required signatures is the 1st item
        # on the stack and the number of public keys is the 2nd to last
        # item on the stack.
        required_sigs = as_small_int(pops[0].opcode)
        num_pubkeys = as_small_int(pops[-2].opcode)
        for i in range(num_pubkeys):
            addr = AddressPubKey.new_from_params(pops[i + 1].data, chain_params)
            addrs.append(addr)
    elif script_class == ScriptClass.NullDataTy:
        # Null data transactions have no addresses or required
        # signatures.
        pass
    elif script_class == ScriptClass.NonStandardTy:
        # Don't attempt to extract addresses or required signatures for
        # nonstandard transactions.
        pass
    else:
        pass

    return script_class, addrs, required_sigs


def ExtractAtomicSwapDataPushes():
    pass
