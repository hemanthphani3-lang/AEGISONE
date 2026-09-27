import pytest
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.evaluator import policy_evaluator
from app.engine.models import Policy
from app.risk.enums import RiskLevel
from app.risk.evaluator import risk_evaluator
from app.signals.conditions import RiskConditionEvaluator
from app.signals.enums import ConditionResult, SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal


def test_risk_condition_evaluator_matching() -> None:
    evaluator = RiskConditionEvaluator()
    policy = Policy(
        id="p-high-risk",
        name="High Risk Policy",
        description="D",
        target_risk_level="HIGH",
        action=PolicyDecision.BLOCK,
    )

    # 1. HIGH risk -> MATCH
    ctx_high = SecurityContext()
    ctx_high.add_signal(
        SecuritySignal(
            name="risk.level", value=RiskLevel.HIGH, source=SignalSource.LOCAL
        )
    )
    assert evaluator.evaluate(ctx_high, policy) == ConditionResult.MATCH

    # 2. LOW risk -> NO_MATCH
    ctx_low = SecurityContext()
    ctx_low.add_signal(
        SecuritySignal(
            name="risk.level", value=RiskLevel.LOW, source=SignalSource.LOCAL
        )
    )
    assert evaluator.evaluate(ctx_low, policy) == ConditionResult.NO_MATCH

    # 3. UNKNOWN risk -> NO_MATCH (Requirement 13)
    ctx_unknown = SecurityContext()
    ctx_unknown.add_signal(
        SecuritySignal(
            name="risk.level", value=RiskLevel.UNKNOWN, source=SignalSource.LOCAL
        )
    )
    assert evaluator.evaluate(ctx_unknown, policy) == ConditionResult.NO_MATCH


def test_risk_policy_actions_block_and_mfa() -> None:
    policy_block = Policy(
        id="high-risk-block",
        name="Block High Risk",
        description="D",
        target_risk_level="HIGH",
        action=PolicyDecision.BLOCK,
    )
    policy_mfa = Policy(
        id="high-risk-mfa",
        name="Require MFA for High Risk",
        description="D",
        target_risk_level="HIGH",
        action=PolicyDecision.MFA_REQUIRED,
    )

    ctx = SecurityContext()
    ctx.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.ADMIN], source=SignalSource.KEYCLOAK
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.mfa_completed", value=False, source=SignalSource.KEYCLOAK
        )
    )
    # Evaluate risk
    risk_evaluator.evaluate(ctx)
    assert ctx.get_value("risk.level") == RiskLevel.HIGH

    # Evaluate against BLOCK policy
    res_block = policy_evaluator.evaluate(ctx, [policy_block])
    assert res_block.decision == PolicyDecision.BLOCK

    # Evaluate against MFA_REQUIRED policy
    res_mfa = policy_evaluator.evaluate(ctx, [policy_mfa])
    assert res_mfa.decision == PolicyDecision.MFA_REQUIRED


def test_client_cannot_spoof_risk_level() -> None:
    """Verify that client body parameters cannot force a LOW risk level when privileged MFA is missing."""
    ctx = SecurityContext()
    # Keycloak principal signal (trusted)
    ctx.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.ADMIN], source=SignalSource.KEYCLOAK
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.mfa_completed", value=False, source=SignalSource.KEYCLOAK
        )
    )
    # Simulated client attempt to inject low risk
    ctx.add_signal(
        SecuritySignal(
            name="risk.level", value=RiskLevel.LOW, source=SignalSource.LOCAL, confidence=SignalConfidence.LOW
        )
    )

    # RiskEvaluator derives risk from trusted context, overriding low-confidence client injection
    assessment = risk_evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.HIGH
    assert ctx.get_value("risk.level") == RiskLevel.HIGH
