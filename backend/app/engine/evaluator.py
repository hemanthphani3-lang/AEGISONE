from app.engine.enums import PolicyDecision
from app.engine.models import EvaluationResult, Policy, RequestContext
from app.engine.repository import AbstractPolicyRepository
from app.signals.aggregator import context_aggregator
from app.signals.models import SecurityContext
from app.signals.registry import condition_registry


class PolicyEvaluator:
    """Evaluator that executes policies against a normalized SecurityContext.

    Delegates condition evaluation to pluggable ConditionRegistry while keeping
    PolicyEvaluator completely decoupled from signal sources and vendor logic.
    Enforces decision hierarchy: BLOCK > MFA_REQUIRED > ALLOW.
    """

    def is_policy_matched(
        self, context: RequestContext | SecurityContext, policy: Policy
    ) -> bool:
        """Determine if a single policy applies to the given context using condition evaluators."""
        if not policy.enabled:
            return False

        if isinstance(context, RequestContext):
            sec_context = context_aggregator.from_request_context(context)
        else:
            sec_context = context

        return condition_registry.evaluate_all(sec_context, policy)

    def resolve_decision(self, matched_policies: list[Policy]) -> EvaluationResult:
        """Resolve the overall decision from all matched policies using the decision hierarchy."""
        if not matched_policies:
            return EvaluationResult(
                decision=PolicyDecision.ALLOW,
                matched_policies=[],
                reasons=["No matching restrictive policy. Default action: ALLOW."],
                decision_precedence_trace="Final Decision: ALLOW. No restrictive policy matched context. Default action: ALLOW.",
            )

        reasons = [
            f"Policy '{p.name}' ({p.id}) triggered decision: {p.action.value}."
            for p in matched_policies
        ]

        actions = {p.action for p in matched_policies}

        if PolicyDecision.BLOCK in actions:
            final_decision = PolicyDecision.BLOCK
            blocking_policies = [p for p in matched_policies if p.action == PolicyDecision.BLOCK]
            pol_names = ", ".join(f"'{p.name}' ({p.id})" for p in blocking_policies)
            precedence_trace = (
                f"Final Decision: BLOCK. Decision Precedence: BLOCK overrides MFA_REQUIRED and ALLOW. "
                f"Triggered by policy/policies: {pol_names}."
            )
        elif PolicyDecision.MFA_REQUIRED in actions:
            final_decision = PolicyDecision.MFA_REQUIRED
            mfa_policies = [p for p in matched_policies if p.action == PolicyDecision.MFA_REQUIRED]
            pol_names = ", ".join(f"'{p.name}' ({p.id})" for p in mfa_policies)
            precedence_trace = (
                f"Final Decision: MFA_REQUIRED. Decision Precedence: MFA_REQUIRED overrides ALLOW. "
                f"Triggered by policy/policies: {pol_names}."
            )
        else:
            final_decision = PolicyDecision.ALLOW
            pol_names = ", ".join(f"'{p.name}' ({p.id})" for p in matched_policies)
            precedence_trace = f"Final Decision: ALLOW. Matched policies: {pol_names}."

        return EvaluationResult(
            decision=final_decision,
            matched_policies=[p.id for p in matched_policies],
            reasons=reasons,
            decision_precedence_trace=precedence_trace,
        )

    def evaluate(
        self,
        context: RequestContext | SecurityContext,
        policies: list[Policy] | AbstractPolicyRepository,
    ) -> EvaluationResult:
        """Evaluate a request or security context against a policy list or repository."""
        if isinstance(policies, AbstractPolicyRepository):
            policy_list = policies.get_all()
        else:
            policy_list = policies

        if isinstance(context, RequestContext):
            sec_context = context_aggregator.from_request_context(context)
        else:
            sec_context = context

        from app.risk.evaluator import risk_evaluator
        assessment = risk_evaluator.evaluate(sec_context)

        from app.engine.models import PolicyTraceSummary, SignalSummary

        policy_traces: list[PolicyTraceSummary] = []
        matched: list[Policy] = []
        for p in policy_list:
            is_matched = self.is_policy_matched(sec_context, p)
            if is_matched:
                matched.append(p)

            cond_details = condition_registry.evaluate_detailed(sec_context, p)
            exclusion_detail = next((c for c in cond_details if c.condition_type == "EXCLUSION"), None)
            is_excluded = False
            exclusion_reason = None
            if exclusion_detail and exclusion_detail.result == "NO_MATCH":
                is_excluded = True
                exclusion_reason = exclusion_detail.reason

            policy_traces.append(
                PolicyTraceSummary(
                    policy_id=p.id,
                    policy_name=p.name,
                    enabled=p.enabled,
                    matched=is_matched,
                    excluded=is_excluded,
                    exclusion_reason=exclusion_reason,
                    action=p.action,
                    target_roles=p.target_roles,
                    target_protocols=p.target_protocols,
                    target_risk_level=p.target_risk_level,
                    condition_details=cond_details,
                )
            )

        evaluated_signals: list[SignalSummary] = []
        for sig in sec_context.signals.values():
            val = sig.value.value if hasattr(sig.value, "value") else sig.value
            src = sig.source.value if hasattr(sig.source, "value") else str(sig.source)
            st = sig.status.value if hasattr(sig.status, "value") else str(sig.status)
            conf = sig.confidence.value if hasattr(sig.confidence, "value") else str(sig.confidence)
            evaluated_signals.append(
                SignalSummary(
                    name=sig.name,
                    value=val,
                    source=src,
                    status=st,
                    confidence=conf,
                )
            )

        res = self.resolve_decision(matched)
        res.risk_level = (
            assessment.level.value
            if hasattr(assessment.level, "value")
            else str(assessment.level)
        )
        res.risk_factors = [f.name for f in assessment.factors]
        res.risk_trace = assessment.trace
        res.evaluated_signals = evaluated_signals
        res.policy_traces = policy_traces
        return res



policy_evaluator = PolicyEvaluator()

