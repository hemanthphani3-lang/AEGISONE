import pytest
from fastapi.testclient import TestClient

from app.audit.enums import AuditEventType
from app.audit.service import audit_service
from app.auth.verifier import jwt_verifier
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import Policy, RequestContext
from app.engine.repository import policy_repository as in_memory_repo
from app.main import app
from app.risk.enums import RiskLevel
from app.signals.aggregator import context_aggregator
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal
from app.simulation.models import SimulationOverrides, SimulationRequest
from app.simulation.service import simulation_service
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation."""
    jwt_verifier._signing_key = SECRET_KEY


def test_simulation_context_immutability():
    """Verify that running a simulation does NOT mutate the original base SecurityContext."""
    sec_context = SecurityContext()
    sec_context.add_signal(
        SecuritySignal(
            name="identity.roles",
            value=[UserRole.ADMIN],
            source=SignalSource.LOCAL,
            status=SignalStatus.AVAILABLE,
            confidence=SignalConfidence.HIGH,
        )
    )
    sec_context.add_signal(
        SecuritySignal(
            name="auth.mfa_completed",
            value=False,
            source=SignalSource.LOCAL,
            status=SignalStatus.AVAILABLE,
            confidence=SignalConfidence.HIGH,
        )
    )

    # Capture initial signals state
    initial_signals = {
        name: sig.model_copy(deep=True) for name, sig in sec_context.signals.items()
    }

    policies = in_memory_repo.get_all()
    overrides = SimulationOverrides(mfa_completed=True, location="CA")

    sim_result = simulation_service.run_simulation(sec_context, overrides, policies)

    # Verify original context remains 100% unchanged after simulation
    assert len(sec_context.signals) == len(initial_signals)
    assert sec_context.get_value("auth.mfa_completed") is False
    assert sec_context.has_signal("location") is False
    assert sec_context.signals["auth.mfa_completed"].value == initial_signals["auth.mfa_completed"].value


def test_simulation_mfa_override_mfa_required_to_allow():
    """Verify simulation shows MFA_REQUIRED -> ALLOW when MFA completed override is set."""
    req_context = RequestContext(
        user_id="admin1",
        roles=[UserRole.ADMIN],
        authentication={"protocol": "MODERN", "mfa_completed": False},
    )
    base_sec_context = context_aggregator.from_request_context(req_context)
    policies = in_memory_repo.get_all()

    overrides = SimulationOverrides(mfa_completed=True)
    res = simulation_service.run_simulation(base_sec_context, overrides, policies)

    assert res.base_decision == PolicyDecision.MFA_REQUIRED
    assert res.simulated_decision == PolicyDecision.ALLOW
    assert res.decision_changed is True
    assert res.trace.decision_changed is True
    assert any(pc.policy_id == "admin-mfa" for pc in res.trace.policy_changes)


def test_simulation_legacy_to_modern_auth_protocol():
    """Verify simulation of LEGACY -> MODERN authentication protocol."""
    req_context = RequestContext(
        user_id="user1",
        roles=[UserRole.STUDENT],
        authentication={"protocol": "LEGACY", "mfa_completed": False},
    )
    base_sec_context = context_aggregator.from_request_context(req_context)
    policies = [p for p in in_memory_repo.get_all() if p.id in {"admin-mfa", "block-legacy-auth"}]

    overrides = SimulationOverrides(auth_protocol=AuthProtocol.MODERN)
    res = simulation_service.run_simulation(base_sec_context, overrides, policies)

    assert res.base_decision == PolicyDecision.BLOCK
    assert res.simulated_decision == PolicyDecision.ALLOW
    assert res.decision_changed is True


def test_simulation_risk_recomputation():
    """Verify risk is dynamically recomputed when overriding risk-influencing signals."""
    req_context = RequestContext(
        user_id="admin1",
        roles=[UserRole.ADMIN],
        authentication={"protocol": "MODERN", "mfa_completed": False},
    )
    base_sec_context = context_aggregator.from_request_context(req_context)
    policies = in_memory_repo.get_all()

    # Base context risk: ADMIN + no MFA -> HIGH risk
    res_base = simulation_service.run_simulation(base_sec_context, SimulationOverrides(), policies)
    assert res_base.base_risk == RiskLevel.HIGH

    # Override: mfa_completed=True -> Risk recomputes to LOW
    res_sim = simulation_service.run_simulation(
        base_sec_context, SimulationOverrides(mfa_completed=True), policies
    )
    assert res_sim.base_risk == RiskLevel.HIGH
    assert res_sim.simulated_risk == RiskLevel.LOW
    assert res_sim.risk_changed is True


def test_simulation_api_admin_allowed():
    """POST /api/v1/simulate/evaluate/me with ADMIN role returns 200 OK."""
    token = generate_test_token(sub="admin1", preferred_username="admin01", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"mfa_completed": True}, "policy_ids": ["admin-mfa", "block-legacy-auth"]}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data
    assert data["base_decision"] == "MFA_REQUIRED"
    assert data["simulated_decision"] == "ALLOW"
    assert data["decision_changed"] is True


def test_simulation_api_security_admin_allowed():
    """POST /api/v1/simulate/evaluate/me with SECURITY_ADMIN role returns 200 OK."""
    token = generate_test_token(
        sub="secadmin1", preferred_username="secadmin01", roles=["SECURITY_ADMIN"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"device_compliant": True}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 200


def test_simulation_api_staff_denied_403():
    """POST /api/v1/simulate/evaluate/me with STAFF role returns 403 Forbidden."""
    token = generate_test_token(sub="staff1", preferred_username="staff01", roles=["STAFF"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"mfa_completed": True}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 403


def test_simulation_api_student_denied_403():
    """POST /api/v1/simulate/evaluate/me with STUDENT role returns 403 Forbidden."""
    token = generate_test_token(sub="student1", preferred_username="student01", roles=["STUDENT"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"mfa_completed": True}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 403


def test_simulation_api_break_glass_alone_denied_403():
    """POST /api/v1/simulate/evaluate/me with BREAK_GLASS role alone returns 403 Forbidden."""
    token = generate_test_token(
        sub="bg1", preferred_username="breakglass01", roles=["BREAK_GLASS"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"mfa_completed": True}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 403


def test_simulation_api_unauthenticated_401():
    """POST /api/v1/simulate/evaluate/me without Bearer token returns 401 Unauthorized."""
    payload = {"overrides": {"mfa_completed": True}}
    response = client.post("/api/v1/simulate/evaluate/me", json=payload)
    assert response.status_code == 401


def test_simulation_api_invalid_override_422():
    """POST /api/v1/simulate/evaluate/me with unknown override field returns 422 Unprocessable Entity."""
    token = generate_test_token(sub="admin1", preferred_username="admin01", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"unknown_field": "hacked"}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 422


def test_simulation_api_user_id_override_forbidden_422():
    """Attempting to inject user_id override in SimulationOverrides returns 422."""
    token = generate_test_token(sub="admin1", preferred_username="admin01", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"user_id": "target_user_id"}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 422


def test_simulation_role_override_authorization_boundary():
    """Student attempting role override in payload is rejected at authorization layer (403)."""
    token = generate_test_token(sub="student1", preferred_username="student01", roles=["STUDENT"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"roles": ["ADMIN"]}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 403


def test_simulation_records_policy_simulated_audit_event():
    """Simulation records POLICY_SIMULATED audit event rather than standard POLICY_EVALUATED."""
    token = generate_test_token(sub="admin1", preferred_username="admin01", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"overrides": {"mfa_completed": True}}

    response = client.post("/api/v1/simulate/evaluate/me", headers=headers, json=payload)
    assert response.status_code == 200

    audit_resp = client.get(
        "/api/v1/audit/events?event_type=POLICY_SIMULATED",
        headers=headers,
    )
    assert audit_resp.status_code == 200
    events = audit_resp.json()["events"]
    assert len(events) > 0
    latest_sim = events[0]
    assert latest_sim["action"] == "SIMULATE_POLICY"
    assert "simulation_id" in latest_sim["metadata"]


def test_policies_simulate_api_authorization():
    """Verify authorization for POST /api/v1/policies/simulate endpoint across all 5 roles."""
    # ADMIN -> 200
    admin_token = generate_test_token(sub="admin-sim", roles=["ADMIN"])
    resp_admin = client.post(
        "/api/v1/policies/simulate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"overrides": {"mfa_completed": True}},
    )
    assert resp_admin.status_code == 200

    # SECURITY_ADMIN -> 200
    sec_token = generate_test_token(sub="sec-sim", roles=["SECURITY_ADMIN"])
    resp_sec = client.post(
        "/api/v1/policies/simulate",
        headers={"Authorization": f"Bearer {sec_token}"},
        json={"overrides": {"mfa_completed": True}},
    )
    assert resp_sec.status_code == 200

    # STAFF -> 403
    staff_token = generate_test_token(sub="staff-sim", roles=["STAFF"])
    resp_staff = client.post(
        "/api/v1/policies/simulate",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"overrides": {"mfa_completed": True}},
    )
    assert resp_staff.status_code == 403

    # STUDENT -> 403
    student_token = generate_test_token(sub="student-sim", roles=["STUDENT"])
    resp_student = client.post(
        "/api/v1/policies/simulate",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"overrides": {"mfa_completed": True}},
    )
    assert resp_student.status_code == 403

    # BREAK_GLASS -> 403
    bg_token = generate_test_token(sub="bg-sim", roles=["BREAK_GLASS"])
    resp_bg = client.post(
        "/api/v1/policies/simulate",
        headers={"Authorization": f"Bearer {bg_token}"},
        json={"overrides": {"mfa_completed": True}},
    )
    assert resp_bg.status_code == 403

    # Unauthenticated -> 401
    resp_unauth = client.post(
        "/api/v1/policies/simulate",
        json={"overrides": {"mfa_completed": True}},
    )
    assert resp_unauth.status_code == 401


def test_simulation_explanation_model_and_precedence():
    """Verify simulation returns rich evaluation_result with decision_precedence_trace and condition_details."""
    admin_token = generate_test_token(sub="admin-explainer", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "base_context": {
            "user_id": "legacy-sim-user",
            "roles": ["STUDENT"],
            "authentication": {"protocol": "LEGACY", "mfa_completed": False},
        },
        "overrides": {},
    }

    resp = client.post("/api/v1/policies/simulate", headers=headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["simulated_decision"] == "BLOCK"
    assert "evaluation_result" in data
    eval_res = data["evaluation_result"]
    assert "decision_precedence_trace" in eval_res
    assert "BLOCK" in eval_res["decision_precedence_trace"]
    assert "policy_traces" in eval_res

    # Verify condition_details on policy traces
    for pt in eval_res["policy_traces"]:
        assert "condition_details" in pt
        for cd in pt["condition_details"]:
            assert "condition_type" in cd
            assert "result" in cd
            assert "reason" in cd


def test_simulation_secrets_safety_no_sensitive_tokens_leaked():
    """Verify simulation output and response models contain no JWT, tokens, passwords, or cookies."""
    admin_token = generate_test_token(sub="admin-secret-test", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"overrides": {"mfa_completed": True}}

    resp = client.post("/api/v1/policies/simulate", headers=headers, json=payload)
    assert resp.status_code == 200
    raw_text = resp.text

    assert "access_token" not in raw_text
    assert "refresh_token" not in raw_text
    assert "client_secret" not in raw_text
    assert "password" not in raw_text

