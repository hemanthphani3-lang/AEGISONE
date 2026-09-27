import pytest
from app.auth.models import AuthenticatedUser
from app.engine.enums import AuthProtocol, UserRole
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.provider import (
    BrowserLocationProvider,
    DeviceSignalProvider,
    FutureProviderRegistry,
    KeycloakIdentityProvider,
)


def test_keycloak_identity_provider():
    provider = KeycloakIdentityProvider()
    user = AuthenticatedUser(user_id="user-123", username="testuser", roles=["ADMIN"], mfa_completed=True)
    signals = provider.get_signals_sync(user)

    sig_dict = {s.name: s for s in signals}
    assert "identity.user_id" in sig_dict
    assert sig_dict["identity.user_id"].value == "user-123"
    assert sig_dict["identity.user_id"].status == SignalStatus.AVAILABLE

    assert "identity.roles" in sig_dict
    assert sig_dict["identity.roles"].value == [UserRole.ADMIN]

    assert "auth.mfa_completed" in sig_dict
    assert sig_dict["auth.mfa_completed"].value is True


def test_browser_location_provider_success():
    provider = BrowserLocationProvider()
    signals = provider.get_signals_sync({"city": "Kakinada", "country": "IN"})

    assert len(signals) == 1
    sig = signals[0]
    assert sig.name == "location"
    assert sig.value == "KAKINADA"
    assert sig.status == SignalStatus.AVAILABLE
    assert sig.source == SignalSource.GEOLOCATION_PROVIDER


def test_browser_location_provider_permission_denied():
    provider = BrowserLocationProvider()
    signals = provider.get_signals_sync({"permission_status": "denied"})

    assert len(signals) == 1
    sig = signals[0]
    assert sig.name == "location"
    assert sig.value is None
    assert sig.status == SignalStatus.UNAVAILABLE
    assert "permission denied" in sig.metadata["explanation"].lower()


def test_device_signal_provider_unavailable():
    provider = DeviceSignalProvider()
    signals = provider.get_signals_sync({})

    sig_dict = {s.name: s for s in signals}
    assert "device.managed" in sig_dict
    assert sig_dict["device.managed"].value is None
    assert sig_dict["device.managed"].status == SignalStatus.UNAVAILABLE
    assert sig_dict["device.managed"].source == SignalSource.DEVICE_PROVIDER
    assert "unavailable" in sig_dict["device.managed"].metadata["explanation"].lower()

    assert "device.compliant" in sig_dict
    assert sig_dict["device.compliant"].value is None
    assert sig_dict["device.compliant"].status == SignalStatus.UNAVAILABLE
    assert sig_dict["device.compliant"].source == SignalSource.DEVICE_PROVIDER


def test_future_provider_registry():
    registry = FutureProviderRegistry()
    assert registry.get_provider("keycloak") is not None
    assert registry.get_provider("browser_location") is not None
    assert registry.get_provider("device_posture") is not None

    user = AuthenticatedUser(user_id="user-456", username="secuser", roles=["SECURITY_ADMIN"])
    collected = registry.collect_all(user)
    assert len(collected) >= 4
