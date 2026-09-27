from datetime import datetime, timezone
from typing import Any
import uuid
from pydantic import BaseModel, Field
from app.audit.enums import AuditEventType, AuditOutcome


class AuditEvent(BaseModel):
    """Structured domain model representing a security audit event."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_user_id: str = "anonymous"
    actor_username: str | None = None
    actor_roles: list[str] = Field(default_factory=list)
    event_type: AuditEventType
    action: str
    resource_type: str
    resource_id: str | None = None
    outcome: AuditOutcome
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class AuditEventListResponse(BaseModel):
    """Paginated API response for audit events supporting items/page/page_size and events/limit/offset."""

    items: list[AuditEvent] = Field(default_factory=list)
    events: list[AuditEvent] = Field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0
    limit: int = 25
    offset: int = 0

