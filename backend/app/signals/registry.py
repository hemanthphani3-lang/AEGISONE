from app.engine.models import Policy

from app.signals.conditions import (
    AbstractConditionEvaluator,
    AuthProtocolConditionEvaluator,
    DeviceConditionEvaluator,
    ExclusionConditionEvaluator,
    LocationConditionEvaluator,
    MfaConditionEvaluator,
    RiskConditionEvaluator,
    RoleConditionEvaluator,
)
from app.signals.enums import ConditionResult
from app.signals.models import SecurityContext


class ConditionRegistry:
    """Registry that manages modular ConditionEvaluator instances for policy evaluation."""

    def __init__(self) -> None:
        self._evaluators: dict[str, AbstractConditionEvaluator] = {}
        self.register_default_evaluators()

    def register_default_evaluators(self) -> None:
        """Register default condition evaluators."""
        self.register("exclusion", ExclusionConditionEvaluator())
        self.register("role", RoleConditionEvaluator())
        self.register("protocol", AuthProtocolConditionEvaluator())
        self.register("location", LocationConditionEvaluator())
        self.register("device", DeviceConditionEvaluator())
        self.register("mfa", MfaConditionEvaluator())
        self.register("risk", RiskConditionEvaluator())

    def register(self, key: str, evaluator: AbstractConditionEvaluator) -> None:
        """Register a new condition evaluator under a key."""
        self._evaluators[key] = evaluator

    def unregister(self, key: str) -> None:
        """Unregister an evaluator by key."""
        self._evaluators.pop(key, None)

    def get_evaluator(self, key: str) -> AbstractConditionEvaluator | None:
        """Retrieve a registered evaluator by key."""
        return self._evaluators.get(key)

    def evaluate_all(self, context: SecurityContext, policy: Policy) -> bool:
        """Evaluate all registered condition evaluators using logical AND semantics.

        Returns True if all evaluators match, False otherwise.
        """
        for key, evaluator in self._evaluators.items():
            result = evaluator.evaluate(context, policy)
            if result == ConditionResult.NO_MATCH or result == ConditionResult.UNKNOWN:
                return False
        return True

    def evaluate_detailed(self, context: SecurityContext, policy: Policy) -> list:
        """Evaluate all registered condition evaluators and return detailed breakdown."""
        from app.engine.models import ConditionDetail
        details = []
        for key, evaluator in self._evaluators.items():
            result, reason = evaluator.evaluate_with_reason(context, policy)
            details.append(
                ConditionDetail(
                    condition_type=key.upper(),
                    result=result.value if hasattr(result, "value") else str(result),
                    reason=reason,
                )
            )
        return details


condition_registry = ConditionRegistry()
