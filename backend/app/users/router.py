from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.authorization import Permission, require_permission
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser

from app.users.models import (
    UserCreateRequest,
    UserResetPasswordRequest,
    UserResponse,
    UserToggleRequest,
)
from app.users.service import keycloak_user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> list[UserResponse]:
    """List user accounts (requires ADMIN or SECURITY_ADMIN permission)."""
    return await keycloak_user_service.list_users()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> UserResponse:

    """Create a new user account in Keycloak and assign specified AegisOne role (requires ADMIN or SECURITY_ADMIN)."""

    # STUDENT and STAFF cannot create accounts
    if "STUDENT" in current_user.roles or "STAFF" in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create user accounts.",
        )

    # Privileged role validation: SECURITY_ADMIN cannot create ADMIN or BREAK_GLASS accounts
    if "ADMIN" not in current_user.roles and payload.role.upper() in {"ADMIN", "BREAK_GLASS"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only ADMIN role can assign privileged role '{payload.role}'.",
        )

    try:
        return await keycloak_user_service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/{user_id}/toggle")
async def toggle_user_status(
    user_id: str,
    payload: UserToggleRequest,
    current_user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> dict[str, str]:
    """Enable or disable a user account (requires ADMIN or SECURITY_ADMIN)."""
    success = await keycloak_user_service.toggle_user(user_id, payload.enabled)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{user_id}' not found.",
        )
    action = "enabled" if payload.enabled else "disabled"
    return {"message": f"User account '{user_id}' successfully {action}."}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    payload: UserResetPasswordRequest,
    current_user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> dict[str, str]:

    """Reset user password or trigger required-action email (requires ADMIN or SECURITY_ADMIN)."""
    success = await keycloak_user_service.reset_password(
        user_id, payload.temporary_password, payload.send_required_action_email
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{user_id}' not found or action failed.",
        )
    return {"message": f"Password reset action for user '{user_id}' completed successfully."}
