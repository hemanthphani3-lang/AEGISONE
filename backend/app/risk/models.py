from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.risk.enums import RiskLevel
from app.signals.enums import SignalConfidence


class RiskFactor(BaseModel):
    """Structured representation of an individual risk factor."""

    name: str
    severity: RiskLevel
    source: str = "RISK_ENGINE"
    reason: str
    signal_name: str | None = None


class RiskAssessment(BaseModel):
    """Result of deterministic risk evaluation on a SecurityContext."""

    level: RiskLevel
    factors: list[RiskFactor] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: SignalConfidence = SignalConfidence.HIGH
    trace: str = ""
