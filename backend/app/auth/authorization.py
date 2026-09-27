from enum import Enum
from typing import Callable
from fastapi import Depends, HTTPException, status
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.service import audit_service
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser
from app.engine.enums import UserRole


class Permission(str, Enum):
    """Extensible permission definitions for fine-grained capability checks."""

    READ_POLICY = "READ_POLICY"
    WRITE_POLICY = "WRITE_POLICY"
    DELETE_POLICY = "DELETE_POLICY"
    READ_AUDIT = "READ_AUDIT"
    RUN_SIMULATION = "RUN_SIMULATION"
    EVALUATE_ACCESS = "EVALUATE_ACCESS"
    VIEW_RISK = "VIEW_RISK"
    READ_INCIDENTS = "READ_INCIDENTS"
    MANAGE_INCIDENTS = "MANAGE_INCIDENTS"
    REMEDIATE_INCIDENTS = "REMEDIATE_INCIDENTS"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    UserRole.ADMIN.value: {
        Permission.READ_POLICY,
        Permission.WRITE_POLICY,
        Permission.DELETE_POLICY,
        Permission.READ_AUDIT,
        Permission.RUN_SIMULATION,
        Permission.EVALUATE_ACCESS,
        Permission.VIEW_RISK,
        Permission.READ_INCIDENTS,
        Permission.MANAGE_INCIDENTS,
        Permission.REMEDIATE_INCIDENTS,
    },
    UserRole.SECURITY_ADMIN.value: {
        Permission.READ_POLICY,
        Permission.WRITE_POLICY,
        Permission.DELETE_POLICY,
        Permission.READ_AUDIT,
        Permission.RUN_SIMULATION,
        Permission.EVALUATE_ACCESS,
        Permission.VIEW_RISK,
        Permission.READ_INCIDENTS,
        Permission.MANAGE_INCIDENTS,
        Permission.REMEDIATE_INCIDENTS,
    },
    UserRole.STAFF.value: {
        Permission.READ_POLICY,
        Permission.EVALUATE_ACCESS,
        Permission.VIEW_RISK,
        Permission.READ_INCIDENTS,
    },
    UserRole.STUDENT.value: {
        Permission.EVALUATE_ACCESS,
    },
    UserRole.BREAK_GLASS.value: {
        Permission.READ_POLICY,
        Permission.EVALUATE_ACCESS,
        Permission.READ_INCIDENTS,
    },
}

POLICY_WRITE_ROLES = {UserRole.ADMIN.value, UserRole.SECURITY_ADMIN.value}


def require_roles(
    *allowed_roles: UserRole | str, action: str = "PERFORM_ACTION", resource_type: str = "RESOURCE"
) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory that verifies an authenticated user possesses at least one required role (ANY match).

    Raises:
        HTTP 401 Unauthorized: If no valid authentication token is provided (via get_current_user).
        HTTP 403 Forbidden: If authenticated user lacks required roles.
    """
    allowed_set = {
        role.value if isinstance(role, UserRole) else str(role)
        for role in allowed_roles
    }

    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        user_roles_set = set(current_user.roles)
        if not user_roles_set.intersection(allowed_set):
            audit_service.record_event_sync(
                event_type=AuditEventType.AUTHORIZATION_DENIED,
                action=action,
                resource_type=resource_type,
                outcome=AuditOutcome.DENIED,
                actor=current_user,
                metadata={
                    "allowed_roles": sorted(list(allowed_set)),
                    "attempted_roles": current_user.roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to perform this action.",
            )
        return current_user

    return role_checker


def require_any_role(
    *allowed_roles: UserRole | str, action: str = "PERFORM_ACTION", resource_type: str = "RESOURCE"
) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Alias for require_roles verifying user possesses at least one allowed role."""
    return require_roles(*allowed_roles, action=action, resource_type=resource_type)


def require_all_roles(
    *required_roles: UserRole | str, action: str = "PERFORM_ACTION", resource_type: str = "RESOURCE"
) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory that verifies an authenticated user possesses ALL required roles.

    Raises:
        HTTP 401 Unauthorized: If no valid authentication token is provided (via get_current_user).
        HTTP 403 Forbidden: If authenticated user lacks any of the required roles.
    """
    required_set = {
        role.value if isinstance(role, UserRole) else str(role)
        for role in required_roles
    }

    def all_roles_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        user_roles_set = set(current_user.roles)
        if not required_set.issubset(user_roles_set):
            audit_service.record_event_sync(
                event_type=AuditEventType.AUTHORIZATION_DENIED,
                action=action,
                resource_type=resource_type,
                outcome=AuditOutcome.DENIED,
                actor=current_user,
                metadata={
                    "required_roles": sorted(list(required_set)),
                    "attempted_roles": current_user.roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to perform this action.",
            )
        return current_user

    return all_roles_checker


def require_permission(
    permission: Permission, action: str = "CHECK_PERMISSION", resource_type: str = "RESOURCE"
) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory that verifies an authenticated user possesses a specific domain permission.

    Raises:
        HTTP 401 Unauthorized: If no valid authentication token is provided (via get_current_user).
        HTTP 403 Forbidden: If user roles do not grant the required permission.
    """
    def permission_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        user_permissions: set[Permission] = set()
        for role in current_user.roles:
            user_permissions.update(ROLE_PERMISSIONS.get(role, set()))

        if permission not in user_permissions:
            audit_service.record_event_sync(
                event_type=AuditEventType.AUTHORIZATION_DENIED,
                action=action,
                resource_type=resource_type,
                outcome=AuditOutcome.DENIED,
                actor=current_user,
                metadata={
                    "required_permission": permission.value,
                    "attempted_roles": current_user.roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}",
            )
        return current_user

    return permission_checker


require_authenticated_user = get_current_user
require_policy_write_permission = require_roles(
    UserRole.ADMIN, UserRole.SECURITY_ADMIN, action="CREATE_POLICY", resource_type="POLICY"
)


