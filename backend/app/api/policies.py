from typing import Any
from fastapi import APIRouter, Depends, Query, status
from app.auth.authorization import (
    Permission,
    require_permission,
)
from app.auth.models import AuthenticatedUser
from app.engine.models import (
    Policy,
    PolicyCreate,
    PolicyDiffResponse,
    PolicyListResponse,
    PolicyRollbackRequest,
    PolicyUpdate,
    PolicyValidationResponse,
    PolicyVersionDetail,
    PolicyVersionListResponse,
)
from app.services.policy_service import policy_service

router = APIRouter()


@router.post("/policies/validate", response_model=PolicyValidationResponse)
async def validate_policy(
    payload: dict[str, Any],
    user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> PolicyValidationResponse:
    """Validate policy definition payload before creation or edit (Requires WRITE_POLICY permission)."""
    is_create = "id" in payload and payload["id"] is not None
    return policy_service.validate_policy_payload(payload, is_create=is_create)


@router.post("/policies/{policy_id}/validate", response_model=PolicyValidationResponse)
async def validate_existing_policy(
    policy_id: str,
    payload: dict[str, Any],
    user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> PolicyValidationResponse:
    """Validate changes to an existing policy before saving (Requires WRITE_POLICY permission)."""
    await policy_service.get_policy_by_id(policy_id)
    return policy_service.validate_policy_payload(payload, is_create=False)


@router.get("/policies", response_model=PolicyListResponse)
async def get_policies(
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> PolicyListResponse:
    """Retrieve all available conditional access policies (Requires READ_POLICY permission)."""
    policies = await policy_service.list_policies()
    return PolicyListResponse(policies=policies)


@router.get("/policies/{policy_id}", response_model=Policy)
async def get_policy(
    policy_id: str,
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> Policy:
    """Retrieve a single policy by ID (Requires READ_POLICY permission)."""
    return await policy_service.get_policy_by_id(policy_id)


@router.post("/policies", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate,
    user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> Policy:
    """Create a new policy (Requires WRITE_POLICY permission: ADMIN or SECURITY_ADMIN)."""
    return await policy_service.create_policy(payload, actor=user)


@router.patch("/policies/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: str,
    payload: PolicyUpdate,
    user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> Policy:
    """Safely update mutable fields of an existing policy (Requires WRITE_POLICY permission: ADMIN or SECURITY_ADMIN)."""
    return await policy_service.update_policy(policy_id, payload, actor=user)


@router.delete("/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    user: AuthenticatedUser = Depends(require_permission(Permission.DELETE_POLICY)),
) -> dict[str, str]:
    """Delete a policy by ID (Requires DELETE_POLICY permission: ADMIN or SECURITY_ADMIN)."""
    return await policy_service.delete_policy(policy_id, actor=user)


@router.get("/policies/{policy_id}/versions", response_model=PolicyVersionListResponse)
async def get_policy_versions(
    policy_id: str,
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> PolicyVersionListResponse:
    """Retrieve historical version snapshot summaries for a policy (Requires READ_POLICY permission)."""
    return await policy_service.get_policy_versions(policy_id)


@router.get("/policies/{policy_id}/versions/{version}", response_model=PolicyVersionDetail)
async def get_policy_version_detail(
    policy_id: str,
    version: int,
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> PolicyVersionDetail:
    """Retrieve full detail of a historical version snapshot (Requires READ_POLICY permission)."""
    return await policy_service.get_policy_version_detail(policy_id, version)


@router.get("/policies/{policy_id}/versions/{version}/diff", response_model=PolicyDiffResponse)
async def get_policy_version_diff(
    policy_id: str,
    version: int,
    against_version: int | None = Query(default=None),
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> PolicyDiffResponse:
    """Compare two policy versions and return field-level diffs (Requires READ_POLICY permission)."""
    return await policy_service.get_policy_version_diff(policy_id, version, against_version)


@router.post("/policies/{policy_id}/rollback", response_model=Policy)
async def rollback_policy(
    policy_id: str,
    payload: PolicyRollbackRequest,
    user: AuthenticatedUser = Depends(require_permission(Permission.WRITE_POLICY)),
) -> Policy:
    """Rollback policy to a historical version snapshot as a brand new current version (Requires WRITE_POLICY permission)."""
    return await policy_service.rollback_policy(policy_id, payload, actor=user)
