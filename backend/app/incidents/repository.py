from datetime import datetime, timezone
import json
import uuid
from typing import Any
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.models import AuthenticatedUser
from app.db.models import DBIncident, DBIncidentEvent, DBPolicy
from app.incidents.models import (
    IncidentCreate,
    IncidentEventType,
    IncidentFilter,
    IncidentSeverity,
    IncidentStatus,
    IncidentSummaryStats,
)


class IncidentRepository:
    """Database repository for security incidents and activity timeline events using AsyncSession."""

    @staticmethod
    async def create_incident(
        db: AsyncSession,
        data: IncidentCreate,
        actor: AuthenticatedUser | str,
        correlation_id: str,
    ) -> DBIncident:
        incident_id = f"INC-{uuid.uuid4().hex[:10].upper()}"
        actor_id = actor.user_id if isinstance(actor, AuthenticatedUser) else str(actor)

        db_incident = DBIncident(
            id=incident_id,
            title=data.title,
            description=data.description,
            severity=data.severity.value if hasattr(data.severity, "value") else str(data.severity),
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            source_type=data.source_type,
            source_id=data.source_id,
            policy_id=data.policy_id,
            finding_id=data.finding_id,
            fingerprint=data.fingerprint,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=actor_id,
            assigned_to=data.assigned_to,
            correlation_id=correlation_id,
        )
        db.add(db_incident)
        await db.flush()

        # Add initial INCIDENT_CREATED timeline event
        actor_name = actor.username if isinstance(actor, AuthenticatedUser) else str(actor)
        init_event = DBIncidentEvent(
            id=f"INCEV-{uuid.uuid4().hex[:10].upper()}",
            incident_id=incident_id,
            event_type=IncidentEventType.INCIDENT_CREATED.value,
            actor_user_id=actor_id,
            actor_username=actor_name,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            metadata_json=json.dumps({
                "severity": db_incident.severity,
                "status": db_incident.status,
                "source_type": db_incident.source_type,
                "policy_id": db_incident.policy_id,
            }),
        )
        db.add(init_event)
        await db.commit()
        await db.refresh(db_incident)
        return db_incident

    @staticmethod
    async def get_incident(db: AsyncSession, incident_id: str) -> DBIncident | None:
        stmt = (
            select(DBIncident)
            .where(DBIncident.id == incident_id)
            .options(selectinload(DBIncident.events))
        )
        res = await db.scalars(stmt)
        return res.first()

    @staticmethod
    async def get_active_incident_by_fingerprint(db: AsyncSession, fingerprint: str) -> DBIncident | None:
        """Fetch active (non-resolved, non-dismissed) incident matching exact fingerprint."""
        if not fingerprint:
            return None
        active_statuses = [
            IncidentStatus.OPEN.value,
            IncidentStatus.ACKNOWLEDGED.value,
            IncidentStatus.INVESTIGATING.value,
            IncidentStatus.REOPENED.value,
        ]
        stmt = (
            select(DBIncident)
            .where(
                DBIncident.fingerprint == fingerprint,
                DBIncident.status.in_(active_statuses),
            )
            .order_by(DBIncident.created_at.desc())
        )
        res = await db.scalars(stmt)
        return res.first()

    @staticmethod
    async def list_incidents(db: AsyncSession, filter_params: IncidentFilter) -> tuple[list[DBIncident], int]:
        stmt = select(DBIncident).options(selectinload(DBIncident.events))

        if filter_params.status:
            stmt = stmt.where(DBIncident.status == filter_params.status.value)
        if filter_params.severity:
            stmt = stmt.where(DBIncident.severity == filter_params.severity.value)
        if filter_params.policy_id:
            stmt = stmt.where(DBIncident.policy_id == filter_params.policy_id)
        if filter_params.assigned_to:
            stmt = stmt.where(DBIncident.assigned_to == filter_params.assigned_to)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            stmt = stmt.where(
                or_(
                    DBIncident.title.ilike(pattern),
                    DBIncident.description.ilike(pattern),
                    DBIncident.id.ilike(pattern),
                    DBIncident.policy_id.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.scalar(count_stmt)) or 0

        # Pagination and ordering
        offset = (filter_params.page - 1) * filter_params.page_size
        stmt = stmt.order_by(DBIncident.created_at.desc()).offset(offset).limit(filter_params.page_size)

        res = await db.scalars(stmt)
        items = list(res.all())
        return items, total

    @staticmethod
    async def get_summary_stats(db: AsyncSession) -> IncidentSummaryStats:
        total = (await db.scalar(select(func.count(DBIncident.id)))) or 0
        open_cnt = (
            await db.scalar(
                select(func.count(DBIncident.id)).where(
                    DBIncident.status.in_([
                        IncidentStatus.OPEN.value,
                        IncidentStatus.ACKNOWLEDGED.value,
                        IncidentStatus.INVESTIGATING.value,
                        IncidentStatus.REOPENED.value,
                    ])
                )
            )
        ) or 0
        crit_cnt = (
            await db.scalar(
                select(func.count(DBIncident.id)).where(
                    DBIncident.severity == IncidentSeverity.CRITICAL.value,
                    DBIncident.status != IncidentStatus.RESOLVED.value,
                    DBIncident.status != IncidentStatus.DISMISSED.value,
                )
            )
        ) or 0
        high_cnt = (
            await db.scalar(
                select(func.count(DBIncident.id)).where(
                    DBIncident.severity == IncidentSeverity.HIGH.value,
                    DBIncident.status != IncidentStatus.RESOLVED.value,
                    DBIncident.status != IncidentStatus.DISMISSED.value,
                )
            )
        ) or 0
        unassigned_cnt = (
            await db.scalar(
                select(func.count(DBIncident.id)).where(
                    DBIncident.assigned_to.is_(None),
                    DBIncident.status != IncidentStatus.RESOLVED.value,
                    DBIncident.status != IncidentStatus.DISMISSED.value,
                )
            )
        ) or 0

        # Count distinct policy_ids in active incidents
        policies_at_risk = (
            await db.scalar(
                select(func.count(func.distinct(DBIncident.policy_id))).where(
                    DBIncident.policy_id.isnot(None),
                    DBIncident.status.in_([
                        IncidentStatus.OPEN.value,
                        IncidentStatus.ACKNOWLEDGED.value,
                        IncidentStatus.INVESTIGATING.value,
                        IncidentStatus.REOPENED.value,
                    ]),
                )
            )
        ) or 0

        return IncidentSummaryStats(
            total_incidents=total,
            open_incidents=open_cnt,
            critical_incidents=crit_cnt,
            high_incidents=high_cnt,
            unassigned_incidents=unassigned_cnt,
            policies_at_risk_count=policies_at_risk,
        )

    @staticmethod
    async def add_event(
        db: AsyncSession,
        incident_id: str,
        event_type: IncidentEventType | str,
        actor: AuthenticatedUser | str,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> DBIncidentEvent:
        actor_id = actor.user_id if isinstance(actor, AuthenticatedUser) else str(actor)
        actor_name = actor.username if isinstance(actor, AuthenticatedUser) else str(actor)
        ev_type = event_type.value if hasattr(event_type, "value") else str(event_type)

        event = DBIncidentEvent(
            id=f"INCEV-{uuid.uuid4().hex[:10].upper()}",
            incident_id=incident_id,
            event_type=ev_type,
            actor_user_id=actor_id,
            actor_username=actor_name,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            metadata_json=json.dumps(metadata or {}),
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event


incident_repository = IncidentRepository()
