from typing import Any
from fastapi import APIRouter, Depends, Query, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.authorization import Permission, require_permission
from app.auth.models import AuthenticatedUser
from app.core.correlation import get_correlation_id
from app.db.session import get_db_session
from app.incidents.models import (
    Incident,
    IncidentCreate,
    IncidentEvent,
    IncidentFilter,
    IncidentSeverity,
    IncidentStatus,
    IncidentSummaryStats,
    RemediationRequest,
    RemediationResponse,
)
from app.incidents.pipeline import intelligence_incident_pipeline
from app.incidents.repository import incident_repository
from app.incidents.service import incident_service

router = APIRouter(prefix="/incidents", tags=["Security Operations Center & Incidents"])


@router.get("", response_model=dict[str, Any])
async def list_incidents(
    status_filter: IncidentStatus | None = Query(None, alias="status"),
    severity: IncidentSeverity | None = Query(None),
    policy_id: str | None = Query(None),
    assigned_to: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.READ_INCIDENTS)),
):
    """List security incidents with filtering, search, and pagination."""
    filter_params = IncidentFilter(
        status=status_filter,
        severity=severity,
        policy_id=policy_id,
        assigned_to=assigned_to,
        search=search,
        page=page,
        page_size=page_size,
    )
    items, total = await incident_repository.list_incidents(db, filter_params)
    return {
        "incidents": [Incident.model_validate(inc) for inc in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats", response_model=IncidentSummaryStats)
async def get_incident_stats(
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.READ_INCIDENTS)),
):
    """Retrieve high-level incident summary metrics for the SOC dashboard."""
    return await incident_repository.get_summary_stats(db)


@router.post("/sync-intelligence", response_model=dict[str, Any])
async def sync_intelligence_incidents(
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Trigger automated intelligence scan to convert HIGH/CRITICAL findings into deduplicated incidents."""
    created_ids = await intelligence_incident_pipeline.sync_intelligence_incidents(
        db=db,
        actor=user,
        correlation_id=correlation_id,
    )
    return {
        "success": True,
        "created_count": len(created_ids),
        "created_incident_ids": created_ids,
    }


@router.get("/{incident_id}", response_model=Incident)
async def get_incident_detail(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.READ_INCIDENTS)),
):
    """Get full details of a specific security incident."""
    return await incident_service.get_incident_or_404(db, incident_id)


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_manual_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Manually create a new security incident."""
    return await incident_service.create_incident(
        db=db,
        data=data,
        actor=user,
        correlation_id=correlation_id,
    )


@router.post("/{incident_id}/acknowledge", response_model=Incident)
async def acknowledge_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Transition incident status to ACKNOWLEDGED."""
    return await incident_service.update_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.ACKNOWLEDGED,
        actor=user,
        correlation_id=correlation_id,
    )


@router.post("/{incident_id}/assign", response_model=Incident)
async def assign_incident(
    incident_id: str,
    assigned_to: str | None = Query(None, description="Username/ID of administrator to assign"),
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Assign or unassign an incident to an authorized administrator."""
    return await incident_service.assign_incident(
        db=db,
        incident_id=incident_id,
        assigned_to=assigned_to,
        actor=user,
        correlation_id=correlation_id,
    )


@router.post("/{incident_id}/resolve", response_model=Incident)
async def resolve_incident(
    incident_id: str,
    resolution_summary: str = Query(..., description="Explanation of resolution"),
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Transition incident status to RESOLVED with resolution summary."""
    return await incident_service.update_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.RESOLVED,
        actor=user,
        correlation_id=correlation_id,
        resolution_summary=resolution_summary,
    )


@router.post("/{incident_id}/dismiss", response_model=Incident)
async def dismiss_incident(
    incident_id: str,
    reason: str = Query(..., description="Reason for dismissing incident"),
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Transition incident status to DISMISSED."""
    return await incident_service.update_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.DISMISSED,
        actor=user,
        correlation_id=correlation_id,
        resolution_summary=reason,
    )


@router.post("/{incident_id}/reopen", response_model=Incident)
async def reopen_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Reopen a previously RESOLVED or DISMISSED incident."""
    return await incident_service.update_status(
        db=db,
        incident_id=incident_id,
        new_status=IncidentStatus.REOPENED,
        actor=user,
        correlation_id=correlation_id,
    )


@router.post("/{incident_id}/comment", response_model=Incident)
async def add_incident_comment(
    incident_id: str,
    comment: str = Query(..., description="Investigation note or comment"),
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.MANAGE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Add an investigation comment to an incident timeline."""
    return await incident_service.add_comment(
        db=db,
        incident_id=incident_id,
        comment=comment,
        actor=user,
        correlation_id=correlation_id,
    )


@router.get("/{incident_id}/events", response_model=list[IncidentEvent])
async def get_incident_events(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.READ_INCIDENTS)),
):
    """Retrieve immutable activity timeline events for an incident."""
    incident = await incident_service.get_incident_or_404(db, incident_id)
    return [IncidentEvent.model_validate(ev) for ev in incident.events]


@router.post("/{incident_id}/remediate", response_model=RemediationResponse)
async def remediate_incident(
    incident_id: str,
    request: RemediationRequest,
    db: AsyncSession = Depends(get_db_session),
    user: AuthenticatedUser = Security(require_permission(Permission.REMEDIATE_INCIDENTS)),
    correlation_id: str = Depends(get_correlation_id),
):
    """Perform policy remediation for an incident (e.g. disable policy or rollback version)."""
    return await incident_service.remediate_incident(
        db=db,
        incident_id=incident_id,
        request=request,
        actor=user,
        correlation_id=correlation_id,
    )
