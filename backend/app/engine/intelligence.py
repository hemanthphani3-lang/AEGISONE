from typing import Any
from app.engine.enums import PolicyDecision, UserRole
from app.engine.intelligence_models import (
    FindingSeverity,
    IntelligenceFinding,
    PolicyHealthStatus,
    PolicyHealthSummary,
    PolicyIntelligenceReport,
)
from app.engine.models import Policy


class PolicyIntelligenceEngine:
    """Engine providing deterministic static security analysis, quality findings, and health scoring for policy sets."""

    @staticmethod
    def _normalize_set(items: list[Any] | None) -> set[str]:
        if not items:
            return set()
        return {item.value if hasattr(item, "value") else str(item) for item in items}

    def detect_broad_policies(self, policies: list[Policy]) -> list[IntelligenceFinding]:
        """Detect policies with empty target roles, protocols, and locations (unconditional scope)."""
        findings: list[IntelligenceFinding] = []
        for p in policies:
            if not p.enabled:
                continue
            has_roles = bool(p.target_roles)
            has_protocols = bool(p.target_protocols)
            has_locations = bool(p.target_locations)

            if not has_roles and not has_protocols and not has_locations:
                findings.append(
                    IntelligenceFinding(
                        finding_type="OVERLY_BROAD",
                        severity=FindingSeverity.MEDIUM,
                        reason=f"Policy '{p.name}' ({p.id}) has no role, protocol, or location restrictions (unconditional scope).",
                        affected_policy_ids=[p.id],
                        recommendation="Restrict policy targets by specifying explicit roles, authentication protocols, or geographic locations.",
                    )
                )
        return findings

    def detect_duplicates(self, policies: list[Policy]) -> list[IntelligenceFinding]:
        """Detect multiple active policies with identical conditions and actions."""
        findings: list[IntelligenceFinding] = []
        enabled_pols = [p for p in policies if p.enabled]
        n = len(enabled_pols)

        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = enabled_pols[i], enabled_pols[j]
                if (
                    p1.action == p2.action
                    and self._normalize_set(p1.target_roles) == self._normalize_set(p2.target_roles)
                    and self._normalize_set(p1.target_protocols) == self._normalize_set(p2.target_protocols)
                    and set(p1.target_locations or []) == set(p2.target_locations or [])
                    and self._normalize_set(p1.exclusions) == self._normalize_set(p2.exclusions)
                    and set(p1.excluded_users or []) == set(p2.excluded_users or [])
                ):
                    findings.append(
                        IntelligenceFinding(
                            finding_type="DUPLICATE",
                            severity=FindingSeverity.LOW,
                            reason=f"Policy '{p1.name}' ({p1.id}) and Policy '{p2.name}' ({p2.id}) have identical conditions and actions.",
                            affected_policy_ids=[p1.id, p2.id],
                            recommendation="Consolidate duplicate policies into a single policy definition to prevent rule bloat.",
                        )
                    )
        return findings

    def detect_conflicts(self, policies: list[Policy]) -> list[IntelligenceFinding]:
        """Detect contradictory policy pairs (e.g., Policy A allows while Policy B blocks matching contexts)."""
        findings: list[IntelligenceFinding] = []
        enabled_pols = [p for p in policies if p.enabled]
        n = len(enabled_pols)

        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = enabled_pols[i], enabled_pols[j]
                if p1.action == p2.action:
                    continue

                # Check if actions conflict (BLOCK vs ALLOW)
                is_contradiction = (
                    (p1.action == PolicyDecision.BLOCK and p2.action == PolicyDecision.ALLOW)
                    or (p1.action == PolicyDecision.ALLOW and p2.action == PolicyDecision.BLOCK)
                )
                if not is_contradiction:
                    continue

                # Check role overlap
                r1 = self._normalize_set(p1.target_roles)
                r2 = self._normalize_set(p2.target_roles)
                roles_overlap = (not r1 or not r2) or bool(r1.intersection(r2))

                # Check protocol overlap
                pr1 = self._normalize_set(p1.target_protocols)
                pr2 = self._normalize_set(p2.target_protocols)
                protos_overlap = (not pr1 or not pr2) or bool(pr1.intersection(pr2))

                # Check location overlap
                loc1 = set(p1.target_locations or [])
                loc2 = set(p2.target_locations or [])
                locs_overlap = (not loc1 or not loc2) or bool(loc1.intersection(loc2))

                if roles_overlap and protos_overlap and locs_overlap:
                    findings.append(
                        IntelligenceFinding(
                            finding_type="CONFLICT",
                            severity=FindingSeverity.HIGH,
                            reason=f"Policy '{p1.name}' ({p1.id}, action={p1.action.value}) conflicts with Policy '{p2.name}' ({p2.id}, action={p2.action.value}) for overlapping target contexts.",
                            affected_policy_ids=[p1.id, p2.id],
                            recommendation="Align policy actions or refine target role/protocol scopes so rules are unambiguous.",
                        )
                    )
        return findings

    def detect_shadowed_policies(self, policies: list[Policy]) -> list[IntelligenceFinding]:
        """Detect policies whose decisions are completely overridden by a broader BLOCK policy."""
        findings: list[IntelligenceFinding] = []
        enabled_pols = [p for p in policies if p.enabled]

        block_policies = [p for p in enabled_pols if p.action == PolicyDecision.BLOCK]
        other_policies = [p for p in enabled_pols if p.action != PolicyDecision.BLOCK]

        for block_p in block_policies:
            b_roles = self._normalize_set(block_p.target_roles)
            b_protos = self._normalize_set(block_p.target_protocols)
            b_locs = set(block_p.target_locations or [])

            for other_p in other_policies:
                o_roles = self._normalize_set(other_p.target_roles)
                o_protos = self._normalize_set(other_p.target_protocols)
                o_locs = set(other_p.target_locations or [])

                # Check if block policy scope covers or subsumes other policy scope
                roles_subsumed = not b_roles or (o_roles and o_roles.issubset(b_roles))
                protos_subsumed = not b_protos or (o_protos and o_protos.issubset(b_protos))
                locs_subsumed = not b_locs or (o_locs and o_locs.issubset(b_locs))

                if roles_subsumed and protos_subsumed and locs_subsumed:
                    findings.append(
                        IntelligenceFinding(
                            finding_type="SHADOWED",
                            severity=FindingSeverity.MEDIUM,
                            reason=f"Policy '{other_p.name}' ({other_p.id}, action={other_p.action.value}) is shadowed by high-precedence BLOCK Policy '{block_p.name}' ({block_p.id}).",
                            affected_policy_ids=[other_p.id, block_p.id],
                            recommendation="Review shadowed policy necessity or adjust condition criteria to make the rule effective.",
                        )
                    )
        return findings

    def detect_dangerous_policies(self, policies: list[Policy]) -> list[IntelligenceFinding]:
        """Detect risky policy rules e.g. ALLOW for HIGH risk level or BLOCK on admins without exclusions."""
        findings: list[IntelligenceFinding] = []
        for p in policies:
            if not p.enabled:
                continue

            # 1. ALLOW action for HIGH risk level
            target_risk = getattr(p, "target_risk_level", None)
            risk_val = target_risk.value if hasattr(target_risk, "value") else str(target_risk or "")
            if p.action == PolicyDecision.ALLOW and risk_val.upper() in {"HIGH", "CRITICAL"}:
                findings.append(
                    IntelligenceFinding(
                        finding_type="DANGEROUS",
                        severity=FindingSeverity.CRITICAL,
                        reason=f"Policy '{p.name}' ({p.id}) explicitly permits ALLOW for {risk_val.upper()} risk sessions.",
                        affected_policy_ids=[p.id],
                        recommendation="Change policy action to MFA_REQUIRED or BLOCK for high-risk access attempts.",
                    )
                )

            # 2. ALLOW for non-compliant or unmanaged devices
            if p.action == PolicyDecision.ALLOW:
                if p.target_device_compliant is False or p.target_device_managed is False:
                    findings.append(
                        IntelligenceFinding(
                            finding_type="DANGEROUS",
                            severity=FindingSeverity.HIGH,
                            reason=f"Policy '{p.name}' ({p.id}) explicitly permits ALLOW for non-compliant or unmanaged devices.",
                            affected_policy_ids=[p.id],
                            recommendation="Require MFA or compliance verification before granting access to unmanaged devices.",
                        )
                    )

            # 3. BLOCK targeting administrative roles without any exclusions (Admin lockout risk!)
            roles = self._normalize_set(p.target_roles)
            admin_roles = {UserRole.ADMIN.value, UserRole.SECURITY_ADMIN.value}
            if p.action == PolicyDecision.BLOCK and roles.intersection(admin_roles):
                has_exclusions = bool(p.exclusions) or bool(p.excluded_users)
                if not has_exclusions:
                    findings.append(
                        IntelligenceFinding(
                            finding_type="DANGEROUS",
                            severity=FindingSeverity.CRITICAL,
                            reason=f"Policy '{p.name}' ({p.id}) blocks administrative roles without break-glass or user exclusions (Lockout Risk!).",
                            affected_policy_ids=[p.id],
                            recommendation="Configure emergency break-glass role or user exclusions to prevent administrative lockout.",
                        )
                    )
        return findings

    def compute_policy_health(self, policy: Policy, findings: list[IntelligenceFinding]) -> PolicyHealthSummary:
        """Compute a deterministic health classification and score index for a single policy."""
        score = 100
        pol_findings = [f for f in findings if policy.id in f.affected_policy_ids]

        for f in pol_findings:
            if f.severity == FindingSeverity.CRITICAL:
                score -= 40
            elif f.severity == FindingSeverity.HIGH:
                score -= 25
            elif f.severity == FindingSeverity.MEDIUM:
                score -= 15
            elif f.severity == FindingSeverity.LOW:
                score -= 5

        score = max(0, min(100, score))

        has_critical = any(f.severity == FindingSeverity.CRITICAL for f in pol_findings)

        if has_critical or score < 50:
            status = PolicyHealthStatus.CRITICAL
        elif score < 75:
            status = PolicyHealthStatus.WARNING
        elif score < 90:
            status = PolicyHealthStatus.REVIEW
        else:
            status = PolicyHealthStatus.SAFE

        return PolicyHealthSummary(
            policy_id=policy.id,
            status=status,
            score=score,
            findings=pol_findings,
        )

    def analyze_all(self, policies: list[Policy]) -> PolicyIntelligenceReport:
        """Run all static analysis detectors and aggregate global report."""
        findings: list[IntelligenceFinding] = []
        findings.extend(self.detect_broad_policies(policies))
        findings.extend(self.detect_duplicates(policies))
        findings.extend(self.detect_conflicts(policies))
        findings.extend(self.detect_shadowed_policies(policies))
        findings.extend(self.detect_dangerous_policies(policies))

        summaries: list[PolicyHealthSummary] = []
        health_counts = {"SAFE": 0, "REVIEW": 0, "WARNING": 0, "CRITICAL": 0}

        for p in policies:
            sum_item = self.compute_policy_health(p, findings)
            summaries.append(sum_item)
            health_counts[sum_item.status.value] += 1

        enabled_count = sum(1 for p in policies if p.enabled)
        disabled_count = len(policies) - enabled_count

        return PolicyIntelligenceReport(
            total_policies=len(policies),
            enabled_policies=enabled_count,
            disabled_policies=disabled_count,
            health_counts=health_counts,
            findings_count=len(findings),
            policy_health_summaries=summaries,
            global_findings=findings,
        )


policy_intelligence_engine = PolicyIntelligenceEngine()
