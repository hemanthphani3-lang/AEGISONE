import pytest
from fastapi import HTTPException
from app.auth.authorization import (
    Permission,
    require_all_roles,
    require_any_role,
    require_permission,
    require_policy_write_permission,
    require_roles,
)
from app.auth.models import AuthenticatedUser
from app.engine.enums import UserRole


def test_require_roles_single_valid_role():
    """Verify require_roles passes when user has the allowed role."""
    user = AuthenticatedUser(user_id="u1", username="admin01", roles=["ADMIN"])
    checker = require_roles(UserRole.ADMIN)
    result = checker(user)
    assert result.user_id == "u1"


def test_require_roles_single_invalid_role_raises_403():
    """Verify require_roles raises HTTP 403 when user lacks required role."""
    user = AuthenticatedUser(user_id="u2", username="student01", roles=["STUDENT"])
    checker = require_roles(UserRole.ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        checker(user)
    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in exc_info.value.detail


def test_require_any_role_matches_one():
    """Verify require_any_role passes if user has at least one matching role."""
    user = AuthenticatedUser(user_id="u3", username="staff01", roles=["STAFF"])
    checker = require_any_role(UserRole.ADMIN, UserRole.STAFF)
    result = checker(user)
    assert result.username == "staff01"


def test_require_all_roles_passes_when_all_present():
    """Verify require_all_roles passes when user possesses all specified roles."""
    user = AuthenticatedUser(user_id="u4", username="multi01", roles=["STAFF", "ADMIN"])
    checker = require_all_roles(UserRole.ADMIN, UserRole.STAFF)
    result = checker(user)
    assert result.username == "multi01"


def test_require_all_roles_fails_when_one_missing():
    """Verify require_all_roles raises 403 when user lacks any one of the required roles."""
    user = AuthenticatedUser(user_id="u5", username="admin_only", roles=["ADMIN"])
    checker = require_all_roles(UserRole.ADMIN, UserRole.SECURITY_ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        checker(user)
    assert exc_info.value.status_code == 403


def test_permission_admin_has_full_permissions():
    """Verify ADMIN role possesses all domain permissions."""
    user = AuthenticatedUser(user_id="a1", username="admin01", roles=["ADMIN"])
    for perm in Permission:
        checker = require_permission(perm)
        res = checker(user)
        assert res.username == "admin01"


def test_permission_student_has_limited_permissions():
    """Verify STUDENT has EVALUATE_ACCESS permission but lacks WRITE_POLICY (403)."""
    user = AuthenticatedUser(user_id="s1", username="student01", roles=["STUDENT"])
    
    # Allowed
    res = require_permission(Permission.EVALUATE_ACCESS)(user)
    assert res.username == "student01"

    # Denied
    with pytest.raises(HTTPException) as exc_info:
        require_permission(Permission.WRITE_POLICY)(user)
    assert exc_info.value.status_code == 403
    assert "Missing required permission" in exc_info.value.detail


def test_permission_break_glass_role():
    """Verify BREAK_GLASS has READ_POLICY and EVALUATE_ACCESS but lacks WRITE_POLICY."""
    user = AuthenticatedUser(user_id="bg1", username="bg01", roles=["BREAK_GLASS"])
    
    # Allowed
    res_read = require_permission(Permission.READ_POLICY)(user)
    assert res_read.username == "bg01"

    # Denied
    with pytest.raises(HTTPException) as exc_info:
        require_permission(Permission.WRITE_POLICY)(user)
    assert exc_info.value.status_code == 403


def test_unknown_role_denied_access():
    """Verify unrecognized/unknown role cannot pass role checks (403)."""
    user = AuthenticatedUser(user_id="x1", username="unknown_user", roles=["UNKNOWN_ROLE"])
    checker = require_roles(UserRole.STUDENT, UserRole.STAFF, UserRole.ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        checker(user)
    assert exc_info.value.status_code == 403


def test_student_policy_write_permission_denied():
    """Verify STUDENT is denied policy write permission (403)."""
    user = AuthenticatedUser(user_id="s1", username="student01", roles=["STUDENT"])
    with pytest.raises(HTTPException) as exc_info:
        require_policy_write_permission(user)
    assert exc_info.value.status_code == 403


def test_staff_policy_write_permission_denied():
    """Verify STAFF is denied policy write permission (403)."""
    user = AuthenticatedUser(user_id="st1", username="staff01", roles=["STAFF"])
    with pytest.raises(HTTPException) as exc_info:
        require_policy_write_permission(user)
    assert exc_info.value.status_code == 403


def test_admin_policy_write_permission_allowed():
    """Verify ADMIN is granted policy write permission."""
    user = AuthenticatedUser(user_id="a1", username="admin01", roles=["ADMIN"])
    result = require_policy_write_permission(user)
    assert result.username == "admin01"


def test_security_admin_policy_write_permission_allowed():
    """Verify SECURITY_ADMIN is granted policy write permission."""
    user = AuthenticatedUser(
        user_id="sa1", username="secadmin01", roles=["SECURITY_ADMIN"]
    )
    result = require_policy_write_permission(user)
    assert result.username == "secadmin01"
