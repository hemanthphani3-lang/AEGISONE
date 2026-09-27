from app.auth.context_builder import IdentityContextBuilder
from app.auth.models import AuthenticatedUser
from app.engine.enums import AuthProtocol, UserRole


def test_builder_admin_principal():
    """1. Valid ADMIN principal -> RequestContext contains ADMIN role."""
    user = AuthenticatedUser(
        user_id="sub-admin-123", username="admin01", roles=["ADMIN"]
    )
    context = IdentityContextBuilder.build_context(user)
    assert context.user_id == "sub-admin-123"
    assert UserRole.ADMIN in context.roles
    assert context.authentication.protocol == AuthProtocol.MODERN


def test_builder_student_principal():
    """2. Valid STUDENT principal -> RequestContext contains STUDENT role."""
    user = AuthenticatedUser(
        user_id="sub-student-456", username="student01", roles=["STUDENT"]
    )
    context = IdentityContextBuilder.build_context(user)
    assert context.user_id == "sub-student-456"
    assert UserRole.STUDENT in context.roles


def test_builder_multiple_recognized_roles():
    """3. Multiple recognized roles -> all preserved."""
    user = AuthenticatedUser(
        user_id="sub-multi-789",
        username="staff_admin",
        roles=["ADMIN", "STAFF"],
    )
    context = IdentityContextBuilder.build_context(user)
    assert set(context.roles) == {UserRole.ADMIN, UserRole.STAFF}


def test_builder_unknown_role_ignored():
    """4. Unknown role string -> safely ignored."""
    user = AuthenticatedUser(
        user_id="sub-unknown",
        username="unknown_role_user",
        roles=["STUDENT", "UNRECOGNIZED_ROLE_XYZ"],
    )
    context = IdentityContextBuilder.build_context(user)
    assert context.roles == [UserRole.STUDENT]


def test_builder_keycloak_oidc_protocol_always_modern():
    """6. Keycloak/OIDC principal -> protocol is MODERN."""
    user = AuthenticatedUser(
        user_id="sub-1", username="user1", roles=["STAFF"]
    )
    context = IdentityContextBuilder.build_context(user)
    assert context.authentication.protocol == AuthProtocol.MODERN


def test_builder_mfa_completed_when_claimed():
    """7. Token/claims indicating verified MFA -> MFA completed."""
    user = AuthenticatedUser(
        user_id="sub-mfa",
        username="mfa_user",
        roles=["ADMIN"],
        mfa_completed=True,
        amr=["otp"],
    )
    context = IdentityContextBuilder.build_context(user)
    assert context.authentication.mfa_completed is True


def test_builder_mfa_incomplete_without_evidence():
    """8. Token without trustworthy MFA evidence -> MFA incomplete."""
    user = AuthenticatedUser(
        user_id="sub-no-mfa",
        username="no_mfa_user",
        roles=["ADMIN"],
        mfa_completed=False,
    )
    context = IdentityContextBuilder.build_context(user)
    assert context.authentication.mfa_completed is False


def test_builder_untrusted_device_unknown():
    """9. No trusted device info -> device state remains None (unknown)."""
    user = AuthenticatedUser(user_id="sub-d", username="user_d", roles=["STUDENT"])
    context = IdentityContextBuilder.build_context(user)
    assert context.device.managed is None
    assert context.device.compliant is None


def test_builder_untrusted_location_unknown():
    """10. No trusted location info -> location remains UNKNOWN."""
    user = AuthenticatedUser(user_id="sub-l", username="user_l", roles=["STUDENT"])
    context = IdentityContextBuilder.build_context(user)
    assert context.location == "UNKNOWN"


def test_identity_anti_spoofing_protection():
    """11 & 12. Client attempting to spoof user_id, roles, or protocol in body is ignored."""
    user = AuthenticatedUser(
        user_id="real-student-sub", username="student01", roles=["STUDENT"]
    )
    malicious_client_data = {
        "user_id": "admin01",  # Attempt to spoof admin user ID
        "role": "ADMIN",  # Attempt to spoof admin role
        "roles": ["ADMIN", "SECURITY_ADMIN"],  # Attempt to spoof admin roles
        "authentication": {"protocol": "LEGACY", "mfa_completed": True},
    }

    context = IdentityContextBuilder.build_context(user, malicious_client_data)
    # MUST retain real student user_id and roles from authenticated principal
    assert context.user_id == "real-student-sub"
    assert context.roles == [UserRole.STUDENT]
    assert UserRole.ADMIN not in context.roles
    assert context.authentication.protocol == AuthProtocol.MODERN
