from datetime import datetime, timezone
import pytest
from app.engine.enums import AuthProtocol, UserRole
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal


def test_security_signal_creation() -> None:
    sig = SecuritySignal(
        name="device.compliance",
        value="COMPLIANT",
        source=SignalSource.DEVICE_PROVIDER,
        status=SignalStatus.AVAILABLE,
        confidence=SignalConfidence.HIGH,
        metadata={"vendor": "Intune"},
    )
    assert sig.name == "device.compliance"
    assert sig.value == "COMPLIANT"
    assert sig.source == SignalSource.DEVICE_PROVIDER
    assert sig.status == SignalStatus.AVAILABLE
    assert sig.confidence == SignalConfidence.HIGH
    assert sig.timestamp.tzinfo == timezone.utc
    assert sig.is_available is True


def test_security_context_lookups() -> None:
    ctx = SecurityContext()
    sig1 = SecuritySignal(
        name="identity.user_id",
        value="usr-999",
        source=SignalSource.KEYCLOAK,
        status=SignalStatus.AVAILABLE,
    )
    sig2 = SecuritySignal(
        name="device.managed",
        value=True,
        source=SignalSource.LOCAL,
        status=SignalStatus.AVAILABLE,
    )
    sig3 = SecuritySignal(
        name="device.compliant",
        value=None,
        source=SignalSource.LOCAL,
        status=SignalStatus.UNKNOWN,
    )

    ctx.add_signal(sig1)
    ctx.add_signal(sig2)
    ctx.add_signal(sig3)

    assert ctx.has_signal("identity.user_id") is True
    assert ctx.get_value("identity.user_id") == "usr-999"
    assert ctx.get_value("device.managed") is True
    assert ctx.get_status("device.compliant") == SignalStatus.UNKNOWN
    assert ctx.get_status("nonexistent") == SignalStatus.UNKNOWN
    assert ctx.get_value("nonexistent", "default_val") == "default_val"


def test_security_context_convenience_properties() -> None:
    ctx = SecurityContext()
    ctx.add_signal(
        SecuritySignal(
            name="identity.user_id",
            value="user-abc",
            source=SignalSource.KEYCLOAK,
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="identity.roles",
            value=[UserRole.ADMIN, UserRole.SECURITY_ADMIN],
            source=SignalSource.KEYCLOAK,
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.protocol",
            value=AuthProtocol.MODERN,
            source=SignalSource.KEYCLOAK,
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.mfa_completed",
            value=True,
            source=SignalSource.KEYCLOAK,
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="location",
            value="US",
            source=SignalSource.LOCAL,
        )
    )

    assert ctx.user_id == "user-abc"
    assert ctx.roles == [UserRole.ADMIN, UserRole.SECURITY_ADMIN]
    assert ctx.role == UserRole.ADMIN
    assert ctx.protocol == AuthProtocol.MODERN
    assert ctx.mfa_completed is True
    assert ctx.location == "US"
