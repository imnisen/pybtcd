from enum import Enum


# ErrorCode identifies a kind of script error.
class ErrorCode(Enum):
    # ErrInternal is returned if internal consistency checks fail.  In
    # practice this error should never be seen as it would mean there is an
    # error in the engine logic.
    ErrInternal = 0

    # ---------------------------------------
    # Failures related to improper API usage.
    # ---------------------------------------

    # ErrInvalidFlags is returned when the passed flags to NewEngine
    # contain an invalid combination.
    ErrInvalidFlags = 1

    # ErrInvalidIndex is returned when an out-of-bounds index is passed to
    # a function.
    ErrInvalidIndex = 2

    # ErrInvalidIndex is returned when an out-of-bounds index is passed to
    # a function.
    ErrUnsupportedAddress = 3

    # ErrNotMultisigScript is returned from CalcMultiSigStats when the
    # provided script is not a multisig script.
    ErrNotMultisigScript = 4

    # ErrTooManyRequiredSigs is returned from MultiSigScript when the
    # specified number of required signatures is larger than the number of
    # provided public keys.
    ErrTooManyRequiredSigs = 5

    # ErrTooMuchNullData is returned from NullDataScript when the length of
    # the provided data exceeds MaxDataCarrierSize.
    ErrTooMuchNullData = 6

    # ------------------------------------------
    # Failures related to final execution state.
    # ------------------------------------------

    # ErrEarlyReturn is returned when OP_RETURN is executed in the script.
    ErrEarlyReturn = 7

    # ErrEmptyStack is returned when the script evaluated without error,
    # but terminated with an empty top stack element.
    ErrEmptyStack = 8

    # ErrEvalFalse is returned when the script evaluated without error but
    # terminated with a false top stack element.
    ErrEvalFalse = 9

    # ErrScriptUnfinished is returned when CheckErrorCondition is called on
    # a script that has not finished executing.
    ErrScriptUnfinished = 10

    # ErrScriptDone is returned when an attempt to execute an opcode is
    # made once all of them have already been executed.  This can happen
    # due to things such as a second call to Execute or calling Step after
    # all opcodes have already been executed.
    ErrInvalidProgramCounter = 11

    # -----------------------------------------------------
    # Failures related to exceeding maximum allowed limits.
    # -----------------------------------------------------

    # ErrScriptTooBig is returned if a script is larger than MaxScriptSize.
    ErrScriptTooBig = 12

    # ErrElementTooBig is returned if the size of an element to be pushed
    # to the stack is over MaxScriptElementSize.
    ErrElementTooBig = 13

    # ErrTooManyOperations is returned if a script has more than
    # MaxOpsPerScript opcodes that do not push data.
    ErrTooManyOperations = 14

    # ErrStackOverflow is returned when stack and altstack combined depth
    # is over the limit.
    ErrStackOverflow = 15

    # ErrInvalidPubKeyCount is returned when the number of public keys
    # specified for a multsig is either negative or greater than
    # MaxPubKeysPerMultiSig.
    ErrInvalidPubKeyCount = 16

    # ErrInvalidSignatureCount is returned when the number of signatures
    # specified for a multisig is either negative or greater than the
    # number of public keys.
    ErrInvalidSignatureCount = 17

    # ErrNumberTooBig is returned when the argument for an opcode that
    # expects numeric input is larger than the expected maximum number of
    # bytes.  For the most part, opcodes that deal with stack manipulation
    # via offsets, arithmetic, numeric comparison, and boolean logic are
    # those that this applies to.  However, any opcode that expects numeric
    # input may fail with this code.
    ErrNumberTooBig = 18

    # --------------------------------------------
    # Failures related to verification operations.
    # --------------------------------------------

    # ErrVerify is returned when OP_VERIFY is encountered in a script and
    # the top item on the data stack does not evaluate to true.
    ErrVerify = 19

    # ErrEqualVerify is returned when OP_EQUALVERIFY is encountered in a
    # script and the top item on the data stack does not evaluate to true.
    ErrEqualVerify = 20

    # ErrNumEqualVerify is returned when OP_NUMEQUALVERIFY is encountered
    # in a script and the top item on the data stack does not evaluate to
    # true.
    ErrNumEqualVerify = 21

    # ErrCheckSigVerify is returned when OP_CHECKSIGVERIFY is encountered
    # in a script and the top item on the data stack does not evaluate to
    # true.
    ErrCheckSigVerify = 22

    # ErrCheckSigVerify is returned when OP_CHECKMULTISIGVERIFY is
    # encountered in a script and the top item on the data stack does not
    # evaluate to true.
    ErrCheckMultiSigVerify = 23

    # --------------------------------------------
    # Failures related to improper use of opcodes.
    # --------------------------------------------

    # ErrDisabledOpcode is returned when a disabled opcode is encountered
    # in a script.
    ErrDisabledOpcode = 24

    # ErrReservedOpcode is returned when an opcode marked as reserved
    # is encountered in a script.
    ErrReservedOpcode = 25

    # ErrMalformedPush is returned when a data push opcode tries to push
    # more bytes than are left in the script.
    ErrMalformedPush = 26

    # ErrInvalidStackOperation is returned when a stack operation is
    # attempted with a number that is invalid for the current stack size.
    ErrInvalidStackOperation = 27

    # ErrUnbalancedConditional is returned when an OP_ELSE or OP_ENDIF is
    # encountered in a script without first having an OP_IF or OP_NOTIF or
    # the end of script is reached without encountering an OP_ENDIF when
    # an OP_IF or OP_NOTIF was previously encountered.
    ErrUnbalancedConditional = 28

    # ---------------------------------
    # Failures related to malleability.
    # ---------------------------------

    # ErrMinimalData is returned when the ScriptVerifyMinimalData flag
    # is set and the script contains push operations that do not use
    # the minimal opcode required.
    ErrMinimalData = 29

    # ErrInvalidSigHashType is returned when a signature hash type is not
    # one of the supported types.
    ErrInvalidSigHashType = 30

    # ErrSigTooShort is returned when a signature that should be a
    # canonically-encoded DER signature is too short.
    ErrSigTooShort = 31

    # ErrSigTooLong is returned when a signature that should be a
    # canonically-encoded DER signature is too long.
    ErrSigTooLong = 32

    # ErrSigInvalidSeqID is returned when a signature that should be a
    # canonically-encoded DER signature does not have the expected ASN.1
    # sequence ID.
    ErrSigInvalidSeqID = 33

    # ErrSigInvalidDataLen is returned a signature that should be a
    # canonically-encoded DER signature does not specify the correct number
    # of remaining bytes for the R and S portions.
    ErrSigInvalidDataLen = 34

    # ErrSigMissingSTypeID is returned a signature that should be a
    # canonically-encoded DER signature does not provide the ASN.1 type ID
    # for S.
    ErrSigMissingSTypeID = 35

    # ErrSigMissingSLen is returned when a signature that should be a
    # canonically-encoded DER signature does not provide the length of S.
    ErrSigMissingSLen = 36

    # ErrSigInvalidSLen is returned a signature that should be a
    # canonically-encoded DER signature does not specify the correct number
    # of bytes for the S portion.
    ErrSigInvalidSLen = 37

    # ErrSigInvalidRIntID is returned when a signature that should be a
    # canonically-encoded DER signature does not have the expected ASN.1
    # integer ID for R.
    ErrSigInvalidRIntID = 38

    # ErrSigZeroRLen is returned when a signature that should be a
    # canonically-encoded DER signature has an R length of zero.
    ErrSigZeroRLen = 39

    # ErrSigNegativeR is returned when a signature that should be a
    # canonically-encoded DER signature has a negative value for R.
    ErrSigNegativeR = 40

    # ErrSigTooMuchRPadding is returned when a signature that should be a
    # canonically-encoded DER signature has too much padding for R.
    ErrSigTooMuchRPadding = 41

    # ErrSigInvalidSIntID is returned when a signature that should be a
    # canonically-encoded DER signature does not have the expected ASN.1
    # integer ID for S.
    ErrSigInvalidSIntID = 42

    # ErrSigZeroSLen is returned when a signature that should be a
    # canonically-encoded DER signature has an S length of zero.
    ErrSigZeroSLen = 43

    # ErrSigNegativeS is returned when a signature that should be a
    # canonically-encoded DER signature has a negative value for S.
    ErrSigNegativeS = 44

    # ErrSigTooMuchSPadding is returned when a signature that should be a
    # canonically-encoded DER signature has too much padding for S.
    ErrSigTooMuchSPadding = 45

    # ErrSigHighS is returned when the ScriptVerifyLowS flag is set and the
    # script contains any signatures whose S values are higher than the
    # half order.
    ErrSigHighS = 46

    # ErrNotPushOnly is returned when a script that is required to only
    # push data to the stack performs other operations.  A couple of cases
    # where this applies is for a pay-to-script-hash signature script when
    # bip16 is active and when the ScriptVerifySigPushOnly flag is set.
    ErrNotPushOnly = 47

    # ErrSigNullDummy is returned when the ScriptStrictMultiSig flag is set
    # and a multisig script has anything other than 0 for the extra dummy
    # argument.
    ErrSigNullDummy = 48

    # ErrPubKeyType is returned when the ScriptVerifyStrictEncoding
    # flag is set and the script contains invalid public keys.
    ErrPubKeyType = 49

    # ErrCleanStack is returned when the ScriptVerifyCleanStack flag
    # is set, and after evalution, the stack does not contain only a
    # single element.
    ErrCleanStack = 50

    # ErrNullFail is returned when the ScriptVerifyNullFail flag is
    # set and signatures are not empty on failed checksig or checkmultisig
    # operations.
    ErrNullFail = 51

    # ErrWitnessMalleated is returned if ScriptVerifyWitness is set and a
    # native p2wsh program is encountered which has a non-empty sigScript.
    ErrWitnessMalleated = 52

    # ErrWitnessMalleatedP2SH is returned if ScriptVerifyWitness if set
    # and the validation logic for nested p2sh encounters a sigScript
    # which isn't *exactyl* a datapush of the witness program.
    ErrWitnessMalleatedP2SH = 53

    # -------------------------------
    # Failures related to soft forks.
    # -------------------------------

    # ErrDiscourageUpgradableNOPs is returned when the
    # ScriptDiscourageUpgradableNops flag is set and a NOP opcode is
    # encountered in a script.
    ErrDiscourageUpgradableNOPs = 54

    # ErrNegativeLockTime is returned when a script contains an opcode that
    # interprets a negative lock time.
    ErrNegativeLockTime = 55

    # ErrUnsatisfiedLockTime is returned when a script contains an opcode
    # that involves a lock time and the required lock time has not been
    # reached.
    ErrUnsatisfiedLockTime = 56

    # ErrMinimalIf is returned if ScriptVerifyWitness is set and the
    # operand of an OP_IF/OP_NOF_IF are not either an empty vector or
    # [0x01].
    ErrMinimalIf = 57

    # ErrDiscourageUpgradableWitnessProgram is returned if
    # ScriptVerifyWitness is set and the versino of an executing witness
    # program is outside the set of currently defined witness program
    # vesions.
    ErrDiscourageUpgradableWitnessProgram = 58

    # ----------------------------------------
    # Failures related to segregated witness.
    # ----------------------------------------

    # ErrWitnessProgramEmpty is returned if ScriptVerifyWitness is set and
    # the witness stack itself is empty.
    ErrWitnessProgramEmpty = 59

    # ErrWitnessProgramMismatch is returned if ScriptVerifyWitness is set
    # and the witness itself for a p2wkh witness program isn't *exactly* 2
    # items or if the witness for a p2wsh isn't the sha255 of the witness
    # script.
    ErrWitnessProgramMismatch = 60

    # ErrWitnessProgramWrongLength is returned if ScriptVerifyWitness is
    # set and the length of the witness program violates the length as
    # dictated by the current witness version.
    ErrWitnessProgramWrongLength = 61

    # ErrWitnessUnexpected is returned if ScriptVerifyWitness is set and a
    # transaction includes witness data but doesn't spend an which is a
    # witness program (nested or native).
    ErrWitnessUnexpected = 62

    # ErrWitnessPubKeyType is returned if ScriptVerifyWitness is set and
    # the public key used in either a check-sig or check-multi-sig isn't
    # serialized in a compressed format.
    ErrWitnessPubKeyType = 62

    # numErrorCodes is the maximum error code number used in tests.  This
    # entry MUST be the last entry in the enum.
    numErrorCodes = 63


    def __str__(self):
        return errorCodeStrings[self]


