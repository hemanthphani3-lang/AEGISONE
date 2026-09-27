import pytest
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import Policy
from app.signals.aggregator import context_aggregator
from app.signals.conditions import (
    AuthProtocolConditionEvaluator,
    DeviceConditionEvaluator,
    ExclusionConditionEvaluator,
    LocationConditionEvaluator,
    MfaConditionEvaluator,
    RoleConditionEvaluator,
)
from app.signals.enums import ConditionResult, SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal
from app.signals.registry import ConditionRegistry, condition_registry


def test_exclusion_condition_evaluator() -> None:
    evaluator = ExclusionConditionEvaluator()
    policy = Policy(
        id="p1",
        name="N",
        description="D",
        action=PolicyDecision.BLOCK,
        exclusions=[UserRole.BREAK_GLASS],
        excluded_users=["user-excluded"],
    )

    ctx_normal = SecurityContext()
    ctx_normal.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.STUDENT], source=SignalSource.KEYCLOAK
        )
    )
    ctx_normal.add_signal(
        SecuritySignal(name="identity.user_id", value="user-1", source=SignalSource.KEYCLOAK)
    )

    ctx_bg = SecurityContext()
    ctx_bg.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.BREAK_GLASS], source=SignalSource.KEYCLOAK
        )
    )

    ctx_user_ex = SecurityContext()
    ctx_user_ex.add_signal(
        SecuritySignal(name="identity.user_id", value="user-excluded", source=SignalSource.KEYCLOAK)
    )

    assert evaluator.evaluate(ctx_normal, policy) == ConditionResult.MATCH
    assert evaluator.evaluate(ctx_bg, policy) == ConditionResult.NO_MATCH
    assert evaluator.evaluate(ctx_user_ex, policy) == ConditionResult.NO_MATCH


def test_device_condition_unknown_status() -> None:
    evaluator = DeviceConditionEvaluator()
    policy = Policy(
        id="p-device",
        name="Device Policy",
        description="D",
        action=PolicyDecision.BLOCK,
        target_device_compliant=True,
    )

    # Context with UNKNOWN device.compliant status
    ctx_unknown = SecurityContext()
    ctx_unknown.add_signal(
        SecuritySignal(
            name="device.compliant",
            value=None,
            source=SignalSource.LOCAL,
            status=SignalStatus.UNKNOWN,
        )
    )

    result = evaluator.evaluate(ctx_unknown, policy)
    assert result == ConditionResult.UNKNOWN
    # Ensure UNKNOWN is distinct from NO_MATCH
    assert result != ConditionResult.NO_MATCH


def test_condition_registry_operations() -> None:
    registry = ConditionRegistry()

    assert registry.get_evaluator("role") is not None
    assert registry.get_evaluator("device") is not None

    policy = Policy(
        id="p-role",
        name="Role Policy",
        description="D",
        target_roles=[UserRole.ADMIN],
        action=PolicyDecision.MFA_REQUIRED,
    )

    ctx_admin = SecurityContext()
    ctx_admin.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.ADMIN], source=SignalSource.KEYCLOAK
        )
    )

    ctx_student = SecurityContext()
    ctx_student.add_signal(
        SecuritySignal(
            name="identity.roles", value=[UserRole.STUDENT], source=SignalSource.KEYCLOAK
        )
    )

    assert registry.evaluate_all(ctx_admin, policy) is True
    assert registry.evaluate_all(ctx_student, policy) is False
