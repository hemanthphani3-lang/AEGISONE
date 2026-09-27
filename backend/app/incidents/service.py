from datetime import datetime, timezone
import json
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.service import audit_service
from app.auth.models import AuthenticatedUser
from app.db.models import DBIncident
from app.incidents.models import (
    IncidentCreate,
    IncidentEventType,
    IncidentFilter,
    IncidentStatus,
    IncidentSummaryStats,
    RemediationAction,
    RemediationRequest,
    RemediationResponse,
)
from app.engine.models import PolicyRollbackRequest, PolicyUpdate
from app.incidents.repository import incident_repository
from app.services.policy_service import policy_service


ALLOWED_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.OPEN: {
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.DISMISSED,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.ACKNOWLEDGED: {
        IncidentStatus.INVESTIGATING,
        IncidentStatus.DISMISSED,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.INVESTIGATING: {
        IncidentStatus.RESOLVED,
        IncidentStatus.DISMISSED,
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.REOPENED,
    },
    IncidentStatus.DISMISSED: {
        IncidentStatus.REOPENED,
    },
    IncidentStatus.REOPENED: {
        IncidentStatus.INVESTIGATING,
        IncidentStatus.RESOLVED,
        IncidentStatus.DISMISSED,
    },
}


class IncidentService:
    """Service orchestrating incident lifecycle, state transitions, audit trail, and policy remediation."""

    @staticmethod
    def validate_transition(current_status: IncidentStatus, new_status: IncidentStatus) -> None:
        if current_status == new_status:
            return
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid incident status transition from '{current_status.value}' to '{new_status.value}'. Allowed target states: {[s.value for s in allowed]}.",
            )

    async def create_incident(
        self,
        db: AsyncSession,
        data: IncidentCreate,
        actor: AuthenticatedUser | str,
        correlation_id: str,
    ) -> DBIncident:
        incident = await incident_repository.create_incident(db, data, actor, correlation_id)

        # Record audit event
        actor_user = actor if isinstance(actor, AuthenticatedUser) else None
        await audit_service.record_event(
            event_type=AuditEventType.INCIDENT_CREATED,
            action="CREATE_INCIDENT",
            resource_type="INCIDENT",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS,
            actor=actor_user,
            metadata={
                "title": incident.title,
                "severity": incident.severity,
                "status": incident.status,
                "policy_id": incident.policy_id,
                "fingerprint": incident.fingerprint,
            },
            correlation_id=correlation_id,
        )
        return incident

    async def get_incident_or_404(self, db: AsyncSession, incident_id: str) -> DBIncident:
        incident = await incident_repository.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID '{incident_id}' not found.",
            )
        return incident

    async def update_status(
        self,
        db: AsyncSession,
        incident_id: str,
        new_status: IncidentStatus,
        actor: AuthenticatedUser,
        correlation_id: str,
        resolution_summary: str | None = None,
    ) -> DBIncident:
        incident = await self.get_incident_or_404(db, incident_id)
        current_status = IncidentStatus(incident.status)

        self.validate_transition(current_status, new_status)

        old_status_val = incident.status
        incident.status = new_status.value
        incident.updated_at = datetime.now(timezone.utc)

        if new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)
            incident.resolved_by = actor.user_id
            if resolution_summary:
                incident.resolution_summary = resolution_summary
        elif new_status == IncidentStatus.REOPENED:
            incident.resolved_at = None
            incident.resolved_by = None

        await db.commit()
        await db.refresh(incident)

        event_type_map = {
            IncidentStatus.ACKNOWLEDGED: IncidentEventType.INCIDENT_ACKNOWLEDGED,
            IncidentStatus.RESOLVED: IncidentEventType.INCIDENT_RESOLVED,
            IncidentStatus.DISMISSED: IncidentEventType.INCIDENT_DISMISSED,
            IncidentStatus.REOPENED: IncidentEventType.INCIDENT_REOPENED,
        }
        ev_type = event_type_map.get(new_status, IncidentEventType.INCIDENT_STATUS_CHANGED)

        await incident_repository.add_event(
            db=db,
            incident_id=incident.id,
            event_type=ev_type,
            actor=actor,
            correlation_id=correlation_id,
            metadata={
                "previous_status": old_status_val,
                "new_status": new_status.value,
                "resolution_summary": resolution_summary,
            },
        )

        await audit_service.record_event(
            event_type=AuditEventType.INCIDENT_STATUS_CHANGED,
            action=f"STATUS_CHANGE_{new_status.value}",
            resource_type="INCIDENT",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS,
            actor=actor,
            metadata={
                "previous_status": old_status_val,
                "new_status": new_status.value,
                "resolution_summary": resolution_summary,
            },
            correlation_id=correlation_id,
        )

        return incident

    async def assign_incident(
        self,
        db: AsyncSession,
        incident_id: str,
        assigned_to: str | None,
        actor: AuthenticatedUser,
        correlation_id: str,
    ) -> DBIncident:
        incident = await self.get_incident_or_404(db, incident_id)
        old_assigned = incident.assigned_to

        incident.assigned_to = assigned_to
        incident.assigned_at = datetime.now(timezone.utc) if assigned_to else None
        incident.assigned_by = actor.user_id if assigned_to else None
        incident.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(incident)

        await incident_repository.add_event(
            db=db,
            incident_id=incident.id,
            event_type=IncidentEventType.INCIDENT_ASSIGNED,
            actor=actor,
            correlation_id=correlation_id,
            metadata={
                "previous_assignee": old_assigned,
                "new_assignee": assigned_to,
            },
        )

        await audit_service.record_event(
            event_type=AuditEventType.INCIDENT_ASSIGNED,
            action="ASSIGN_INCIDENT",
            resource_type="INCIDENT",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS,
            actor=actor,
            metadata={
                "previous_assignee": old_assigned,
                "new_assignee": assigned_to,
            },
            correlation_id=correlation_id,
        )

        return incident

    async def add_comment(
        self,
        db: AsyncSession,
        incident_id: str,
        comment: str,
        actor: AuthenticatedUser,
        correlation_id: str,
    ) -> DBIncident:
        incident = await self.get_incident_or_404(db, incident_id)
        if not comment or not comment.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comment cannot be empty.",
            )

        incident.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(incident)

        await incident_repository.add_event(
            db=db,
            incident_id=incident.id,
            event_type=IncidentEventType.INCIDENT_COMMENTED,
            actor=actor,
            correlation_id=correlation_id,
            metadata={"comment": comment.strip()},
        )

        await audit_service.record_event(
            event_type=AuditEventType.INCIDENT_COMMENTED,
            action="ADD_INCIDENT_COMMENT",
            resource_type="INCIDENT",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS,
            actor=actor,
            metadata={"comment": comment.strip()},
            correlation_id=correlation_id,
        )

        return incident

    async def remediate_incident(
        self,
        db: AsyncSession,
        incident_id: str,
        request: RemediationRequest,
        actor: AuthenticatedUser,
        correlation_id: str,
    ) -> RemediationResponse:
        incident = await self.get_incident_or_404(db, incident_id)

        if not incident.policy_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incident '{incident_id}' has no associated policy_id for remediation.",
            )

        policy_id = incident.policy_id
        action_type = request.action
        msg = ""

        if action_type == RemediationAction.DISABLE_POLICY:
            await policy_service.update_policy(
                policy_id=policy_id,
                payload=PolicyUpdate(enabled=False, expected_version=request.expected_version),
                actor=actor,
            )
            msg = f"Policy '{policy_id}' was successfully disabled as part of incident remediation."
        elif action_type == RemediationAction.ENABLE_POLICY:
            await policy_service.update_policy(
                policy_id=policy_id,
                payload=PolicyUpdate(enabled=True, expected_version=request.expected_version),
                actor=actor,
            )
            msg = f"Policy '{policy_id}' was successfully enabled as part of incident remediation."
        elif action_type == RemediationAction.ROLLBACK_POLICY:
            if request.target_version is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="target_version is required for ROLLBACK_POLICY remediation action.",
                )
            req = PolicyRollbackRequest(
                target_version=request.target_version,
                expected_current_version=request.expected_version or 1,
            )
            await policy_service.rollback_policy(
                policy_id=policy_id,
                rollback_req=req,
                actor=actor,
            )
            msg = f"Policy '{policy_id}' was successfully rolled back to version {request.target_version}."

        # Add timeline event to incident
        await incident_repository.add_event(
            db=db,
            incident_id=incident.id,
            event_type=IncidentEventType.INCIDENT_REMEDIATED,
            actor=actor,
            correlation_id=correlation_id,
            metadata={
                "action": action_type.value,
                "policy_id": policy_id,
                "expected_version": request.expected_version,
                "target_version": request.target_version,
                "reason": request.reason,
            },
        )

        await audit_service.record_event(
            event_type=AuditEventType.INCIDENT_REMEDIATED,
            action=f"REMEDIATE_{action_type.value}",
            resource_type="INCIDENT",
            resource_id=incident.id,
            outcome=AuditOutcome.SUCCESS,
            actor=actor,
            metadata={
                "policy_id": policy_id,
                "action": action_type.value,
                "reason": request.reason,
            },
            correlation_id=correlation_id,
        )

        return RemediationResponse(
            incident_id=incident.id,
            remediation_action=action_type,
            success=True,
            policy_id=policy_id,
            message=msg,
            timestamp=datetime.now(timezone.utc),
        )


incident_service = IncidentService()
