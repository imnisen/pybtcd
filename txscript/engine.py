from enum import Enum
from .opcode import *


class ScriptFlag(Enum):
    # ScriptBip16 defines whether the bip16 threshold has passed and thus
    # pay-to-script hash transactions will be fully validated.
    ScriptBip16 = 1 << 0

    # ScriptStrictMultiSig defines whether to verify the stack item
    # used by CHECKMULTISIG is zero length.
    ScriptStrictMultiSig = 1 << 1

    # ScriptDiscourageUpgradableNops defines whether to verify that
    # NOP1 through NOP10 are reserved for future soft-fork upgrades.  This
    # flag must not be used for consensus critical code nor applied to
    # blocks as this flag is only for stricter standard transaction
    # checks.  This flag is only applied when the above opcodes are
    # executed.
    ScriptDiscourageUpgradableNops = 1 << 2

    # ScriptVerifyCheckLockTimeVerify defines whether to verify that
    # a transaction output is spendable based on the locktime.
    # This is BIP0065.
    ScriptVerifyCheckLockTimeVerify = 1 << 3

    # ScriptVerifyCheckSequenceVerify defines whether to allow execution
    # pathways of a script to be restricted based on the age of the output
    # being spent.  This is BIP0112.
    ScriptVerifyCheckSequenceVerify = 1 << 4

    # ScriptVerifyCleanStack defines that the stack must contain only
    # one stack element after evaluation and that the element must be
    # true if interpreted as a boolean.  This is rule 6 of BIP0062.
    # This flag should never be used without the ScriptBip16 flag nor the
    # ScriptVerifyWitness flag.
    ScriptVerifyCleanStack = 1 << 5

    # ScriptVerifyDERSignatures defines that signatures are required
    # to compily with the DER format.
    ScriptVerifyDERSignatures = 1 << 6

    # ScriptVerifyLowS defines that signtures are required to comply with
    # the DER format and whose S value is <= order / 2.  This is rule 5
    # of BIP0062.
    ScriptVerifyLowS = 1 << 7

    # ScriptVerifyMinimalData defines that signatures must use the smallest
    # push operator. This is both rules 3 and 4 of BIP0062.
    ScriptVerifyMinimalData = 1 << 8

    # ScriptVerifyNullFail defines that signatures must be empty if
    # a CHECKSIG or CHECKMULTISIG operation fails.
    ScriptVerifyNullFail = 1 << 9

    # ScriptVerifySigPushOnly defines that signature scripts must contain
    # only pushed data.  This is rule 2 of BIP0062.
    ScriptVerifySigPushOnly = 1 << 10

    # ScriptVerifyStrictEncoding defines that signature scripts and
    # public keys must follow the strict encoding requirements.
    ScriptVerifyStrictEncoding = 1 << 11

    # ScriptVerifyWitness defines whether or not to verify a transaction
    # output using a witness program template.
    ScriptVerifyWitness = 1 << 12

    # ScriptVerifyDiscourageUpgradeableWitnessProgram makes witness
    # program with versions 2-16 non-standard.
    ScriptVerifyDiscourageUpgradeableWitnessProgram = 1 << 13

    # ScriptVerifyMinimalIf makes a script with an OP_IF/OP_NOTIF whose
    # operand is anything other than empty vector or [0x01] non-standard.
    ScriptVerifyMinimalIf = 1 << 14

    # ScriptVerifyWitnessPubKeyType makes a script within a check-sig
    # operation whose public key isn't serialized in a compressed format
    # non-standard.
    ScriptVerifyWitnessPubKeyType = 1 << 15


class ScriptFlags:
    def __init__(self, data):
        if type(data) is ScriptFlag:
            self._data = data.value
        elif type(data) is int:
            self._data = data
        elif type(data) is ScriptFlags:
            self._data = ScriptFlags.value
        else:
            self._data = 0

    @property
    def value(self):
        return self._data


    def has_flag(self, flag):
        return (self._data & flag.value) == flag.value






# Engine is the virtual machine that executes scripts.
class Engine:
    def __init__(self, scripts, script_idx, script_off, last_code_seq,
                 dstack, astack, tx, tx_idx, cond_stack, num_ops,
                 flags, sig_cache, hash_cache, bip16, saved_first_stack,
                 witness_version, witness_program, inptut_amount):
        """

        :param [][]parsedOpcode scripts:
        :param int script_idx:
        :param int script_off:
        :param int last_code_seq:
        :param stack dstack:
        :param stack astack:
        :param wire.MsgTx tx:
        :param int tx_idx:
        :param []int cond_stack:
        :param int num_ops:
        :param ScriptFlags flags:
        :param SigCache sig_cache:
        :param TxSigHashes hash_cache:
        :param bool bip16:
        :param [][]byte saved_first_stack:
        :param int witness_version:
        :param []byte witness_program:
        :param int64 inptut_amount:
        """
        self.scripts = scripts
        self.script_idx = script_idx
        self.script_off = script_off
        self.last_code_seq = last_code_seq
        self.dstack = dstack
        self.astack = astack
        self.tx = tx
        self.tx_idx = tx_idx
        self.cond_stack = cond_stack
        self.num_ops = num_ops
        self.flags = flags
        self.sig_cache = sig_cache
        self.hash_cache = hash_cache
        self.bip16 = bip16
        self.saved_first_stack = saved_first_stack
        self.witness_version = witness_version
        self.witness_program = witness_program
        self.inptut_amount = inptut_amount


    # has_flag returns whether the script engine instance has the passed flag set.
    def has_flag(self, flag: ScriptFlag) -> bool:
        return self.flags.has_flag(flag)

    # is_branch_executing returns whether or not the current conditional branch is
    # actively executing.  For example, when the data stack has an OP_FALSE on it
    # and an OP_IF is encountered, the branch is inactive until an OP_ELSE or
    # OP_ENDIF is encountered.  It properly handles nested conditionals.
    def is_branch_executing(self) -> bool:
        if len(self.cond_stack) == 0:
            return True
        return self.cond_stack[-1] == OpCondTrue
