from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from app.engine.enums import AuthProtocol, UserRole
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus


class SecuritySignal(BaseModel):
    """Normalized security signal representation."""

    name: str
    value: Any = None
    source: SignalSource | str = SignalSource.LOCAL
    status: SignalStatus = SignalStatus.AVAILABLE
    confidence: SignalConfidence = SignalConfidence.HIGH
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        return self.status == SignalStatus.AVAILABLE and self.value is not None


class SecurityContext(BaseModel):
    """Normalized security context containing evaluated security signals."""

    signals: dict[str, SecuritySignal] = Field(default_factory=dict)

    def add_signal(self, signal: SecuritySignal) -> None:
        """Add or update a signal in the normalized context."""
        self.signals[signal.name] = signal

    def get_signal(self, name: str) -> SecuritySignal | None:
        """Retrieve a signal object by name."""
        return self.signals.get(name)

    def get_value(self, name: str, default: Any = None) -> Any:
        """Retrieve the value of a signal if available, otherwise return default."""
        sig = self.signals.get(name)
        if sig and sig.is_available:
            return sig.value
        return default

    def get_status(self, name: str) -> SignalStatus:
        """Retrieve the status of a signal (defaults to UNKNOWN if signal is missing)."""
        sig = self.signals.get(name)
        if sig is None:
            return SignalStatus.UNKNOWN
        return sig.status

    def has_signal(self, name: str) -> bool:
        """Check if an available signal exists in the context."""
        sig = self.signals.get(name)
        return sig is not None and sig.is_available

    # ------------------------------------------------------------------
    # Convenience / Legacy helper properties
    # ------------------------------------------------------------------

    @property
    def user_id(self) -> str:
        val = self.get_value("identity.user_id")
        return str(val) if val is not None else "anonymous"

    @property
    def roles(self) -> list[UserRole]:
        val = self.get_value("identity.roles", [])
        res: list[UserRole] = []
        if isinstance(val, list):
            for item in val:
                if isinstance(item, UserRole):
                    res.append(item)
                elif isinstance(item, str):
                    try:
                        res.append(UserRole(item))
                    except ValueError:
                        pass
        return res

    @property
    def role(self) -> UserRole | None:
        roles = self.roles
        return roles[0] if roles else None

    @property
    def location(self) -> str:
        return str(self.get_value("location", "UNKNOWN"))

    @property
    def protocol(self) -> AuthProtocol:
        val = self.get_value("auth.protocol")
        if isinstance(val, AuthProtocol):
            return val
        if isinstance(val, str):
            try:
                return AuthProtocol(val)
            except ValueError:
                pass
        return AuthProtocol.MODERN

    @property
    def mfa_completed(self) -> bool:
        return bool(self.get_value("auth.mfa_completed", False))

    @property
    def device_managed(self) -> bool | None:
        return self.get_value("device.managed", None)

    @property
    def device_compliant(self) -> bool | None:
        return self.get_value("device.compliant", None)
