from enum import Enum


# ErrorCode identifies a kind of script error.
class ErrorCode(Enum):
    # ErrInternal is returned if internal consistency checks fail.  In
    # practice this error should never be seen as it would mean there is an
    # error in the engine logic.
    ErrInternal = (1 << 0, "ErrInternal")

    # ---------------------------------------
    # Failures related to improper API usage.
    # ---------------------------------------

    # ErrInvalidFlags is returned when the passed flags to NewEngine
    # contain an invalid combination.
    ErrInvalidFlags = (1 << 1, "ErrInvalidFlags")

    # ErrInvalidIndex is returned when an out-of-bounds index is passed to
    # a function.
    ErrInvalidIndex = (1 << 2, "ErrInvalidIndex")

    # ErrInvalidIndex is returned when an out-of-bounds index is passed to
    # a function.
    ErrUnsupportedAddress = (1 << 3, "ErrUnsupportedAddress")

    # ErrNotMultisigScript is returned from CalcMultiSigStats when the
    # provided script is not a multisig script.
    ErrNotMultisigScript = (1 << 4, "ErrNotMultisigScript")

    # ErrTooManyRequiredSigs is returned from MultiSigScript when the
    # specified number of required signatures is larger than the number of
    # provided public keys.
    ErrTooManyRequiredSigs = (1 << 5, "ErrTooManyRequiredSigs")

    # ErrTooMuchNullData is returned from NullDataScript when the length of
    # the provided data exceeds MaxDataCarrierSize.
    ErrTooMuchNullData = (1 << 6, "ErrTooMuchNullData")

    # ------------------------------------------
    # Failures related to final execution state.
    # ------------------------------------------

    # ErrEarlyReturn is returned when OP_RETURN is executed in the script.
    ErrEarlyReturn = (1 << 7, "ErrEarlyReturn")

    # ErrEmptyStack is returned when the script evaluated without error,
    # but terminated with an empty top stack element.
    ErrEmptyStack = (1 << 8, "ErrEmptyStack")

    # ErrEvalFalse is returned when the script evaluated without error but
    # terminated with a false top stack element.
    ErrEvalFalse = (1 << 9, "ErrEvalFalse")

    # ErrScriptUnfinished is returned when CheckErrorCondition is called on
    # a script that has not finished executing.
    ErrScriptUnfinished = (1 << 10, "ErrScriptUnfinished")

    # ErrScriptDone is returned when an attempt to execute an opcode is
    # made once all of them have already been executed.  This can happen
    # due to things such as a second call to Execute or calling Step after
    # all opcodes have already been executed.
    ErrInvalidProgramCounter = (1 << 11, "ErrInvalidProgramCounter")

    # -----------------------------------------------------
    # Failures related to exceeding maximum allowed limits.
    # -----------------------------------------------------

    # ErrScriptTooBig is returned if a script is larger than MaxScriptSize.
    ErrScriptTooBig = (1 << 12, "ErrScriptTooBig")

    # ErrElementTooBig is returned if the size of an element to be pushed
    # to the stack is over MaxScriptElementSize.
    ErrElementTooBig = (1 << 13, "ErrElementTooBig")

    # ErrTooManyOperations is returned if a script has more than
    # MaxOpsPerScript opcodes that do not push data.
    ErrTooManyOperations = (1 << 14, "ErrTooManyOperations")

    # ErrStackOverflow is returned when stack and altstack combined depth
    # is over the limit.
    ErrStackOverflow = (1 << 15, "ErrStackOverflow")

    # ErrInvalidPubKeyCount is returned when the number of public keys
    # specified for a multsig is either negative or greater than
    # MaxPubKeysPerMultiSig.
    ErrInvalidPubKeyCount = (1 << 16, "ErrInvalidPubKeyCount")

    # ErrInvalidSignatureCount is returned when the number of signatures
    # specified for a multisig is either negative or greater than the
    # number of public keys.
    ErrInvalidSignatureCount = (1 << 17, "ErrInvalidSignatureCount")

    # ErrNumberTooBig is returned when the argument for an opcode that
    # expects numeric input is larger than the expected maximum number of
    # bytes.  For the most part, opcodes that deal with stack manipulation
    # via offsets, arithmetic, numeric comparison, and boolean logic are
    # those that this applies to.  However, any opcode that expects numeric
    # input may fail with this code.
    ErrNumberTooBig = (1 << 18, "ErrNumberTooBig")

    # --------------------------------------------
    # Failures related to verification operations.
    # --------------------------------------------

    # ErrVerify is returned when OP_VERIFY is encountered in a script and
    # the top item on the data stack does not evaluate to true.
    ErrVerify = (1 << 19, "ErrVerify")

    # ErrEqualVerify is returned when OP_EQUALVERIFY is encountered in a
    # script and the top item on the data stack does not evaluate to true.
    ErrEqualVerify = (1 << 20, "ErrEqualVerify")

    # ErrNumEqualVerify is returned when OP_NUMEQUALVERIFY is encountered
    # in a script and the top item on the data stack does not evaluate to
    # true.
    ErrNumEqualVerify = (1 << 21, "ErrNumEqualVerify")

    # ErrCheckSigVerify is returned when OP_CHECKSIGVERIFY is encountered
    # in a script and the top item on the data stack does not evaluate to
    # true.
    ErrCheckSigVerify = (1 << 22, "ErrCheckSigVerify")

    # ErrCheckSigVerify is returned when OP_CHECKMULTISIGVERIFY is
    # encountered in a script and the top item on the data stack does not
    # evaluate to true.
    ErrCheckMultiSigVerify = (1 << 23, "ErrCheckMultiSigVerify")

    # --------------------------------------------
    # Failures related to improper use of opcodes.
    # --------------------------------------------

    # ErrDisabledOpcode is returned when a disabled opcode is encountered
    # in a script.
    ErrDisabledOpcode = (1 << 24, "ErrDisabledOpcode")

    # ErrReservedOpcode is returned when an opcode marked as reserved
    # is encountered in a script.
    ErrReservedOpcode = (1 << 25, "ErrReservedOpcode")

    # ErrMalformedPush is returned when a data push opcode tries to push
    # more bytes than are left in the script.
    ErrMalformedPush = (1 << 26, "ErrMalformedPush")

    # ErrInvalidStackOperation is returned when a stack operation is
    # attempted with a number that is invalid for the current stack size.
    ErrInvalidStackOperation = (1 << 27, "ErrInvalidStackOperation")

    # ErrUnbalancedConditional is returned when an OP_ELSE or OP_ENDIF is
    # encountered in a script without first having an OP_IF or OP_NOTIF or
    # the end of script is reached without encountering an OP_ENDIF when
    # an OP_IF or OP_NOTIF was previously encountered.
    ErrUnbalancedConditional = (1 << 28, "ErrUnbalancedConditional")

    # ---------------------------------
    # Failures related to malleability.
    # ---------------------------------

    # ErrMinimalData is returned when the ScriptVerifyMinimalData flag
    # is set and the script contains push operations that do not use
    # the minimal opcode required.
    ErrMinimalData = (1 << 29, "ErrMinimalData")

    # ErrInvalidSigHashType is returned when a signature hash type is not
    # one of the supported types.
    ErrInvalidSigHashType = (1 << 30, "ErrInvalidSigHashType")

    # ErrSigDER is returned when a signature is not a canonically-encoded
    # DER signature.
    ErrSigDER = (1 << 31, "ErrSigDER")

    # ErrSigHighS is returned when the ScriptVerifyLowS flag is set and the
    # script contains any signatures whose S values are higher than the
    # half order.
    ErrSigHighS = (1 << 32, "ErrSigHighS")

    # ErrNotPushOnly is returned when a script that is required to only
    # push data to the stack performs other operations.  A couple of cases
    # where this applies is for a pay-to-script-hash signature script when
    # bip16 is active and when the ScriptVerifySigPushOnly flag is set.
    ErrNotPushOnly = (1 << 33, "ErrNotPushOnly")

    # ErrSigNullDummy is returned when the ScriptStrictMultiSig flag is set
    # and a multisig script has anything other than 0 for the extra dummy
    # argument.
    ErrSigNullDummy = (1 << 34, "ErrSigNullDummy")

    # ErrPubKeyType is returned when the ScriptVerifyStrictEncoding
    # flag is set and the script contains invalid public keys.
    ErrPubKeyType = (1 << 35, "ErrPubKeyType")

    # ErrCleanStack is returned when the ScriptVerifyCleanStack flag
    # is set, and after evalution, the stack does not contain only a
    # single element.
    ErrCleanStack = (1 << 36, "ErrCleanStack")

    # ErrNullFail is returned when the ScriptVerifyNullFail flag is
    # set and signatures are not empty on failed checksig or checkmultisig
    # operations.
    ErrNullFail = (1 << 37, "ErrNullFail")

    # ErrWitnessMalleated is returned if ScriptVerifyWitness is set and a
    # native p2wsh program is encountered which has a non-empty sigScript.
    ErrWitnessMalleated = (1 << 38, "ErrWitnessMalleated")

    # ErrWitnessMalleatedP2SH is returned if ScriptVerifyWitness if set
    # and the validation logic for nested p2sh encounters a sigScript
    # which isn't *exactyl* a datapush of the witness program.
    ErrWitnessMalleatedP2SH = (1 << 39, "ErrWitnessMalleatedP2SH")

    # -------------------------------
    # Failures related to soft forks.
    # -------------------------------

    # ErrDiscourageUpgradableNOPs is returned when the
    # ScriptDiscourageUpgradableNops flag is set and a NOP opcode is
    # encountered in a script.
    ErrDiscourageUpgradableNOPs = (1 << 40, "ErrDiscourageUpgradableNOPs")

    # ErrNegativeLockTime is returned when a script contains an opcode that
    # interprets a negative lock time.
    ErrNegativeLockTime = (1 << 41, "ErrNegativeLockTime")

    # ErrUnsatisfiedLockTime is returned when a script contains an opcode
    # that involves a lock time and the required lock time has not been
    # reached.
    ErrUnsatisfiedLockTime = (1 << 42, "ErrUnsatisfiedLockTime")

    # ErrMinimalIf is returned if ScriptVerifyWitness is set and the
    # operand of an OP_IF/OP_NOF_IF are not either an empty vector or
    # [0x01].
    ErrMinimalIf = (1 << 43, "ErrMinimalIf")

    # ErrDiscourageUpgradableWitnessProgram is returned if
    # ScriptVerifyWitness is set and the versino of an executing witness
    # program is outside the set of currently defined witness program
    # vesions.
    ErrDiscourageUpgradableWitnessProgram = (1 << 44, "ErrDiscourageUpgradableWitnessProgram")

    # ----------------------------------------
    # Failures related to segregated witness.
    # ----------------------------------------

    # ErrWitnessProgramEmpty is returned if ScriptVerifyWitness is set and
    # the witness stack itself is empty.
    ErrWitnessProgramEmpty = (1 << 45, "ErrWitnessProgramEmpty")

    # ErrWitnessProgramMismatch is returned if ScriptVerifyWitness is set
    # and the witness itself for a p2wkh witness program isn't *exactly* 2
    # items or if the witness for a p2wsh isn't the sha255 of the witness
    # script.
    ErrWitnessProgramMismatch = (1 << 46, "ErrWitnessProgramMismatch")

    # ErrWitnessProgramWrongLength is returned if ScriptVerifyWitness is
    # set and the length of the witness program violates the length as
    # dictated by the current witness version.
    ErrWitnessProgramWrongLength = (1 << 47, "ErrWitnessProgramWrongLength")

    # ErrWitnessUnexpected is returned if ScriptVerifyWitness is set and a
    # transaction includes witness data but doesn't spend an which is a
    # witness program (nested or native).
    ErrWitnessUnexpected = (1 << 48, "ErrWitnessUnexpected")

    # ErrWitnessPubKeyType is returned if ScriptVerifyWitness is set and
    # the public key used in either a check-sig or check-multi-sig isn't
    # serialized in a compressed format.
    ErrWitnessPubKeyType = (1 << 49, "ErrWitnessPubKeyType")

    numErrorCodes = (1 << 50, "numErrorCodes")


class ScriptError(BaseException):
    def __init__(self, c, desc):
        """

        :param ErrorCode c:
        :param str desc:
        """

        self.c = c
        self.desc = desc