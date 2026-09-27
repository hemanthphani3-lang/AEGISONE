import pytest
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.evaluator import PolicyEvaluator
from app.engine.models import (
    AuthInfo,
    DeviceInfo,
    Policy,
    RequestContext,
)
from app.engine.repository import InMemoryPolicyRepository

evaluator = PolicyEvaluator()


def test_unit_student_modern_mfa_completed_allow():
    """1. Student + Modern + MFA completed -> ALLOW."""
    context = RequestContext(
        user_id="s1",
        role=UserRole.STUDENT,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=True),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.ALLOW
    assert result.matched_policies == []


def test_unit_student_modern_mfa_not_completed_allow():
    """2. Student + Modern + MFA not completed -> ALLOW (No policy targets student)."""
    context = RequestContext(
        user_id="s2",
        role=UserRole.STUDENT,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.ALLOW
    assert result.matched_policies == []


def test_unit_admin_modern_mfa_completed_allow():
    """3. Admin + Modern + MFA completed -> ALLOW."""
    context = RequestContext(
        user_id="a1",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=True),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.ALLOW


def test_unit_admin_modern_mfa_not_completed_mfa_required():
    """4. Admin + Modern + MFA not completed -> MFA_REQUIRED."""
    context = RequestContext(
        user_id="a2",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.MFA_REQUIRED
    assert "admin-mfa" in result.matched_policies


def test_unit_security_admin_modern_mfa_not_completed_mfa_required():
    """5. Security Admin + Modern + MFA not completed -> MFA_REQUIRED."""
    context = RequestContext(
        user_id="sa1",
        role=UserRole.SECURITY_ADMIN,
        location="US",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.MFA_REQUIRED


def test_unit_student_legacy_block():
    """6. Student + Legacy -> BLOCK."""
    context = RequestContext(
        user_id="s3",
        role=UserRole.STUDENT,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.LEGACY, mfa_completed=False),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.BLOCK
    assert "block-legacy-auth" in result.matched_policies


def test_unit_admin_legacy_block():
    """7. Admin + Legacy -> BLOCK."""
    context = RequestContext(
        user_id="a3",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.LEGACY, mfa_completed=False),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.BLOCK


def test_unit_device_unmanaged_policy_matches():
    """8. Admin + unmanaged device + applicable device policy -> restrictive result."""
    device_policy = Policy(
        id="unmanaged-admin-mfa",
        name="Unmanaged Admin MFA",
        description="Unmanaged admin devices require MFA",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        target_device_managed=False,
        action=PolicyDecision.MFA_REQUIRED,
    )
    context = RequestContext(
        user_id="a4",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [device_policy])
    assert result.decision == PolicyDecision.MFA_REQUIRED
    assert result.matched_policies == ["unmanaged-admin-mfa"]


def test_unit_device_managed_policy_no_match():
    """9. Admin + managed device -> policy requiring unmanaged device must not match."""
    device_policy = Policy(
        id="unmanaged-admin-mfa",
        name="Unmanaged Admin MFA",
        description="Unmanaged admin devices require MFA",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        target_device_managed=False,
        action=PolicyDecision.MFA_REQUIRED,
    )
    context = RequestContext(
        user_id="a5",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [device_policy])
    assert result.decision == PolicyDecision.ALLOW
    assert result.matched_policies == []


def test_unit_location_matching():
    """10. Request matching location-specific policy -> matches."""
    location_policy = Policy(
        id="block-outside-eu",
        name="Location Check",
        description="Block non-EU access",
        enabled=True,
        target_locations=["US"],
        action=PolicyDecision.BLOCK,
    )
    context = RequestContext(
        user_id="u1",
        role=UserRole.STAFF,
        location="US",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=True),
    )
    result = evaluator.evaluate(context, [location_policy])
    assert result.decision == PolicyDecision.BLOCK


def test_unit_location_non_matching():
    """11. Request from different location -> policy does not match."""
    location_policy = Policy(
        id="block-us-only",
        name="Location Check",
        description="Block US access",
        enabled=True,
        target_locations=["US"],
        action=PolicyDecision.BLOCK,
    )
    context = RequestContext(
        user_id="u2",
        role=UserRole.STAFF,
        location="EU",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=True),
    )
    result = evaluator.evaluate(context, [location_policy])
    assert result.decision == PolicyDecision.ALLOW


def test_unit_excluded_role():
    """12. Excluded role -> policy ignored."""
    context = RequestContext(
        user_id="bg1",
        role=UserRole.BREAK_GLASS,
        location="US",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    repo = InMemoryPolicyRepository()
    result = evaluator.evaluate(context, repo)
    assert result.decision == PolicyDecision.ALLOW
    assert "admin-mfa" not in result.matched_policies


def test_unit_excluded_user():
    """13. Excluded user -> policy ignored."""
    user_exclusion_policy = Policy(
        id="admin-mfa-excluded-user",
        name="Admin MFA with Excluded User",
        description="All admins require MFA except vip_admin",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        action=PolicyDecision.MFA_REQUIRED,
        excluded_users=["vip_admin"],
    )
    context = RequestContext(
        user_id="vip_admin",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [user_exclusion_policy])
    assert result.decision == PolicyDecision.ALLOW
    assert result.matched_policies == []


def test_unit_disabled_policy():
    """14. Disabled policy -> ignored."""
    disabled_policy = Policy(
        id="disabled-policy",
        name="Disabled Policy",
        description="This policy is disabled",
        enabled=False,
        target_roles=[UserRole.STUDENT],
        action=PolicyDecision.BLOCK,
    )
    context = RequestContext(
        user_id="s4",
        role=UserRole.STUDENT,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [disabled_policy])
    assert result.decision == PolicyDecision.ALLOW


def test_unit_empty_policy_repository():
    """15. Empty policy repository -> ALLOW."""
    context = RequestContext(
        user_id="any",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.LEGACY, mfa_completed=False),
    )
    empty_repo = InMemoryPolicyRepository(policies=[])
    result = evaluator.evaluate(context, empty_repo)
    assert result.decision == PolicyDecision.ALLOW
    assert result.matched_policies == []


def test_unit_mfa_and_block_combination():
    """16. MFA_REQUIRED + BLOCK -> BLOCK."""
    p1 = Policy(
        id="p-mfa",
        name="Require MFA",
        description="MFA required for admin",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        action=PolicyDecision.MFA_REQUIRED,
    )
    p2 = Policy(
        id="p-block",
        name="Block Legacy",
        description="Block legacy auth",
        enabled=True,
        target_protocols=[AuthProtocol.LEGACY],
        action=PolicyDecision.BLOCK,
    )
    context = RequestContext(
        user_id="a6",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.LEGACY, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [p1, p2])
    assert result.decision == PolicyDecision.BLOCK
    assert set(result.matched_policies) == {"p-mfa", "p-block"}


def test_unit_multiple_mfa_policies():
    """17. Multiple MFA_REQUIRED policies -> MFA_REQUIRED."""
    p1 = Policy(
        id="mfa-1",
        name="MFA 1",
        description="MFA 1",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        action=PolicyDecision.MFA_REQUIRED,
    )
    p2 = Policy(
        id="mfa-2",
        name="MFA 2",
        description="MFA 2",
        enabled=True,
        target_roles=[UserRole.ADMIN],
        action=PolicyDecision.MFA_REQUIRED,
    )
    context = RequestContext(
        user_id="a7",
        role=UserRole.ADMIN,
        location="IN",
        device=DeviceInfo(managed=True, compliant=True),
        authentication=AuthInfo(protocol=AuthProtocol.MODERN, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [p1, p2])
    assert result.decision == PolicyDecision.MFA_REQUIRED
    assert set(result.matched_policies) == {"mfa-1", "mfa-2"}


def test_unit_multiple_block_policies():
    """18. Multiple BLOCK policies -> BLOCK."""
    p1 = Policy(
        id="block-1",
        name="Block 1",
        description="Block 1",
        enabled=True,
        target_protocols=[AuthProtocol.LEGACY],
        action=PolicyDecision.BLOCK,
    )
    p2 = Policy(
        id="block-2",
        name="Block 2",
        description="Block 2",
        enabled=True,
        target_roles=[UserRole.STUDENT],
        target_protocols=[AuthProtocol.LEGACY],
        action=PolicyDecision.BLOCK,
    )
    context = RequestContext(
        user_id="s5",
        role=UserRole.STUDENT,
        location="IN",
        device=DeviceInfo(managed=False, compliant=False),
        authentication=AuthInfo(protocol=AuthProtocol.LEGACY, mfa_completed=False),
    )
    result = evaluator.evaluate(context, [p1, p2])
    assert result.decision == PolicyDecision.BLOCK
    assert set(result.matched_policies) == {"block-1", "block-2"}


def test_unit_duplicate_policy_id_raises_value_error():
    """Verify InMemoryPolicyRepository raises ValueError on duplicate policy IDs."""
    p1 = Policy(
        id="dup-id",
        name="P1",
        description="P1",
        action=PolicyDecision.BLOCK,
    )
    p2 = Policy(
        id="dup-id",
        name="P2",
        description="P2",
        action=PolicyDecision.ALLOW,
    )
    with pytest.raises(ValueError, match="Duplicate policy ID detected"):
        InMemoryPolicyRepository(policies=[p1, p2])
