import blockchain
import wire


# RuleError identifies a rule violation.  It is used to indicate that
# processing of a transaction failed due to one of the many validation
# rules.  The caller can use type assertions to determine if a failure was
# specifically due to a rule violation and use the Err field to access the
# underlying error, which will be either a TxRuleError or a
# blockchain.RuleError.
class RuleError(Exception):
    def __init__(self, err=None):
        self.err = err

    def __repr__(self):
        if not self.err:
            return "RuleError:<None>"

        return repr(self.err)


# TxRuleError identifies a rule violation.  It is used to indicate that
# processing of a transaction failed due to one of the many validation
# rules.  The caller can use type assertions to determine if a failure was
# specifically due to a rule violation and access the ErrorCode field to
# ascertain the specific reason for the rule violation.
class TxRuleError(Exception):
    def __init__(self, reject_code, description):
        self.reject_code = reject_code
        self.description = description

    def __repr__(self):
        return "TxRuleError:" + self.description


# txRuleError creates an underlying TxRuleError with the given a set of
# arguments and returns a RuleError that encapsulates it.
def tx_rule_error(c: wire.RejectCode, desc: str) -> RuleError:
    return RuleError(err=TxRuleError(reject_code=c, description=desc))


# chainRuleError returns a RuleError that encapsulates the given
# blockchain.RuleError.
def chain_rule_error(chain_err: blockchain.RuleError) -> RuleError:
    return RuleError(err=chain_err)
