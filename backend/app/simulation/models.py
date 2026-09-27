import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import RequestContext
from app.risk.enums import RiskLevel


class SimulationOverrides(BaseModel):
    """Typed model for controlled context override fields. Rejects unknown extra fields."""

    model_config = ConfigDict(extra="forbid")

    roles: list[UserRole] | None = Field(default=None, description="Simulated user roles")
    auth_protocol: AuthProtocol | None = Field(default=None, description="Simulated authentication protocol")
    mfa_completed: bool | None = Field(default=None, description="Simulated MFA completed flag")
    device_compliant: bool | None = Field(default=None, description="Simulated device compliance status")
    device_managed: bool | None = Field(default=None, description="Simulated device management status")
    location: str | None = Field(default=None, description="Simulated user location")
    network_type: str | None = Field(default=None, description="Simulated network type")
    risk_level: RiskLevel | None = Field(default=None, description="Direct risk level override")


class SimulationRequest(BaseModel):
    """Payload for initiating a policy evaluation simulation."""

    model_config = ConfigDict(extra="forbid")

    base_context: RequestContext | None = Field(default=None, description="Base RequestContext if provided")
    client_data: dict[str, Any] | None = Field(default=None, description="Client signal data for context overlay")
    overrides: SimulationOverrides = Field(default_factory=SimulationOverrides, description="Simulation overrides")
    policy_ids: list[str] | None = Field(default=None, description="Optional list of policy IDs to evaluate against")


class PolicyChangeTrace(BaseModel):
    """Trace details for a single policy whose match status changed between base and simulated evaluation."""

    policy_id: str
    policy_name: str
    base_matched: bool
    simulated_matched: bool
    change_summary: str


class SimulationTrace(BaseModel):
    """Comprehensive explainability trace detailing what changed during simulation and why."""

    base_decision: PolicyDecision
    simulated_decision: PolicyDecision
    decision_changed: bool
    base_risk: RiskLevel
    simulated_risk: RiskLevel
    risk_changed: bool
    overrides_applied: dict[str, Any]
    policy_changes: list[PolicyChangeTrace]
    explanation: str


from app.engine.models import EvaluationResult, PolicyTraceSummary


class SimulationResult(BaseModel):
    """Structured result of a policy simulation."""

    simulation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    base_decision: PolicyDecision
    simulated_decision: PolicyDecision
    decision_changed: bool
    base_risk: RiskLevel
    simulated_risk: RiskLevel
    risk_changed: bool
    overrides_applied: SimulationOverrides
    trace: SimulationTrace
    evaluation_result: EvaluationResult | None = None
