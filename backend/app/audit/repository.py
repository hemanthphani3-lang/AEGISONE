from abc import ABC, abstractmethod
from datetime import datetime
import threading
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.audit.converters import from_domain_audit_event, to_domain_audit_event
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.models import AuditEvent
from app.db.models import DBAuditEvent


class AbstractAuditRepository(ABC):
    """Abstract repository interface for security audit events."""

    @abstractmethod
    def record_event(self, event: AuditEvent) -> AuditEvent:
        """Record an audit event synchronously."""
        pass

    @abstractmethod
    async def record_event_async(self, event: AuditEvent) -> AuditEvent:
        """Record an audit event asynchronously."""
        pass

    @abstractmethod
    def query_events(
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
    ) -> tuple[list[AuditEvent], int]:
        """Query audit events with optional filtering and pagination (sync)."""
        pass

    @abstractmethod
    async def query_events_async(
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
    ) -> tuple[list[AuditEvent], int]:
        """Query audit events with optional filtering and pagination (async)."""
        pass

    @abstractmethod
    def get_by_id(self, event_id: str) -> AuditEvent | None:
        """Retrieve audit event by ID (sync)."""
        pass

    @abstractmethod
    async def get_by_id_async(self, event_id: str) -> AuditEvent | None:
        """Retrieve audit event by ID (async)."""
        pass


class InMemoryAuditRepository(AbstractAuditRepository):
    """In-memory implementation of audit event repository for testing and fallback."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = threading.Lock()

    def record_event(self, event: AuditEvent) -> AuditEvent:
        with self._lock:
            self._events.append(event)
        return event

    async def record_event_async(self, event: AuditEvent) -> AuditEvent:
        return self.record_event(event)

    def _matches_filter(
        self,
        event: AuditEvent,
        event_type: AuditEventType | str | None,
        actor_user_id: str | None,
        resource_type: str | None,
        resource_id: str | None,
        outcome: AuditOutcome | str | None,
        correlation_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> bool:
        if event_type is not None:
            val = event_type.value if isinstance(event_type, AuditEventType) else event_type
            if event.event_type.value != val:
                return False

        if actor_user_id is not None and event.actor_user_id != actor_user_id:
            return False

        if resource_type is not None and event.resource_type != resource_type:
            return False

        if resource_id is not None and event.resource_id != resource_id:
            return False

        if outcome is not None:
            val = outcome.value if isinstance(outcome, AuditOutcome) else outcome
            if event.outcome.value != val:
                return False

        if correlation_id is not None and event.correlation_id != correlation_id:
            return False

        if start_time is not None and event.timestamp < start_time:
            return False

        if end_time is not None and event.timestamp > end_time:
            return False

        return True

    def query_events(
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
    ) -> tuple[list[AuditEvent], int]:
        with self._lock:
            filtered = [
                e
                for e in self._events
                if self._matches_filter(
                    e,
                    event_type,
                    actor_user_id,
                    resource_type,
                    resource_id,
                    outcome,
                    correlation_id,
                    start_time,
                    end_time,
                )
            ]
            # Order newest first
            filtered.sort(key=lambda x: x.timestamp, reverse=True)
            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total

    async def query_events_async(
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
    ) -> tuple[list[AuditEvent], int]:
        return self.query_events(
            event_type,
            actor_user_id,
            resource_type,
            resource_id,
            outcome,
            correlation_id,
            start_time,
            end_time,
            limit,
            offset,
        )

    def get_by_id(self, event_id: str) -> AuditEvent | None:
        with self._lock:
            for e in self._events:
                if e.id == event_id:
                    return e
            return None

    async def get_by_id_async(self, event_id: str) -> AuditEvent | None:
        return self.get_by_id(event_id)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class PostgresAuditRepository(AbstractAuditRepository):
    """PostgreSQL implementation of audit event repository via SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def record_event(self, event: AuditEvent) -> AuditEvent:
        raise NotImplementedError("Use record_event_async for Postgres audit repository.")

    async def record_event_async(self, event: AuditEvent) -> AuditEvent:
        db_obj = from_domain_audit_event(event)
        self.session.add(db_obj)
        await self.session.flush()
        return event

    def _build_conditions(
        self,
        event_type: AuditEventType | str | None,
        actor_user_id: str | None,
        resource_type: str | None,
        resource_id: str | None,
        outcome: AuditOutcome | str | None,
        correlation_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[Any]:
        conditions = []
        if event_type is not None:
            val = event_type.value if isinstance(event_type, AuditEventType) else event_type
            conditions.append(DBAuditEvent.event_type == val)

        if actor_user_id is not None:
            conditions.append(DBAuditEvent.actor_user_id == actor_user_id)

        if resource_type is not None:
            conditions.append(DBAuditEvent.resource_type == resource_type)

        if resource_id is not None:
            conditions.append(DBAuditEvent.resource_id == resource_id)

        if outcome is not None:
            val = outcome.value if isinstance(outcome, AuditOutcome) else outcome
            conditions.append(DBAuditEvent.outcome == val)

        if correlation_id is not None:
            conditions.append(DBAuditEvent.correlation_id == correlation_id)

        if start_time is not None:
            conditions.append(DBAuditEvent.timestamp >= start_time)

        if end_time is not None:
            conditions.append(DBAuditEvent.timestamp <= end_time)

        return conditions

    def query_events(
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
    ) -> tuple[list[AuditEvent], int]:
        raise NotImplementedError("Use query_events_async for Postgres audit repository.")

    async def query_events_async(
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
    ) -> tuple[list[AuditEvent], int]:
        conditions = self._build_conditions(
            event_type,
            actor_user_id,
            resource_type,
            resource_id,
            outcome,
            correlation_id,
            start_time,
            end_time,
        )

        count_stmt = select(func.count(DBAuditEvent.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = select(DBAuditEvent)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(DBAuditEvent.timestamp.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        db_events = result.scalars().all()
        events = [to_domain_audit_event(e) for e in db_events]
        return events, total

    def get_by_id(self, event_id: str) -> AuditEvent | None:
        raise NotImplementedError("Use get_by_id_async for Postgres audit repository.")

    async def get_by_id_async(self, event_id: str) -> AuditEvent | None:
        stmt = select(DBAuditEvent).where(DBAuditEvent.id == event_id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return to_domain_audit_event(db_obj) if db_obj else None


audit_repository = InMemoryAuditRepository()
