import pytest
from app.auth.models import AuthenticatedUser
from app.engine.enums import AuthProtocol, UserRole
from app.engine.models import AuthInfo, DeviceInfo, RequestContext
from app.signals.aggregator import ContextAggregator
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecuritySignal
from app.signals.provider import AbstractSignalProvider


class FailingSignalProvider(AbstractSignalProvider):
    """Mock provider that simulates an external provider failure."""

    def get_signals_sync(self, input_data: any) -> list[SecuritySignal]:
        return [
            SecuritySignal(
                name="device.compliance",
                value=None,
                source=SignalSource.DEVICE_PROVIDER,
                status=SignalStatus.ERROR,
                confidence=SignalConfidence.LOW,
                metadata={"error": "Connection timed out"},
            )
        ]


def test_aggregator_from_authenticated_user() -> None:
    aggregator = ContextAggregator()
    user = AuthenticatedUser(
        user_id="keycloak-sub-555",
        username="admin_user",
        roles=["ADMIN"],
        mfa_completed=True,
    )
    client_data = {"location": "EU", "device": {"managed": True, "compliant": True}}

    ctx = aggregator.aggregate_sync(principal=user, client_data=client_data)

    assert ctx.user_id == "keycloak-sub-555"
    assert ctx.roles == [UserRole.ADMIN]
    assert ctx.mfa_completed is True
    assert ctx.location == "EU"
    assert ctx.device_managed is True
    assert ctx.device_compliant is True


def test_aggregator_from_legacy_request_context() -> None:
    req_context = RequestContext(
        user_id="legacy-user-7",
        role=UserRole.STAFF,
        location="US",
        device=DeviceInfo(managed=True, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.LEGACY, mfa_completed=False),
    )

    ctx = ContextAggregator.from_request_context(req_context)

    assert ctx.user_id == "legacy-user-7"
    assert ctx.roles == [UserRole.STAFF]
    assert ctx.protocol == AuthProtocol.LEGACY
    assert ctx.mfa_completed is False
    assert ctx.location == "US"
    assert ctx.device_managed is True
    assert ctx.device_compliant is False


def test_provider_failure_handling() -> None:
    """Verify that a failing provider returns status=ERROR and value=None rather than value=False."""
    failing_provider = FailingSignalProvider()
    signals = failing_provider.get_signals_sync(None)

    assert len(signals) == 1
    sig = signals[0]
    assert sig.status == SignalStatus.ERROR
    assert sig.value is None
    # Ensure it is NOT automatically treated as boolean False
    assert sig.value is not False
