import pytest
from app.engine.enums import AuthProtocol, UserRole
from app.risk.enums import RiskLevel
from app.risk.evaluator import RiskEvaluator
from app.risk.models import RiskFactor
from app.risk.registry import RiskRuleRegistry
from app.risk.rules import (
    AbstractRiskRule,
    LegacyAuthenticationRule,
    MockDeviceUnknownRule,
    PrivilegedMfaMissingRule,
    UnknownAuthStateRule,
)
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal


def test_admin_mfa_incomplete_high_risk() -> None:
    evaluator = RiskEvaluator()
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

    assessment = evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.HIGH
    assert any(f.name == "privileged_mfa_missing" for f in assessment.factors)


def test_security_admin_mfa_incomplete_high_risk() -> None:
    evaluator = RiskEvaluator()
    ctx = SecurityContext()
    ctx.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.SECURITY_ADMIN], source=SignalSource.KEYCLOAK
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.mfa_completed", value=False, source=SignalSource.KEYCLOAK
        )
    )

    assessment = evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.HIGH


def test_legacy_authentication_high_risk() -> None:
    evaluator = RiskEvaluator()
    ctx = SecurityContext()
    ctx.add_signal(
        SecuritySignal(
            name="auth.protocol", value=AuthProtocol.LEGACY, source=SignalSource.KEYCLOAK
        )
    )

    assessment = evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.HIGH
    assert any(f.name == "legacy_authentication" for f in assessment.factors)


def test_unknown_auth_state_unknown_risk() -> None:
    evaluator = RiskEvaluator()
    ctx = SecurityContext()
    ctx.add_signal(
        SecuritySignal(
            name="auth.protocol",
            value=None,
            source=SignalSource.KEYCLOAK,
            status=SignalStatus.UNKNOWN,
        )
    )

    assessment = evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.UNKNOWN
    assert any(f.name == "unknown_auth_state" for f in assessment.factors)


def test_normal_trusted_context_low_risk() -> None:
    evaluator = RiskEvaluator()
    ctx = SecurityContext()
    ctx.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.STUDENT], source=SignalSource.KEYCLOAK
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.protocol", value=AuthProtocol.MODERN, source=SignalSource.KEYCLOAK
        )
    )
    ctx.add_signal(
        SecuritySignal(
            name="auth.mfa_completed", value=False, source=SignalSource.KEYCLOAK
        )
    )

    assessment = evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.LOW
    assert len(assessment.factors) == 0


def test_risk_precedence_high_over_medium_and_low() -> None:
    registry = RiskRuleRegistry()
    registry.register(PrivilegedMfaMissingRule())
    registry.register(MockDeviceUnknownRule())

    evaluator = RiskEvaluator(registry=registry)
    ctx = SecurityContext()
    # Privileged user (HIGH factor) + Device unknown (MEDIUM factor)
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
    ctx.add_signal(
        SecuritySignal(
            name="device.compliant",
            value=None,
            source=SignalSource.LOCAL,
            status=SignalStatus.UNKNOWN,
        )
    )

    assessment = evaluator.evaluate(ctx)
    assert assessment.level == RiskLevel.HIGH
    factor_names = [f.name for f in assessment.factors]
    assert "privileged_mfa_missing" in factor_names
    assert "device_unknown" in factor_names
