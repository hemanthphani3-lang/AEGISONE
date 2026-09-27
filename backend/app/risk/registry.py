from app.risk.models import RiskFactor
from app.risk.rules import (
    AbstractRiskRule,
    LegacyAuthenticationRule,
    PrivilegedMfaMissingRule,
    UnknownAuthStateRule,
)
from app.signals.models import SecurityContext


class RiskRuleRegistry:
    """Registry that manages deterministic RiskRule execution."""

    def __init__(self) -> None:
        self._rules: dict[str, AbstractRiskRule] = {}
        self.register_default_rules()

    def register_default_rules(self) -> None:
        """Register default core risk rules."""
        self.register(PrivilegedMfaMissingRule())
        self.register(LegacyAuthenticationRule())
        self.register(UnknownAuthStateRule())

    def register(self, rule: AbstractRiskRule) -> None:
        """Register a new risk rule."""
        self._rules[rule.name] = rule

    def unregister(self, rule_name: str) -> None:
        """Unregister a risk rule by name."""
        self._rules.pop(rule_name, None)

    def get_rule(self, rule_name: str) -> AbstractRiskRule | None:
        """Retrieve a registered rule by name."""
        return self._rules.get(rule_name)

    def evaluate_all(self, context: SecurityContext) -> list[RiskFactor]:
        """Evaluate all registered risk rules against a SecurityContext in deterministic order."""
        factors: list[RiskFactor] = []
        for rule in self._rules.values():
            factor = rule.evaluate(context)
            if factor is not None:
                factors.append(factor)
        return factors


risk_rule_registry = RiskRuleRegistry()
