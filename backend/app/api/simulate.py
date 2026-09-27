from fastapi import APIRouter, Depends, HTTPException, Request
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.service import audit_service
from app.auth.authorization import require_roles
from app.auth.context_builder import identity_context_builder
from app.auth.models import AuthenticatedUser
from app.db.session import async_session_factory, check_database_connection
from app.engine.enums import UserRole
from app.engine.postgres_repository import PostgresPolicyRepository
from app.engine.repository import policy_repository as in_memory_repo
from app.signals.aggregator import context_aggregator
from app.simulation.models import SimulationRequest, SimulationResult
from app.simulation.service import simulation_service

from app.auth.authorization import Permission, require_permission

router = APIRouter()

require_simulation_permission = require_permission(
    Permission.RUN_SIMULATION,
    action="SIMULATE_EVALUATION",
    resource_type="SIMULATION",
)


@router.post("/policies/simulate", response_model=SimulationResult)
@router.post("/simulate/evaluate", response_model=SimulationResult)
async def simulate_evaluate(
    request_body: SimulationRequest,
    raw_request: Request = None,
    current_user: AuthenticatedUser = Depends(require_simulation_permission),
) -> SimulationResult:
    """Run a hypothetical policy simulation using a provided RequestContext or caller context."""
    session = None
    try:
        correlation_id = getattr(getattr(raw_request, "state", None), "correlation_id", None)

        if request_body.base_context:
            base_context = context_aggregator.from_request_context(request_body.base_context)
        else:
            base_context = identity_context_builder.build_security_context(
                current_user, request_body.client_data
            )

        if await check_database_connection():
            session = async_session_factory()
            repo = PostgresPolicyRepository(session)
            policies = await repo.get_all_async()
        else:
            policies = in_memory_repo.get_all()

        if request_body.policy_ids:
            target_ids = set(request_body.policy_ids)
            policies = [p for p in policies if p.id in target_ids]

        sim_result = simulation_service.run_simulation(
            base_context=base_context,
            overrides=request_body.overrides,
            policies=policies,
            correlation_id=correlation_id,
        )

        await audit_service.record_event(
            event_type=AuditEventType.POLICY_SIMULATED,
            action="SIMULATE_POLICY",
            resource_type="POLICY_ENGINE",
            outcome=AuditOutcome.SUCCESS,
            actor=current_user,
            metadata={
                "simulation_id": sim_result.simulation_id,
                "base_decision": sim_result.base_decision.value,
                "simulated_decision": sim_result.simulated_decision.value,
                "decision_changed": sim_result.decision_changed,
                "base_risk": sim_result.base_risk.value,
                "simulated_risk": sim_result.simulated_risk.value,
                "risk_changed": sim_result.risk_changed,
            },
            session=session,
        )
        if session:
            await session.commit()

        return sim_result

    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=500, detail="Policy simulation failed due to a server error."
        )
    finally:
        if session:
            await session.close()


@router.post("/simulate/evaluate/me", response_model=SimulationResult)
async def simulate_evaluate_me(
    request_body: SimulationRequest,
    raw_request: Request = None,
    current_user: AuthenticatedUser = Depends(require_simulation_permission),
) -> SimulationResult:
    """Run a hypothetical policy simulation for the authenticated caller with optional context overrides."""
    session = None
    try:
        correlation_id = getattr(getattr(raw_request, "state", None), "correlation_id", None)
        base_context = identity_context_builder.build_security_context(
            current_user, request_body.client_data
        )

        if await check_database_connection():
            session = async_session_factory()
            repo = PostgresPolicyRepository(session)
            policies = await repo.get_all_async()
        else:
            policies = in_memory_repo.get_all()

        if request_body.policy_ids:
            target_ids = set(request_body.policy_ids)
            policies = [p for p in policies if p.id in target_ids]

        sim_result = simulation_service.run_simulation(
            base_context=base_context,
            overrides=request_body.overrides,
            policies=policies,
            correlation_id=correlation_id,
        )

        await audit_service.record_event(
            event_type=AuditEventType.POLICY_SIMULATED,
            action="SIMULATE_POLICY",
            resource_type="POLICY_ENGINE",
            outcome=AuditOutcome.SUCCESS,
            actor=current_user,
            metadata={
                "simulation_id": sim_result.simulation_id,
                "base_decision": sim_result.base_decision.value,
                "simulated_decision": sim_result.simulated_decision.value,
                "decision_changed": sim_result.decision_changed,
                "base_risk": sim_result.base_risk.value,
                "simulated_risk": sim_result.simulated_risk.value,
                "risk_changed": sim_result.risk_changed,
            },
            session=session,
        )
        if session:
            await session.commit()

        return sim_result

    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=500, detail="Policy simulation failed due to a server error."
        )
    finally:
        if session:
            await session.close()
