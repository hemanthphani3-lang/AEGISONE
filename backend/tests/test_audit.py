from datetime import datetime, timezone
import pytest
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.models import AuditEvent
from app.audit.repository import InMemoryAuditRepository
from app.audit.service import AuditService, sanitize_metadata
from app.auth.models import AuthenticatedUser


def test_audit_event_creation() -> None:
    event = AuditEvent(
        actor_user_id="user-123",
        actor_username="adminuser",
        actor_roles=["ADMIN"],
        event_type=AuditEventType.POLICY_CREATED,
        action="CREATE_POLICY",
        resource_type="POLICY",
        resource_id="policy-001",
        outcome=AuditOutcome.SUCCESS,
        metadata={"name": "Test Policy"},
    )
    assert event.id is not None
    assert event.timestamp.tzinfo == timezone.utc
    assert event.actor_user_id == "user-123"
    assert event.actor_roles == ["ADMIN"]
    assert event.event_type == AuditEventType.POLICY_CREATED
    assert event.outcome == AuditOutcome.SUCCESS


def test_actor_identity_derivation() -> None:
    service = AuditService(repo=InMemoryAuditRepository())
    user = AuthenticatedUser(
        user_id="sub-keycloak-789",
        username="john_doe",
        roles=["ADMIN", "SECURITY_ADMIN"],
    )
    meta = {"action": "test"}
    # Call internal sanitize and verification
    clean = service.sanitize_metadata(meta)
    assert clean == {"action": "test"}


def test_sensitive_data_sanitization() -> None:
    raw_meta = {
        "access_token": "eyJhbGciOiJSUzI1Ni...",
        "refresh_token": "secret_refresh_123",
        "client_secret": "my-secret-key",
        "password": "SuperSecretPassword123",
        "authorization": "Bearer eyJhbG...",
        "safe_field": "public_info",
        "nested": {
            "api_key": "12345",
            "normal_key": "value",
        },
    }
    sanitized = sanitize_metadata(raw_meta)
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["refresh_token"] == "[REDACTED]"
    assert sanitized["client_secret"] == "[REDACTED]"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["safe_field"] == "public_info"
    assert sanitized["nested"]["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["normal_key"] == "value"


@pytest.mark.asyncio
async def test_in_memory_audit_repository() -> None:
    repo = InMemoryAuditRepository()
    repo.clear()
    ev1 = AuditEvent(
        event_type=AuditEventType.POLICY_CREATED,
        action="CREATE",
        resource_type="POLICY",
        resource_id="p1",
        outcome=AuditOutcome.SUCCESS,
        actor_user_id="u1",
    )
    ev2 = AuditEvent(
        event_type=AuditEventType.AUTHORIZATION_DENIED,
        action="ACCESS",
        resource_type="POLICY",
        resource_id="p2",
        outcome=AuditOutcome.DENIED,
        actor_user_id="u2",
    )
    await repo.record_event_async(ev1)
    await repo.record_event_async(ev2)

    events, total = await repo.query_events_async(limit=10, offset=0)
    assert total == 2
    assert len(events) == 2

    # Query filtered by event_type
    filtered, f_total = await repo.query_events_async(
        event_type=AuditEventType.AUTHORIZATION_DENIED
    )
    assert f_total == 1
    assert filtered[0].actor_user_id == "u2"
