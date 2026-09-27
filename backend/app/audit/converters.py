import json
from datetime import datetime, timezone
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.models import AuditEvent
from app.db.models import DBAuditEvent


def to_domain_audit_event(db_event: DBAuditEvent) -> AuditEvent:
    """Convert SQLAlchemy DBAuditEvent to domain AuditEvent model."""
    try:
        roles = json.loads(db_event.actor_roles) if db_event.actor_roles else []
    except Exception:
        roles = []

    try:
        meta = json.loads(db_event.metadata_json) if db_event.metadata_json else {}
    except Exception:
        meta = {}

    # Ensure timestamp is timezone-aware UTC
    ts = db_event.timestamp
    if ts and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return AuditEvent(
        id=db_event.id,
        timestamp=ts,
        actor_user_id=db_event.actor_user_id,
        actor_username=db_event.actor_username,
        actor_roles=roles,
        event_type=AuditEventType(db_event.event_type),
        action=db_event.action,
        resource_type=db_event.resource_type,
        resource_id=db_event.resource_id,
        outcome=AuditOutcome(db_event.outcome),
        metadata=meta,
        correlation_id=db_event.correlation_id,
    )


def from_domain_audit_event(event: AuditEvent) -> DBAuditEvent:
    """Convert domain AuditEvent model to SQLAlchemy DBAuditEvent."""
    return DBAuditEvent(
        id=event.id,
        timestamp=event.timestamp,
        actor_user_id=event.actor_user_id,
        actor_username=event.actor_username,
        actor_roles=json.dumps(event.actor_roles),
        event_type=event.event_type.value,
        action=event.action,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        outcome=event.outcome.value,
        metadata_json=json.dumps(event.metadata),
        correlation_id=event.correlation_id,
    )
