from datetime import datetime, timezone
from app.risk.enums import RiskLevel
from app.risk.models import RiskAssessment, RiskFactor
from app.risk.registry import RiskRuleRegistry, risk_rule_registry
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal


class RiskEvaluator:
    """Evaluates security risk deterministically based on context signals and risk rules."""

    def __init__(self, registry: RiskRuleRegistry | None = None) -> None:
        self.registry = registry or risk_rule_registry

    def evaluate(self, context: SecurityContext) -> RiskAssessment:
        """Evaluate a SecurityContext and produce a deterministic RiskAssessment.

        Also attaches derived risk signals ('risk.level' and 'risk.assessment') to the context.
        """
        # 1. Collect all risk factors from registered rules
        factors = self.registry.evaluate_all(context)

        # Check if context already has an explicit risk.level signal from an external provider
        existing_risk_sig = context.get_signal("risk.level")
        if (
            existing_risk_sig
            and existing_risk_sig.is_available
            and existing_risk_sig.source != SignalSource.LOCAL
        ):
            val_str = str(
                existing_risk_sig.value.value
                if hasattr(existing_risk_sig.value, "value")
                else existing_risk_sig.value
            ).upper()
            try:
                overall_level = RiskLevel(val_str)
            except ValueError:
                overall_level = RiskLevel.UNKNOWN
        else:
            # 2. Determine overall RiskLevel using strict precedence: HIGH > MEDIUM > UNKNOWN > LOW
            high_factors = [f for f in factors if f.severity == RiskLevel.HIGH]
            medium_factors = [f for f in factors if f.severity == RiskLevel.MEDIUM]
            unknown_factors = [f for f in factors if f.severity == RiskLevel.UNKNOWN]

            if high_factors:
                overall_level = RiskLevel.HIGH
            elif medium_factors:
                overall_level = RiskLevel.MEDIUM
            elif unknown_factors:
                overall_level = RiskLevel.UNKNOWN
            else:
                overall_level = RiskLevel.LOW

        # 3. Generate explainable trace summary
        if factors:
            reasons_str = "; ".join(f"{f.name}: {f.reason}" for f in factors)
            trace = f"{overall_level.value} risk determined due to factors: {reasons_str}"
        else:
            trace = "LOW risk determined: No elevated risk factors detected in trusted context."

        assessment = RiskAssessment(
            level=overall_level,
            factors=factors,
            evaluated_at=datetime.now(timezone.utc),
            confidence=SignalConfidence.HIGH,
            trace=trace,
        )

        # 4. Attach derived signals to SecurityContext
        context.add_signal(
            SecuritySignal(
                name="risk.level",
                value=overall_level,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        )
        context.add_signal(
            SecuritySignal(
                name="risk.assessment",
                value=assessment,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        )

        return assessment


risk_evaluator = RiskEvaluator()
