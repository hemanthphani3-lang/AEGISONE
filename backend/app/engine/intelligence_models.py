from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyHealthStatus(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class IntelligenceFinding(BaseModel):
    """Structured policy intelligence finding model."""

    finding_type: str = Field(description="Finding category code e.g. CONFLICT, SHADOWED, BROAD_SCOPE, DANGEROUS, DUPLICATE")
    severity: FindingSeverity = Field(description="Severity classification of the finding")
    reason: str = Field(description="Explainable human-readable reasoning for the finding")
    affected_policy_ids: list[str] = Field(default_factory=list, description="IDs of related or conflicting policies")
    recommendation: str = Field(description="Actionable remediation recommendation")


class PolicyHealthSummary(BaseModel):
    """Health summary for a single policy."""

    policy_id: str
    status: PolicyHealthStatus
    score: int = Field(ge=0, le=100, description="Health score index from 0 (Critical) to 100 (Safe)")
    findings: list[IntelligenceFinding] = Field(default_factory=list)


class PolicyIntelligenceReport(BaseModel):
    """Global intelligence analysis report across all active policies."""

    total_policies: int
    enabled_policies: int
    disabled_policies: int
    health_counts: dict[str, int] = Field(description="Counts by PolicyHealthStatus (SAFE, REVIEW, WARNING, CRITICAL)")
    findings_count: int
    policy_health_summaries: list[PolicyHealthSummary]
    global_findings: list[IntelligenceFinding]
