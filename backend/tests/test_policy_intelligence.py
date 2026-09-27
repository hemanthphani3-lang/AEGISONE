import pytest
from app.engine.enums import PolicyDecision, UserRole
from app.engine.intelligence import policy_intelligence_engine
from app.engine.intelligence_models import FindingSeverity, PolicyHealthStatus
from app.engine.models import Policy


def test_detect_broad_policies():
    broad_policy = Policy(
        id="broad-1",
        name="Broad Unconditional Policy",
        description="Matches everything",
        enabled=True,
        action=PolicyDecision.MFA_REQUIRED,
        target_roles=[],
        target_protocols=[],
        target_locations=[],
    )
    specific_policy = Policy(
        id="spec-1",
        name="Specific Role Policy",
        description="Matches admin role",
        enabled=True,
        action=PolicyDecision.BLOCK,
        target_roles=[UserRole.ADMIN],
        target_protocols=[],
        target_locations=[],
    )

    report = policy_intelligence_engine.analyze_all([broad_policy, specific_policy])
    findings = report.global_findings
    broad_findings = [f for f in findings if f.finding_type == "OVERLY_BROAD"]
    
    assert len(broad_findings) == 1
    assert broad_findings[0].affected_policy_ids == ["broad-1"]


def test_detect_duplicate_policies():
    p1 = Policy(
        id="dup-1",
        name="Dup Policy 1",
        description="First duplicate",
        enabled=True,
        action=PolicyDecision.BLOCK,
        target_roles=[UserRole.STUDENT],
    )
    p2 = Policy(
        id="dup-2",
        name="Dup Policy 2",
        description="Second duplicate",
        enabled=True,
        action=PolicyDecision.BLOCK,
        target_roles=[UserRole.STUDENT],
    )

    report = policy_intelligence_engine.analyze_all([p1, p2])
    dup_findings = [f for f in report.global_findings if f.finding_type == "DUPLICATE"]
    
    assert len(dup_findings) >= 1
    assert "dup-1" in dup_findings[0].affected_policy_ids
    assert "dup-2" in dup_findings[0].affected_policy_ids


def test_detect_conflict_policies():
    p_allow = Policy(
        id="conf-allow",
        name="Allow Staff",
        description="Allow staff access",
        enabled=True,
        action=PolicyDecision.ALLOW,
        target_roles=[UserRole.STAFF],
    )
    p_block = Policy(
        id="conf-block",
        name="Block Staff",
        description="Block staff access",
        enabled=True,
        action=PolicyDecision.BLOCK,
        target_roles=[UserRole.STAFF],
    )

    report = policy_intelligence_engine.analyze_all([p_allow, p_block])
    conf_findings = [f for f in report.global_findings if f.finding_type == "CONFLICT"]

    assert len(conf_findings) >= 1
    assert "conf-allow" in conf_findings[0].affected_policy_ids
    assert "conf-block" in conf_findings[0].affected_policy_ids
    assert conf_findings[0].severity == FindingSeverity.HIGH


def test_detect_dangerous_admin_lockout():
    p_dangerous = Policy(
        id="danger-admin",
        name="Block Admins Unconditionally",
        description="Lockout risk policy",
        enabled=True,
        action=PolicyDecision.BLOCK,
        target_roles=[UserRole.ADMIN, UserRole.SECURITY_ADMIN],
        exclusions=[],
        excluded_users=[],
    )

    report = policy_intelligence_engine.analyze_all([p_dangerous])
    danger_findings = [f for f in report.global_findings if f.finding_type == "DANGEROUS"]

    assert len(danger_findings) >= 1
    assert "danger-admin" in danger_findings[0].affected_policy_ids
    assert danger_findings[0].severity == FindingSeverity.CRITICAL

    # Health score check
    health_summary = next(s for s in report.policy_health_summaries if s.policy_id == "danger-admin")
    assert health_summary.status == PolicyHealthStatus.CRITICAL
    assert health_summary.score < 75