errorCodeStrings = {
    ErrorCode.ErrInternal: "ErrInternal",
    ErrorCode.ErrInvalidFlags: "ErrInvalidFlags",
    ErrorCode.ErrInvalidIndex: "ErrInvalidIndex",
    ErrorCode.ErrUnsupportedAddress: "ErrUnsupportedAddress",
    ErrorCode.ErrNotMultisigScript: "ErrNotMultisigScript",
    ErrorCode.ErrTooManyRequiredSigs: "ErrTooManyRequiredSigs",
    ErrorCode.ErrTooMuchNullData: "ErrTooMuchNullData",
    ErrorCode.ErrEarlyReturn: "ErrEarlyReturn",
    ErrorCode.ErrEmptyStack: "ErrEmptyStack",
    ErrorCode.ErrEvalFalse: "ErrEvalFalse",
    ErrorCode.ErrScriptUnfinished: "ErrScriptUnfinished",
    ErrorCode.ErrInvalidProgramCounter: "ErrInvalidProgramCounter",
    ErrorCode.ErrScriptTooBig: "ErrScriptTooBig",
    ErrorCode.ErrElementTooBig: "ErrElementTooBig",
    ErrorCode.ErrTooManyOperations: "ErrTooManyOperations",
    ErrorCode.ErrStackOverflow: "ErrStackOverflow",
    ErrorCode.ErrInvalidPubKeyCount: "ErrInvalidPubKeyCount",
    ErrorCode.ErrInvalidSignatureCount: "ErrInvalidSignatureCount",
    ErrorCode.ErrNumberTooBig: "ErrNumberTooBig",
    ErrorCode.ErrVerify: "ErrVerify",
    ErrorCode.ErrEqualVerify: "ErrEqualVerify",
    ErrorCode.ErrNumEqualVerify: "ErrNumEqualVerify",
    ErrorCode.ErrCheckSigVerify: "ErrCheckSigVerify",
    ErrorCode.ErrCheckMultiSigVerify: "ErrCheckMultiSigVerify",
    ErrorCode.ErrDisabledOpcode: "ErrDisabledOpcode",
    ErrorCode.ErrReservedOpcode: "ErrReservedOpcode",
    ErrorCode.ErrMalformedPush: "ErrMalformedPush",
    ErrorCode.ErrInvalidStackOperation: "ErrInvalidStackOperation",
    ErrorCode.ErrUnbalancedConditional: "ErrUnbalancedConditional",
    ErrorCode.ErrMinimalData: "ErrMinimalData",
    ErrorCode.ErrInvalidSigHashType: "ErrInvalidSigHashType",
    ErrorCode.ErrSigTooShort: "ErrSigTooShort",
    ErrorCode.ErrSigTooLong: "ErrSigTooLong",
    ErrorCode.ErrSigInvalidSeqID: "ErrSigInvalidSeqID",
    ErrorCode.ErrSigInvalidDataLen: "ErrSigInvalidDataLen",
    ErrorCode.ErrSigMissingSTypeID: "ErrSigMissingSTypeID",
    ErrorCode.ErrSigMissingSLen: "ErrSigMissingSLen",
    ErrorCode.ErrSigInvalidSLen: "ErrSigInvalidSLen",
    ErrorCode.ErrSigInvalidRIntID: "ErrSigInvalidRIntID",
    ErrorCode.ErrSigZeroRLen: "ErrSigZeroRLen",
    ErrorCode.ErrSigNegativeR: "ErrSigNegativeR",
    ErrorCode.ErrSigTooMuchRPadding: "ErrSigTooMuchRPadding",
    ErrorCode.ErrSigInvalidSIntID: "ErrSigInvalidSIntID",
    ErrorCode.ErrSigZeroSLen: "ErrSigZeroSLen",
    ErrorCode.ErrSigNegativeS: "ErrSigNegativeS",
    ErrorCode.ErrSigTooMuchSPadding: "ErrSigTooMuchSPadding",
    ErrorCode.ErrSigHighS: "ErrSigHighS",
    ErrorCode.ErrNotPushOnly: "ErrNotPushOnly",
    ErrorCode.ErrSigNullDummy: "ErrSigNullDummy",
    ErrorCode.ErrPubKeyType: "ErrPubKeyType",
    ErrorCode.ErrCleanStack: "ErrCleanStack",
    ErrorCode.ErrNullFail: "ErrNullFail",
    ErrorCode.ErrDiscourageUpgradableNOPs: "ErrDiscourageUpgradableNOPs",
    ErrorCode.ErrNegativeLockTime: "ErrNegativeLockTime",
    ErrorCode.ErrUnsatisfiedLockTime: "ErrUnsatisfiedLockTime",
    ErrorCode.ErrWitnessProgramEmpty: "ErrWitnessProgramEmpty",
    ErrorCode.ErrWitnessProgramMismatch: "ErrWitnessProgramMismatch",
    ErrorCode.ErrWitnessProgramWrongLength: "ErrWitnessProgramWrongLength",
    ErrorCode.ErrWitnessMalleated: "ErrWitnessMalleated",
    ErrorCode.ErrWitnessMalleatedP2SH: "ErrWitnessMalleatedP2SH",
    ErrorCode.ErrWitnessUnexpected: "ErrWitnessUnexpected",
    ErrorCode.ErrMinimalIf: "ErrMinimalIf",
    ErrorCode.ErrWitnessPubKeyType: "ErrWitnessPubKeyType",
    ErrorCode.ErrDiscourageUpgradableWitnessProgram: "ErrDiscourageUpgradableWitnessProgram",
}


class ScriptError(Exception):
    def __init__(self, c, desc=None, extra_data=None):
        """

        :param ErrorCode c:
        :param str desc:
        """

        self.c = c
        self.desc = desc or ""
        self.extra_data = extra_data

    def __eq__(self, other):
        return self.c == other.c and self.desc == other.desc

    def __repr__(self):
        return "ScriptError(ErrorCode={}, desc={})".format(str(self.c), self.desc or "\"\"")

    def __str__(self):
        return "ScriptError(ErrorCode={}, desc={})".format(str(self.c), self.desc or "\"\"")

    def __hash__(self):
        return hash(str(self.c) + str(self.desc) + str(self.extra_data))


class OtherScriptError(Exception):
    pass


class NotWitnessProgramError(OtherScriptError):
    pass


class IdxTxInptsLenNotMatchError(Exception):
    pass
