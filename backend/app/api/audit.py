from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.models import AuditEventListResponse
from app.audit.service import audit_service
from app.auth.authorization import Permission, require_permission
from app.auth.models import AuthenticatedUser
from app.db.session import async_session_factory, check_database_connection

router = APIRouter()


@router.get("/audit/events", response_model=AuditEventListResponse)
async def get_audit_events(
    event_type: AuditEventType | str | None = None,
    actor_user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: AuditOutcome | str | None = None,
    correlation_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int | None = Query(default=None, ge=0),
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_AUDIT)),
) -> AuditEventListResponse:
    """Retrieve security audit events with optional filtering and pagination.

    Requires READ_AUDIT permission (ADMIN and SECURITY_ADMIN roles).
    """
    # Calculate limit and offset from page / page_size or direct limit / offset
    if page is not None or page_size is not None:
        effective_page_size = page_size if page_size is not None else 25
        effective_page = page if page is not None else 1
        effective_limit = effective_page_size
        effective_offset = (effective_page - 1) * effective_page_size
    else:
        effective_limit = limit if limit is not None else 25
        effective_offset = offset if offset is not None else 0
        effective_page_size = effective_limit
        effective_page = (effective_offset // effective_limit) + 1 if effective_limit > 0 else 1

    session = None
    try:
        if await check_database_connection():
            session = async_session_factory()
            events, total = await audit_service.query_events(
                event_type=event_type,
                actor_user_id=actor_user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                correlation_id=correlation_id,
                start_time=start_time,
                end_time=end_time,
                limit=effective_limit,
                offset=effective_offset,
                session=session,
            )
        else:
            events, total = await audit_service.query_events(
                event_type=event_type,
                actor_user_id=actor_user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                correlation_id=correlation_id,
                start_time=start_time,
                end_time=end_time,
                limit=effective_limit,
                offset=effective_offset,
            )

        return AuditEventListResponse(
            items=events,
            events=events,
            page=effective_page,
            page_size=effective_page_size,
            total=total,
            limit=effective_limit,
            offset=effective_offset,
        )
    finally:
        if session:
            await session.close()

