from abc import ABC, abstractmethod
from typing import Any
from app.auth.models import AuthenticatedUser
from app.engine.enums import AuthProtocol, UserRole
from app.engine.models import RequestContext
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecuritySignal


class AbstractSignalProvider(ABC):
    """Abstract base class for security signal providers."""

    @abstractmethod
    def get_signals_sync(self, input_data: Any) -> list[SecuritySignal]:
        """Produce a list of SecuritySignal instances synchronously."""
        pass

    async def get_signals_async(self, input_data: Any) -> list[SecuritySignal]:
        """Produce a list of SecuritySignal instances asynchronously."""
        return self.get_signals_sync(input_data)


class KeycloakIdentityProvider(AbstractSignalProvider):
    """Signal provider that extracts identity signals from Keycloak AuthenticatedUser principal."""

    def get_signals_sync(self, input_data: Any) -> list[SecuritySignal]:
        if not isinstance(input_data, AuthenticatedUser):
            return [
                SecuritySignal(
                    name="identity.user_id",
                    status=SignalStatus.UNAVAILABLE,
                    source=SignalSource.KEYCLOAK,
                )
            ]

        mapped_roles: list[UserRole] = []
        for r in input_data.roles:
            try:
                role_enum = UserRole(r)
                if role_enum not in mapped_roles:
                    mapped_roles.append(role_enum)
            except ValueError:
                pass

        return [
            SecuritySignal(
                name="identity.user_id",
                value=input_data.user_id,
                source=SignalSource.KEYCLOAK,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
                metadata={"username": input_data.username},
            ),
            SecuritySignal(
                name="identity.roles",
                value=mapped_roles,
                source=SignalSource.KEYCLOAK,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
                metadata={"raw_roles": input_data.roles},
            ),
            SecuritySignal(
                name="auth.protocol",
                value=AuthProtocol.MODERN,
                source=SignalSource.KEYCLOAK,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            ),
            SecuritySignal(
                name="auth.mfa_completed",
                value=input_data.mfa_completed,
                source=SignalSource.KEYCLOAK,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
                metadata={"amr": input_data.amr},
            ),
        ]


class BrowserLocationProvider(AbstractSignalProvider):
    """Signal provider that extracts and normalizes browser geolocation signals safely."""

    def get_signals_sync(self, input_data: Any) -> list[SecuritySignal]:
        if not input_data:
            return [
                SecuritySignal(
                    name="location",
                    value=None,
                    source=SignalSource.GEOLOCATION_PROVIDER,
                    status=SignalStatus.UNAVAILABLE,
                    confidence=SignalConfidence.MEDIUM,
                    metadata={"explanation": "No location payload provided"},
                )
            ]

        # Handle payload dict or string
        loc_val = None
        status = SignalStatus.UNAVAILABLE
        explanation = "Location signal unavailable"

        if isinstance(input_data, dict):
            perm = input_data.get("permission_status")
            if perm == "denied":
                return [
                    SecuritySignal(
                        name="location",
                        value=None,
                        source=SignalSource.GEOLOCATION_PROVIDER,
                        status=SignalStatus.UNAVAILABLE,
                        confidence=SignalConfidence.MEDIUM,
                        metadata={"explanation": "Browser geolocation permission denied by user"},
                    )
                ]

            raw_loc = input_data.get("location") or input_data.get("city") or input_data.get("country")
            if raw_loc:
                loc_val = str(raw_loc).upper()
                status = SignalStatus.AVAILABLE
                explanation = "Normalized location from browser payload"
            elif "latitude" in input_data and "longitude" in input_data:
                # Coarse geographic normalization without storing precise lat/lon
                loc_val = input_data.get("region_code", "BROWSER_GEOLOCATION")
                status = SignalStatus.AVAILABLE
                explanation = "Normalized coarse geographic coordinates"
        elif isinstance(input_data, str) and input_data.strip():
            loc_val = input_data.strip().upper()
            status = SignalStatus.AVAILABLE
            explanation = "Normalized location string"

        return [
            SecuritySignal(
                name="location",
                value=loc_val,
                source=SignalSource.GEOLOCATION_PROVIDER,
                status=status,
                confidence=SignalConfidence.MEDIUM if status == SignalStatus.AVAILABLE else SignalConfidence.LOW,
                metadata={"explanation": explanation},
            )
        ]


