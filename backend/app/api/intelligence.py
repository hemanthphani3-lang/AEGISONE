from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.authorization import Permission, require_permission
from app.auth.models import AuthenticatedUser
from app.engine.intelligence import policy_intelligence_engine
from app.engine.intelligence_models import (
    IntelligenceFinding,
    PolicyHealthSummary,
    PolicyIntelligenceReport,
)
from app.services.policy_service import policy_service

router = APIRouter()


@router.get("/policies/intelligence", response_model=PolicyIntelligenceReport)
async def get_policy_intelligence_report(
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> PolicyIntelligenceReport:
    """Retrieve global policy intelligence report, static analysis findings, and health distribution."""
    policies = await policy_service.list_policies()
    return policy_intelligence_engine.analyze_all(policies)


@router.get("/policies/{policy_id}/health", response_model=PolicyHealthSummary)
async def get_policy_health(
    policy_id: str,
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> PolicyHealthSummary:
    """Retrieve deterministic health summary and findings for a specific policy."""
    policy = await policy_service.get_policy_by_id(policy_id)
    all_policies = await policy_service.list_policies()
    report = policy_intelligence_engine.analyze_all(all_policies)
    
    summary = next((s for s in report.policy_health_summaries if s.policy_id == policy.id), None)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Health analysis for policy '{policy_id}' not found.",
        )
    return summary


@router.get("/policies/{policy_id}/conflicts", response_model=list[IntelligenceFinding])
async def get_policy_conflicts(
    policy_id: str,
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> list[IntelligenceFinding]:
    """Retrieve all conflict findings affecting a specific policy."""
    policy = await policy_service.get_policy_by_id(policy_id)
    all_policies = await policy_service.list_policies()
    report = policy_intelligence_engine.analyze_all(all_policies)
    
    conflicts = [
        f for f in report.global_findings
        if f.finding_type == "CONFLICT" and policy.id in f.affected_policy_ids
    ]
    return conflicts


@router.get("/policies/{policy_id}/shadowed", response_model=list[IntelligenceFinding])
async def get_policy_shadowed(
    policy_id: str,
    user: AuthenticatedUser = Depends(require_permission(Permission.READ_POLICY)),
) -> list[IntelligenceFinding]:
    """Retrieve all shadowed policy findings affecting a specific policy."""
    policy = await policy_service.get_policy_by_id(policy_id)
    all_policies = await policy_service.list_policies()
    report = policy_intelligence_engine.analyze_all(all_policies)
    
    shadowed = [
        f for f in report.global_findings
        if f.finding_type == "SHADOWED" and policy.id in f.affected_policy_ids
    ]
    return shadowed
