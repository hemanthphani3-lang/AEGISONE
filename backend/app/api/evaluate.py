from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.service import audit_service
from app.auth.authorization import Permission, require_permission
from app.auth.context_builder import identity_context_builder
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser
from app.db.session import async_session_factory, check_database_connection
from app.engine.evaluator import policy_evaluator
from app.engine.models import EvaluationResult, RequestContext
from app.engine.postgres_repository import PostgresPolicyRepository
from app.engine.repository import policy_repository as in_memory_repo
from app.risk.evaluator import risk_evaluator
from app.signals.aggregator import context_aggregator

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_request(
    context: RequestContext,
    raw_request: Request = None,
    user: AuthenticatedUser = Depends(require_permission(Permission.EVALUATE_ACCESS)),
) -> EvaluationResult:
    """Evaluate a RequestContext against all active policies from the repository."""
    session = None
    try:
        correlation_id = getattr(getattr(raw_request, "state", None), "correlation_id", None)
        sec_context = context_aggregator.from_request_context(context)
        assessment = risk_evaluator.evaluate(sec_context)

        if await check_database_connection():
            session = async_session_factory()
            repo = PostgresPolicyRepository(session)
            policies = await repo.get_all_async()
        else:
            policies = in_memory_repo.get_all()

        res = policy_evaluator.evaluate(sec_context, policies)
        res.correlation_id = correlation_id
        await audit_service.record_event(
            event_type=AuditEventType.POLICY_EVALUATED,
            action="EVALUATE_POLICY",
            resource_type="POLICY_ENGINE",
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "decision": res.decision.value,
                "matched_policies": res.matched_policies,
                "reasons": res.reasons,
                "evaluated_user_id": context.user_id,
                "risk_level": assessment.level.value,
                "risk_factors": [f.name for f in assessment.factors],
            },
            actor=user,
            session=session,
        )
        return res
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=500, detail="Policy evaluation failed due to a server error."
        )
    finally:
        if session:
            await session.close()


@router.post("/evaluate/me", response_model=EvaluationResult)
async def evaluate_me(
    client_data: dict[str, Any] | None = None,
    raw_request: Request = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvaluationResult:
    """Evaluate Conditional Access policy against current authenticated Keycloak user context."""
    correlation_id = getattr(getattr(raw_request, "state", None), "correlation_id", None)
    sec_context = identity_context_builder.build_security_context(current_user, client_data)
    assessment = risk_evaluator.evaluate(sec_context)
    session = None
    try:
        if await check_database_connection():
            session = async_session_factory()
            repo = PostgresPolicyRepository(session)
            policies = await repo.get_all_async()
        else:
            policies = in_memory_repo.get_all()

        res = policy_evaluator.evaluate(sec_context, policies)
        res.correlation_id = correlation_id
        await audit_service.record_event(
            event_type=AuditEventType.POLICY_EVALUATED,
            action="EVALUATE_POLICY",
            resource_type="POLICY_ENGINE",
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "decision": res.decision.value,
                "matched_policies": res.matched_policies,
                "reasons": res.reasons,
                "risk_level": assessment.level.value,
                "risk_factors": [f.name for f in assessment.factors],
            },
            actor=current_user,
            session=session,
        )
        return res
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=500, detail="Policy evaluation failed due to a server error."
        )
    finally:
        if session:
            await session.close()


