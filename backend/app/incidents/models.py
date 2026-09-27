from datetime import datetime
from enum import Enum
import json
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, computed_field


class IncidentStatus(str, Enum):
    """Controlled lifecycle states for security incidents."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    REOPENED = "REOPENED"


class IncidentSeverity(str, Enum):
    """Severity classification levels for incidents."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentEventType(str, Enum):
    """Audit events recorded in incident timeline."""

    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_ACKNOWLEDGED = "INCIDENT_ACKNOWLEDGED"
    INCIDENT_ASSIGNED = "INCIDENT_ASSIGNED"
    INCIDENT_STATUS_CHANGED = "INCIDENT_STATUS_CHANGED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"
    INCIDENT_DISMISSED = "INCIDENT_DISMISSED"
    INCIDENT_COMMENTED = "INCIDENT_COMMENTED"
    INCIDENT_REOPENED = "INCIDENT_REOPENED"
    INCIDENT_REMEDIATED = "INCIDENT_REMEDIATED"


class RemediationAction(str, Enum):
    """Allowed remediation actions for incidents."""

    DISABLE_POLICY = "DISABLE_POLICY"
    ENABLE_POLICY = "ENABLE_POLICY"
    ROLLBACK_POLICY = "ROLLBACK_POLICY"


class IncidentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    source_type: str = "INTELLIGENCE_FINDING"
    source_id: str | None = None
    policy_id: str | None = None
    finding_id: str | None = None
    fingerprint: str | None = None
    assigned_to: str | None = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    status: IncidentStatus | None = None
    assigned_to: str | None = None
    resolution_summary: str | None = None


class IncidentEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    event_type: IncidentEventType
    actor_user_id: str
    actor_username: str | None = None
    timestamp: datetime
    correlation_id: str
    metadata_json: str = "{}"

    @computed_field
    def metadata(self) -> dict[str, Any]:
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}


class Incident(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_at: datetime | None = None
    assigned_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_summary: str | None = None
    correlation_id: str
    events: list[IncidentEvent] = Field(default_factory=list)


class IncidentFilter(BaseModel):
    status: IncidentStatus | None = None
    severity: IncidentSeverity | None = None
    policy_id: str | None = None
    assigned_to: str | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class IncidentSummaryStats(BaseModel):
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    high_incidents: int
    unassigned_incidents: int
    policies_at_risk_count: int


class RemediationRequest(BaseModel):
    action: RemediationAction
    expected_version: int | None = None
    target_version: int | None = None
    reason: str = Field(..., max_length=500)


class RemediationResponse(BaseModel):
    incident_id: str
    remediation_action: RemediationAction
    success: bool
    policy_id: str
    message: str
    timestamp: datetime