class DeviceSignalProvider(AbstractSignalProvider):
    """Signal provider for enterprise device posture (managed/compliant). Explicitly reports UNAVAILABLE when no provider is connected."""

    def get_signals_sync(self, input_data: Any) -> list[SecuritySignal]:
        signals: list[SecuritySignal] = []

        dev_data = {}
        if isinstance(input_data, dict):
            dev_data = input_data.get("device", {}) if "device" in input_data else input_data
        elif hasattr(input_data, "device"):
            dev = getattr(input_data, "device")
            dev_data = {"managed": getattr(dev, "managed", None), "compliant": getattr(dev, "compliant", None)}

        managed = dev_data.get("managed") if isinstance(dev_data, dict) else None
        compliant = dev_data.get("compliant") if isinstance(dev_data, dict) else None

        # Device managed signal
        if isinstance(managed, bool):
            signals.append(
                SecuritySignal(
                    name="device.managed",
                    value=managed,
                    source=SignalSource.DEVICE_PROVIDER,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.MEDIUM,
                )
            )
        else:
            signals.append(
                SecuritySignal(
                    name="device.managed",
                    value=None,
                    source=SignalSource.DEVICE_PROVIDER,
                    status=SignalStatus.UNAVAILABLE,
                    confidence=SignalConfidence.LOW,
                    metadata={"explanation": "Device management information is unavailable because no device-management provider is configured."},
                )
            )

        # Device compliant signal
        if isinstance(compliant, bool):
            signals.append(
                SecuritySignal(
                    name="device.compliant",
                    value=compliant,
                    source=SignalSource.DEVICE_PROVIDER,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.MEDIUM,
                )
            )
        else:
            signals.append(
                SecuritySignal(
                    name="device.compliant",
                    value=None,
                    source=SignalSource.DEVICE_PROVIDER,
                    status=SignalStatus.UNAVAILABLE,
                    confidence=SignalConfidence.LOW,
                    metadata={"explanation": "Device compliance information is unavailable because no device-compliance provider is configured."},
                )
            )

        return signals


class LocalContextProvider(AbstractSignalProvider):
    """Signal provider for client/local context signals (combines location and device posture)."""

    def __init__(self) -> None:
        self.location_provider = BrowserLocationProvider()
        self.device_provider = DeviceSignalProvider()

    def get_signals_sync(self, input_data: Any) -> list[SecuritySignal]:
        signals: list[SecuritySignal] = []
        signals.extend(self.location_provider.get_signals_sync(input_data))
        signals.extend(self.device_provider.get_signals_sync(input_data))
        return signals


class FutureProviderRegistry:
    """Pluggable registry for managing security signal providers."""

    def __init__(self) -> None:
        self._providers: dict[str, AbstractSignalProvider] = {}
        self.register_defaults()

    def register_defaults(self) -> None:
        self.register("keycloak", KeycloakIdentityProvider())
        self.register("browser_location", BrowserLocationProvider())
        self.register("device_posture", DeviceSignalProvider())

    def register(self, name: str, provider: AbstractSignalProvider) -> None:
        self._providers[name] = provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def get_provider(self, name: str) -> AbstractSignalProvider | None:
        return self._providers.get(name)

    def collect_all(self, input_data: Any) -> list[SecuritySignal]:
        collected: list[SecuritySignal] = []
        for provider in self._providers.values():
            try:
                collected.extend(provider.get_signals_sync(input_data))
            except Exception:
                pass
        return collected


provider_registry = FutureProviderRegistry()

