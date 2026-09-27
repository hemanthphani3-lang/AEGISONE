from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.service import audit_service
from app.auth.models import AuthenticatedUser
from app.auth.verifier import jwt_verifier

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthenticatedUser:
    """FastAPI dependency that extracts and validates Keycloak Bearer token.

    Returns an AuthenticatedUser principal or raises HTTP 401 Unauthorized.
    """
    if credentials is None or not credentials.credentials:
        try:
            await audit_service.record_event(
                event_type=AuditEventType.AUTHENTICATION_FAILURE,
                action="AUTHENTICATE",
                resource_type="SYSTEM",
                outcome=AuditOutcome.FAILURE,
                metadata={"reason": "MISSING_TOKEN"},
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        user = jwt_verifier.verify_token(token)
    except Exception:
        try:
            await audit_service.record_event(
                event_type=AuditEventType.AUTHENTICATION_FAILURE,
                action="AUTHENTICATE",
                resource_type="SYSTEM",
                outcome=AuditOutcome.FAILURE,
                metadata={"reason": "INVALID_TOKEN"},
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        await audit_service.record_event(
            event_type=AuditEventType.AUTHENTICATION_SUCCESS,
            action="AUTHENTICATE",
            resource_type="SYSTEM",
            outcome=AuditOutcome.SUCCESS,
            actor=user,
        )
    except Exception:
        pass

    return user




