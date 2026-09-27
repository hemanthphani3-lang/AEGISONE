from datetime import datetime, timezone
import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.models import AuditEvent
from app.audit.repository import (
    AbstractAuditRepository,
    PostgresAuditRepository,
    audit_repository as default_in_memory_repo,
)
from app.auth.models import AuthenticatedUser
from app.core.correlation import get_correlation_id
from app.db.session import async_session_factory, check_database_connection

logger = logging.getLogger(__name__)

# Sensitive key names and patterns for sanitization
_EXACT_SENSITIVE_KEYS = {"key", "pwd"}
_SENSITIVE_PATTERNS = {
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "bearer",
    "secret",
    "client_secret",
    "password",
    "authorization",
    "auth_header",
    "api_key",
    "private_key",
    "credentials",
    "jwt",
    "cookie",
    "session_token",
}


def sanitize_metadata(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize metadata to strictly exclude secrets, tokens, passwords, and authorization headers."""
    if not meta:
        return {}
    clean: dict[str, Any] = {}
    for k, v in meta.items():
        k_lower = k.lower()
        is_sensitive = k_lower in _EXACT_SENSITIVE_KEYS or any(
            p in k_lower for p in _SENSITIVE_PATTERNS
        )
        if is_sensitive:
            clean[k] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k] = sanitize_metadata(v)
        elif isinstance(v, str) and ("bearer " in v.lower() or "eyj" in v.lower()):
            clean[k] = "[REDACTED]"
        else:
            clean[k] = v
    return clean


class AuditService:
    """Service layer for creating, sanitizing, and persisting security audit events."""

    def __init__(self, repo: AbstractAuditRepository | None = None) -> None:
        self._default_repo = repo or default_in_memory_repo

    def sanitize_metadata(self, meta: dict[str, Any] | None) -> dict[str, Any]:
        return sanitize_metadata(meta)

    def _build_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource_type: str,
        outcome: AuditOutcome,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: AuthenticatedUser | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        cid = correlation_id or get_correlation_id()
        actor_user_id = actor.user_id if actor else "anonymous"
        actor_username = actor.username if actor else None
        actor_roles = actor.roles if actor else []
        clean_meta = sanitize_metadata(metadata)

        return AuditEvent(
            timestamp=datetime.now(timezone.utc),
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            actor_roles=actor_roles,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            metadata=clean_meta,
            correlation_id=cid,
        )

    def record_event_sync(
        self,
        event_type: AuditEventType,
        action: str,
        resource_type: str,
        outcome: AuditOutcome,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: AuthenticatedUser | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Construct, sanitize, and record a security audit event synchronously."""
        event = self._build_event(
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            resource_id=resource_id,
            metadata=metadata,
            actor=actor,
            correlation_id=correlation_id,
        )
        self._default_repo.record_event(event)
        return event

    async def record_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource_type: str,
        outcome: AuditOutcome,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: AuthenticatedUser | None = None,
        correlation_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> AuditEvent:
        """Construct, sanitize, and record a security audit event asynchronously."""
        event = self._build_event(
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            resource_id=resource_id,
            metadata=metadata,
            actor=actor,
            correlation_id=correlation_id,
        )

        try:
            if session:
                pg_repo = PostgresAuditRepository(session)
                await pg_repo.record_event_async(event)
                await session.commit()
                self._default_repo.record_event(event)
                return event

            if await check_database_connection():
                async with async_session_factory() as db_session:
                    pg_repo = PostgresAuditRepository(db_session)
                    await pg_repo.record_event_async(event)
                    await db_session.commit()

            self._default_repo.record_event(event)
            return event
        except Exception as exc:
            logger.error(f"Audit event recording failed: {exc}", exc_info=True)
            try:
                self._default_repo.record_event(event)
            except Exception:
                pass
            return event

    async def query_events(
        self,
        event_type: AuditEventType | str | None = None,
        actor_user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        outcome: AuditOutcome | str | None = None,
        correlation_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        session: AsyncSession | None = None,
    ) -> tuple[list[AuditEvent], int]:
        """Query audit events from database or fallback in-memory repo."""
        if session:
            pg_repo = PostgresAuditRepository(session)
            return await pg_repo.query_events_async(
                event_type=event_type,
                actor_user_id=actor_user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                correlation_id=correlation_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset,
            )

        if await check_database_connection():
            async with async_session_factory() as db_session:
                pg_repo = PostgresAuditRepository(db_session)
                return await pg_repo.query_events_async(
                    event_type=event_type,
                    actor_user_id=actor_user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    outcome=outcome,
                    correlation_id=correlation_id,
                    start_time=start_time,
                    end_time=end_time,
                    limit=limit,
                    offset=offset,
                )

        return await self._default_repo.query_events_async(
            event_type=event_type,
            actor_user_id=actor_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            correlation_id=correlation_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )


audit_service = AuditService()

