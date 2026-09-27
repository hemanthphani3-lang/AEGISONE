from enum import Enum


class RiskLevel(str, Enum):
    """Controlled risk levels produced by RiskEvaluator."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"
