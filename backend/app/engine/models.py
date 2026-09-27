from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole


class DeviceInfo(BaseModel):
    """Device context attributes."""

    managed: bool | None = None
    compliant: bool | None = None


class AuthInfo(BaseModel):
    """Authentication context attributes."""

    protocol: AuthProtocol = AuthProtocol.MODERN
    mfa_completed: bool = False


class RequestContext(BaseModel):
    """Incoming request context to be evaluated against policies."""

    user_id: str
    role: UserRole | None = None
    roles: list[UserRole] = Field(default_factory=list)
    location: str = "UNKNOWN"
    device: DeviceInfo = Field(default_factory=DeviceInfo)
    authentication: AuthInfo

    def model_post_init(self, __context: Any) -> None:
        if self.role and not self.roles:
            self.roles = [self.role]
        elif self.roles and not self.role:
            self.role = self.roles[0]


class Policy(BaseModel):
    """Conditional access policy definition."""

    id: str
    name: str
    description: str
    enabled: bool = True
    target_roles: list[UserRole] = Field(default_factory=list)
    target_protocols: list[AuthProtocol] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    target_device_managed: bool | None = None
    target_device_compliant: bool | None = None
    target_risk_level: str | None = None
    action: PolicyDecision
    exclusions: list[UserRole] = Field(default_factory=list)
    excluded_users: list[str] = Field(default_factory=list)
    version: int = 1


class PolicyCreate(BaseModel):
    """Payload for creating a new policy."""

    id: str
    name: str
    description: str
    enabled: bool = True
    target_roles: list[UserRole] = Field(default_factory=list)
    target_protocols: list[AuthProtocol] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    target_device_managed: bool | None = None
    target_device_compliant: bool | None = None
    target_risk_level: str | None = None
    action: PolicyDecision
    exclusions: list[UserRole] = Field(default_factory=list)
    excluded_users: list[str] = Field(default_factory=list)
    version: int = 1


class PolicyUpdate(BaseModel):
    """Payload for updating mutable policy attributes."""

    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    target_roles: list[UserRole] | None = None
    target_protocols: list[AuthProtocol] | None = None
    target_locations: list[str] | None = None
    target_device_managed: bool | None = None
    target_device_compliant: bool | None = None
    target_risk_level: str | None = None
    action: PolicyDecision | None = None
    exclusions: list[UserRole] | None = None
    excluded_users: list[str] | None = None
    version: int | None = None
    expected_version: int | None = None


class PolicyValidationResponse(BaseModel):
    """Response model for policy definition validation."""

    valid: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PolicyListResponse(BaseModel):
    """API response model for listing policies."""

    policies: list[Policy]


class PolicyVersionSummary(BaseModel):
    """Structured summary of a policy version snapshot."""

    id: str
    policy_id: str
    version: int
    change_type: str
    changed_by_user_id: str
    changed_by_username: str | None = None
    changed_at: datetime
    correlation_id: str


class PolicyVersionDetail(BaseModel):
    """Full detail of a policy version snapshot."""

    id: str
    policy_id: str
    version: int
    snapshot: Policy
    change_type: str
    changed_by_user_id: str
    changed_by_username: str | None = None
    changed_at: datetime
    correlation_id: str


class PolicyVersionListResponse(BaseModel):
    """API response model for policy version history."""

    versions: list[PolicyVersionSummary]


class FieldDiff(BaseModel):
    """Difference representation for a single field."""

    previous: Any = None
    new: Any = None


class PolicyDiffResponse(BaseModel):
    """Response model for comparing two policy versions."""

    policy_id: str
    from_version: int
    to_version: int
    changed_fields: list[str] = Field(default_factory=list)
    field_diffs: dict[str, FieldDiff] = Field(default_factory=dict)
    added_collection_items: dict[str, list[Any]] = Field(default_factory=dict)
    removed_collection_items: dict[str, list[Any]] = Field(default_factory=dict)


class PolicyRollbackRequest(BaseModel):
    """Payload for rolling back a policy to a historical version."""

    target_version: int
    expected_current_version: int | None = None


class SignalSummary(BaseModel):
    """Structured summary of an evaluated security signal."""

    name: str
    value: Any = None
    source: str = "LOCAL"
    status: str = "AVAILABLE"
    confidence: str = "HIGH"


class ConditionDetail(BaseModel):
    """Detailed result of a single condition evaluation within a policy."""

    condition_type: str
    result: str
    reason: str


class PolicyTraceSummary(BaseModel):
    """Structured trace of policy matching evaluation."""

    policy_id: str
    policy_name: str
    enabled: bool = True
    matched: bool = False
    excluded: bool = False
    exclusion_reason: str | None = None
    action: PolicyDecision
    target_roles: list[UserRole] = Field(default_factory=list)
    target_protocols: list[AuthProtocol] = Field(default_factory=list)
    target_risk_level: str | None = None
    condition_details: list[ConditionDetail] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Result of policy evaluation against a RequestContext."""

    decision: PolicyDecision
    matched_policies: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    risk_level: str | None = None
    risk_factors: list[str] = Field(default_factory=list)
    risk_trace: str | None = None
    evaluated_signals: list[SignalSummary] = Field(default_factory=list)
    policy_traces: list[PolicyTraceSummary] = Field(default_factory=list)
    decision_precedence_trace: str | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None
