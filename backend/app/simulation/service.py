import uuid
from datetime import datetime, timezone
from typing import Any

from app.engine.evaluator import policy_evaluator
from app.engine.models import Policy
from app.risk.enums import RiskLevel
from app.risk.evaluator import risk_evaluator
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal
from app.simulation.models import (
    PolicyChangeTrace,
    SimulationOverrides,
    SimulationResult,
    SimulationTrace,
)


class SimulationService:
    """Isolated simulation layer for executing what-if policy evaluations without side effects."""

    def apply_overrides(
        self, base_context: SecurityContext, overrides: SimulationOverrides
    ) -> SecurityContext:
        """Create a deep clone of base_context and apply validated simulation overrides."""
        # 1. Deep clone base context signals to ensure total immutability of the original
        cloned_signals = {
            name: sig.model_copy(deep=True)
            for name, sig in base_context.signals.items()
        }
        simulated_context = SecurityContext(signals=cloned_signals)

        # 2. Apply override signals if present
        if overrides.roles is not None:
            simulated_context.add_signal(
                SecuritySignal(
                    name="identity.roles",
                    value=overrides.roles,
                    source=SignalSource.LOCAL,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        if overrides.auth_protocol is not None:
            simulated_context.add_signal(
                SecuritySignal(
                    name="auth.protocol",
                    value=overrides.auth_protocol,
                    source=SignalSource.LOCAL,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        if overrides.mfa_completed is not None:
            simulated_context.add_signal(
                SecuritySignal(
                    name="auth.mfa_completed",
                    value=overrides.mfa_completed,
                    source=SignalSource.LOCAL,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        if overrides.device_managed is not None:
            status = (
                SignalStatus.AVAILABLE
                if overrides.device_managed is not None
                else SignalStatus.UNKNOWN
            )
            simulated_context.add_signal(
                SecuritySignal(
                    name="device.managed",
                    value=overrides.device_managed,
                    source=SignalSource.LOCAL,
                    status=status,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        if overrides.device_compliant is not None:
            status = (
                SignalStatus.AVAILABLE
                if overrides.device_compliant is not None
                else SignalStatus.UNKNOWN
            )
            simulated_context.add_signal(
                SecuritySignal(
                    name="device.compliant",
                    value=overrides.device_compliant,
                    source=SignalSource.LOCAL,
                    status=status,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        if overrides.location is not None:
            simulated_context.add_signal(
                SecuritySignal(
                    name="location",
                    value=overrides.location,
                    source=SignalSource.LOCAL,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        if overrides.network_type is not None:
            simulated_context.add_signal(
                SecuritySignal(
                    name="network_type",
                    value=overrides.network_type,
                    source=SignalSource.LOCAL,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )

        # 3. Handle risk signal evaluation
        if overrides.risk_level is not None:
            simulated_context.add_signal(
                SecuritySignal(
                    name="risk.level",
                    value=overrides.risk_level,
                    source=SignalSource.LOCAL,
                    status=SignalStatus.AVAILABLE,
                    confidence=SignalConfidence.HIGH,
                    metadata={"simulated": True},
                )
            )
        else:
            # Recompute risk dynamically on simulated context
            risk_evaluator.evaluate(simulated_context)

        return simulated_context

    def run_simulation(
        self,
        base_context: SecurityContext,
        overrides: SimulationOverrides,
        policies: list[Policy],
        correlation_id: str | None = None,
    ) -> SimulationResult:
        """Run an isolated policy evaluation simulation comparing base and simulated states."""
        # 1. Prepare base evaluation context (cloned to protect base_context)
        base_context_eval = SecurityContext(
            signals={k: v.model_copy(deep=True) for k, v in base_context.signals.items()}
        )
        if not base_context_eval.has_signal("risk.level"):
            risk_evaluator.evaluate(base_context_eval)

        base_eval_result = policy_evaluator.evaluate(base_context_eval, policies)
        base_risk = base_context_eval.get_value("risk.level", RiskLevel.LOW)

        # 2. Build simulated context with overrides applied and risk recomputed
        simulated_context = self.apply_overrides(base_context, overrides)
        simulated_eval_result = policy_evaluator.evaluate(simulated_context, policies)
        simulated_risk = simulated_context.get_value("risk.level", RiskLevel.LOW)

        # 3. Compare matched policies
        policy_changes: list[PolicyChangeTrace] = []
        for policy in policies:
            base_matched = policy_evaluator.is_policy_matched(base_context_eval, policy)
            simulated_matched = policy_evaluator.is_policy_matched(simulated_context, policy)
            if base_matched != simulated_matched:
                summary = (
                    "matched -> not_matched"
                    if base_matched
                    else "not_matched -> matched"
                )
                policy_changes.append(
                    PolicyChangeTrace(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        base_matched=base_matched,
                        simulated_matched=simulated_matched,
                        change_summary=summary,
                    )
                )

        decision_changed = base_eval_result.decision != simulated_eval_result.decision
        risk_changed = base_risk != simulated_risk

        # 4. Generate structured explanation trace
        overrides_dict = overrides.model_dump(exclude_none=True)
        explanation_parts = []
        if overrides_dict:
            overrides_str = ", ".join(f"{k}={v}" for k, v in overrides_dict.items())
            explanation_parts.append(f"Simulation overrides applied: {overrides_str}.")
        else:
            explanation_parts.append("No context overrides were specified.")

        if decision_changed:
            explanation_parts.append(
                f"Policy decision changed from {base_eval_result.decision.value} to {simulated_eval_result.decision.value}."
            )
        else:
            explanation_parts.append(
                f"Policy decision remained unchanged as {base_eval_result.decision.value}."
            )

        base_risk_val = base_risk.value if isinstance(base_risk, RiskLevel) else str(base_risk)
        simulated_risk_val = (
            simulated_risk.value if isinstance(simulated_risk, RiskLevel) else str(simulated_risk)
        )
        if risk_changed:
            explanation_parts.append(
                f"Risk level recomputed from {base_risk_val} to {simulated_risk_val}."
            )
        else:
            explanation_parts.append(f"Risk level remained {base_risk_val}.")

        if policy_changes:
            changes_str = "; ".join(
                f"Policy '{pc.policy_name}' ({pc.policy_id}): {pc.change_summary}"
                for pc in policy_changes
            )
            explanation_parts.append(f"Policy match changes: {changes_str}.")
        else:
            explanation_parts.append("No individual policy match states were altered.")

        explanation = " ".join(explanation_parts)

        trace = SimulationTrace(
            base_decision=base_eval_result.decision,
            simulated_decision=simulated_eval_result.decision,
            decision_changed=decision_changed,
            base_risk=base_risk,
            simulated_risk=simulated_risk,
            risk_changed=risk_changed,
            overrides_applied=overrides_dict,
            policy_changes=policy_changes,
            explanation=explanation,
        )

        simulation_id = str(uuid.uuid4())

        return SimulationResult(
            simulation_id=simulation_id,
            correlation_id=correlation_id,
            created_at=datetime.now(timezone.utc),
            base_decision=base_eval_result.decision,
            simulated_decision=simulated_eval_result.decision,
            decision_changed=decision_changed,
            base_risk=base_risk,
            simulated_risk=simulated_risk,
            risk_changed=risk_changed,
            overrides_applied=overrides,
            trace=trace,
            evaluation_result=simulated_eval_result,
        )


simulation_service = SimulationService()
