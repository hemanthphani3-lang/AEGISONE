from abc import ABC, abstractmethod
from typing import Any
from app.engine.enums import PolicyDecision
from app.engine.models import Policy
from app.signals.enums import ConditionResult, SignalStatus
from app.signals.models import SecurityContext


class AbstractConditionEvaluator(ABC):
    """Abstract base class for modular policy condition evaluators."""

    @abstractmethod
    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        """Evaluate a specific condition aspect of a policy against SecurityContext."""
        pass

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        """Evaluate condition aspect and return outcome with human-readable reasoning."""
        res = self.evaluate(context, policy)
        return res, f"Condition evaluated to {res.value}"


class ExclusionConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates role and user exclusions."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        user_roles = context.roles
        user_id = context.user_id

        if policy.exclusions and any(r in policy.exclusions for r in user_roles):
            return ConditionResult.NO_MATCH

        if policy.excluded_users and user_id in policy.excluded_users:
            return ConditionResult.NO_MATCH

        return ConditionResult.MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        user_roles = context.roles
        user_id = context.user_id

        if policy.exclusions and any(r in policy.exclusions for r in user_roles):
            matched = [r.value if hasattr(r, 'value') else str(r) for r in user_roles if r in policy.exclusions]
            return ConditionResult.NO_MATCH, f"User role(s) {matched} excluded by policy"

        if policy.excluded_users and user_id in policy.excluded_users:
            return ConditionResult.NO_MATCH, f"User ID '{user_id}' excluded by policy"

        return ConditionResult.MATCH, "No role or user exclusions match"


class RoleConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates target roles condition."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        if not policy.target_roles:
            return ConditionResult.MATCH

        user_roles = context.roles
        if any(r in policy.target_roles for r in user_roles):
            return ConditionResult.MATCH
        return ConditionResult.NO_MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        if not policy.target_roles:
            return ConditionResult.MATCH, "No target roles specified (matches any role)"

        user_roles = context.roles
        target_strs = [r.value if hasattr(r, 'value') else str(r) for r in policy.target_roles]
        user_strs = [r.value if hasattr(r, 'value') else str(r) for r in user_roles]

        if any(r in policy.target_roles for r in user_roles):
            return ConditionResult.MATCH, f"User role(s) {user_strs} match target roles {target_strs}"
        return ConditionResult.NO_MATCH, f"User role(s) {user_strs} do not match target roles {target_strs}"


class AuthProtocolConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates target authentication protocol condition."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        if not policy.target_protocols:
            return ConditionResult.MATCH

        protocol = context.protocol
        if protocol in policy.target_protocols:
            return ConditionResult.MATCH
        return ConditionResult.NO_MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        if not policy.target_protocols:
            return ConditionResult.MATCH, "No target auth protocols specified (matches any protocol)"

        protocol = context.protocol
        proto_str = protocol.value if hasattr(protocol, 'value') else str(protocol)
        target_strs = [p.value if hasattr(p, 'value') else str(p) for p in policy.target_protocols]

        if protocol in policy.target_protocols:
            return ConditionResult.MATCH, f"Auth protocol '{proto_str}' matches target protocols {target_strs}"
        return ConditionResult.NO_MATCH, f"Auth protocol '{proto_str}' does not match target protocols {target_strs}"


class LocationConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates target location condition."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        if not policy.target_locations:
            return ConditionResult.MATCH

        loc = context.location
        if loc in policy.target_locations:
            return ConditionResult.MATCH
        return ConditionResult.NO_MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        if not policy.target_locations:
            return ConditionResult.MATCH, "No target locations specified (matches any location)"

        loc = context.location
        if loc in policy.target_locations:
            return ConditionResult.MATCH, f"Location '{loc}' matches target locations {policy.target_locations}"
        return ConditionResult.NO_MATCH, f"Location '{loc}' does not match target locations {policy.target_locations}"


class DeviceConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates target device managed and compliant conditions."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        if policy.target_device_managed is not None:
            status = context.get_status("device.managed")
            if status == SignalStatus.UNKNOWN or status == SignalStatus.UNAVAILABLE:
                return ConditionResult.UNKNOWN
            if context.device_managed != policy.target_device_managed:
                return ConditionResult.NO_MATCH

        if policy.target_device_compliant is not None:
            status = context.get_status("device.compliant")
            if status == SignalStatus.UNKNOWN or status == SignalStatus.UNAVAILABLE:
                return ConditionResult.UNKNOWN
            if context.device_compliant != policy.target_device_compliant:
                return ConditionResult.NO_MATCH

        return ConditionResult.MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        if policy.target_device_managed is not None:
            status = context.get_status("device.managed")
            if status == SignalStatus.UNKNOWN or status == SignalStatus.UNAVAILABLE:
                return ConditionResult.UNKNOWN, "Device management signal is unavailable/unknown"
            if context.device_managed != policy.target_device_managed:
                return ConditionResult.NO_MATCH, f"Device managed ({context.device_managed}) does not match target ({policy.target_device_managed})"

        if policy.target_device_compliant is not None:
            status = context.get_status("device.compliant")
            if status == SignalStatus.UNKNOWN or status == SignalStatus.UNAVAILABLE:
                return ConditionResult.UNKNOWN, "Device compliance signal is unavailable/unknown"
            if context.device_compliant != policy.target_device_compliant:
                return ConditionResult.NO_MATCH, f"Device compliant ({context.device_compliant}) does not match target ({policy.target_device_compliant})"

        return ConditionResult.MATCH, "Device criteria met"


class MfaConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates MFA completion state for MFA_REQUIRED policies."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        if policy.action == PolicyDecision.MFA_REQUIRED:
            if context.mfa_completed:
                return ConditionResult.NO_MATCH
        return ConditionResult.MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        if policy.action == PolicyDecision.MFA_REQUIRED:
            if context.mfa_completed:
                return ConditionResult.NO_MATCH, "MFA completed; MFA_REQUIRED policy requirement already satisfied"
            return ConditionResult.MATCH, "MFA incomplete; MFA_REQUIRED policy requirement triggered"
        return ConditionResult.MATCH, "Policy action is not MFA_REQUIRED"


class RiskConditionEvaluator(AbstractConditionEvaluator):
    """Evaluates target_risk_level policy condition against derived risk.level signal."""

    def evaluate(self, context: SecurityContext, policy: Policy) -> ConditionResult:
        target_risk = getattr(policy, "target_risk_level", None)
        if not target_risk:
            return ConditionResult.MATCH

        risk_signal = context.get_signal("risk.level")
        if not risk_signal or not risk_signal.is_available:
            return ConditionResult.NO_MATCH

        actual_val = str(risk_signal.value.value if hasattr(risk_signal.value, "value") else risk_signal.value).upper()
        target_val = str(target_risk.value if hasattr(target_risk, "value") else target_risk).upper()

        if actual_val == "UNKNOWN":
            if target_val == "UNKNOWN":
                return ConditionResult.MATCH
            return ConditionResult.NO_MATCH

        if actual_val == target_val:
            return ConditionResult.MATCH

        return ConditionResult.NO_MATCH

    def evaluate_with_reason(self, context: SecurityContext, policy: Policy) -> tuple[ConditionResult, str]:
        target_risk = getattr(policy, "target_risk_level", None)
        if not target_risk:
            return ConditionResult.MATCH, "No target risk level specified"

        risk_signal = context.get_signal("risk.level")
        if not risk_signal or not risk_signal.is_available:
            return ConditionResult.NO_MATCH, "Risk signal unavailable"

        actual_val = str(risk_signal.value.value if hasattr(risk_signal.value, "value") else risk_signal.value).upper()
        target_val = str(target_risk.value if hasattr(target_risk, "value") else target_risk).upper()

        if actual_val == "UNKNOWN":
            if target_val == "UNKNOWN":
                return ConditionResult.MATCH, "Risk level UNKNOWN matches target UNKNOWN"
            return ConditionResult.NO_MATCH, "Risk level UNKNOWN does not match target risk"

        if actual_val == target_val:
            return ConditionResult.MATCH, f"Actual risk level '{actual_val}' matches target risk level '{target_val}'"

        return ConditionResult.NO_MATCH, f"Actual risk level '{actual_val}' does not match target risk level '{target_val}'"

