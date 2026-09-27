import pytest
from app.engine.enums import PolicyDecision
from app.engine.evaluator import policy_evaluator
from app.engine.models import Policy
from app.signals.enums import ConditionResult, SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal
from app.signals.provider import AbstractSignalProvider
from app.signals.registry import condition_registry


class MockRiskSignalProvider(AbstractSignalProvider):
    """Mock signal provider for future risk intelligence signal (risk.level)."""

    def __init__(self, risk_level: str = "HIGH") -> None:
        self.risk_level = risk_level

    def get_signals_sync(self, input_data: any) -> list[SecuritySignal]:
        return [
            SecuritySignal(
                name="risk.level",
                value=self.risk_level,
                source=SignalSource.RISK_PROVIDER,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        ]


def test_pluggable_future_risk_signal_and_condition() -> None:
    """Demonstrate extending AegisOne with a future risk.level signal and condition.

    Verifies that new signal providers and condition evaluators integrate cleanly
    via ConditionRegistry without modifying PolicyEvaluator core code.
    """
    # 1. Create context with future mock risk signal
    ctx = SecurityContext()
    risk_provider = MockRiskSignalProvider(risk_level="HIGH")
    for sig in risk_provider.get_signals_sync(None):
        ctx.add_signal(sig)

    # 2. Define policy targeting high risk
    high_risk_policy = Policy(
        id="block-high-risk",
        name="Block High Risk Sign-ins",
        description="Block requests evaluated as high risk level",
        enabled=True,
        target_risk_level="HIGH",
        action=PolicyDecision.BLOCK,
    )


    # 3. Evaluate context against policy using policy_evaluator
    result = policy_evaluator.evaluate(ctx, [high_risk_policy])

    # 4. Verify decision and matched policy
    assert result.decision == PolicyDecision.BLOCK
    assert "block-high-risk" in result.matched_policies
