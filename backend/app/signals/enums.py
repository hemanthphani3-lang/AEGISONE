from enum import Enum


class SignalStatus(str, Enum):
    """Availability status of a security signal."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class SignalConfidence(str, Enum):
    """Confidence level of the signal provider observation."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SignalSource(str, Enum):
    """Categorized origin of a security signal."""

    KEYCLOAK = "KEYCLOAK"
    LOCAL = "LOCAL"
    DATABASE = "DATABASE"
    DEVICE_PROVIDER = "DEVICE_PROVIDER"
    NETWORK_PROVIDER = "NETWORK_PROVIDER"
    GEOLOCATION_PROVIDER = "GEOLOCATION_PROVIDER"
    RISK_PROVIDER = "RISK_PROVIDER"
    TEST_PROVIDER = "TEST_PROVIDER"
    UNKNOWN = "UNKNOWN"


class ConditionResult(str, Enum):
    """Outcome of evaluating a single policy condition against a SecurityContext."""

    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    UNKNOWN = "UNKNOWN"
