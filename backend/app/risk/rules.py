from abc import ABC, abstractmethod
from app.engine.enums import AuthProtocol, UserRole
from app.risk.enums import RiskLevel
from app.risk.models import RiskFactor
from app.signals.enums import SignalStatus
from app.signals.models import SecurityContext

PRIVILEGED_ROLES = {UserRole.ADMIN, UserRole.SECURITY_ADMIN}


class AbstractRiskRule(ABC):
    """Abstract base class for deterministic risk evaluation rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique rule identifier name."""
        pass

    @abstractmethod
    def evaluate(self, context: SecurityContext) -> RiskFactor | None:
        """Inspect SecurityContext and return a RiskFactor if rule matches, else None."""
        pass


class PrivilegedMfaMissingRule(AbstractRiskRule):
    """Rule A: Privileged user (ADMIN / SECURITY_ADMIN) without MFA completed -> HIGH risk factor."""

    @property
    def name(self) -> str:
        return "privileged_mfa_missing"

    def evaluate(self, context: SecurityContext) -> RiskFactor | None:
        user_roles = context.roles
        is_privileged = any(r in PRIVILEGED_ROLES for r in user_roles)
        mfa_completed = context.mfa_completed

        if is_privileged and not mfa_completed:
            return RiskFactor(
                name=self.name,
                severity=RiskLevel.HIGH,
                source="IDENTITY",
                reason="Privileged user has not completed MFA",
                signal_name="auth.mfa_completed",
            )
        return None


class LegacyAuthenticationRule(AbstractRiskRule):
    """Rule B: Legacy authentication protocol used -> HIGH risk factor."""

    @property
    def name(self) -> str:
        return "legacy_authentication"

    def evaluate(self, context: SecurityContext) -> RiskFactor | None:
        if context.protocol == AuthProtocol.LEGACY:
            return RiskFactor(
                name=self.name,
                severity=RiskLevel.HIGH,
                source="AUTH",
                reason="Legacy authentication protocol used during sign-in",
                signal_name="auth.protocol",
            )
        return None


class UnknownAuthStateRule(AbstractRiskRule):
    """Rule C: Unknown or unavailable authentication state -> UNKNOWN risk factor."""

    @property
    def name(self) -> str:
        return "unknown_auth_state"

    def evaluate(self, context: SecurityContext) -> RiskFactor | None:
        status = context.get_status("auth.protocol")
        if status in (SignalStatus.UNKNOWN, SignalStatus.UNAVAILABLE, SignalStatus.ERROR):
            return RiskFactor(
                name=self.name,
                severity=RiskLevel.UNKNOWN,
                source="AUTH",
                reason="Authentication protocol state is unknown or unavailable",
                signal_name="auth.protocol",
            )
        return None


class MockDeviceUnknownRule(AbstractRiskRule):
    """Rule D (Optional/Mock): Device compliance status is UNKNOWN -> MEDIUM risk factor."""

    @property
    def name(self) -> str:
        return "device_unknown"

    def evaluate(self, context: SecurityContext) -> RiskFactor | None:
        status = context.get_status("device.compliant")
        if status in (SignalStatus.UNKNOWN, SignalStatus.UNAVAILABLE):
            return RiskFactor(
                name=self.name,
                severity=RiskLevel.MEDIUM,
                source="DEVICE",
                reason="Device compliance status is unknown",
                signal_name="device.compliant",
            )
        return None
