import asyncio
from fastapi.testclient import TestClient
from app.auth.verifier import jwt_verifier
from app.db.session import create_tables
from app.main import app
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    jwt_verifier._signing_key = SECRET_KEY
    asyncio.run(create_tables())


def get_headers(role: str) -> dict[str, str]:
    token = generate_test_token(sub=f"user-{role.lower()}", roles=[role])
    return {"Authorization": f"Bearer {token}"}


def test_incidents_permissions():
    """Verify RBAC permissions for GET /api/v1/incidents (401, 403, 200)."""
    # 1. Unauthenticated -> 401
    resp = client.get("/api/v1/incidents")
    assert resp.status_code == 401

    # 2. STUDENT -> 403
    resp_student = client.get("/api/v1/incidents", headers=get_headers("STUDENT"))
    assert resp_student.status_code == 403

    # 3. STAFF -> 200 (READ_INCIDENTS)
    resp_staff = client.get("/api/v1/incidents", headers=get_headers("STAFF"))
    assert resp_staff.status_code == 200
    assert "incidents" in resp_staff.json()

    # 4. ADMIN -> 200
    resp_admin = client.get("/api/v1/incidents", headers=get_headers("ADMIN"))
    assert resp_admin.status_code == 200

    # 5. SECURITY_ADMIN -> 200
    resp_sec = client.get("/api/v1/incidents", headers=get_headers("SECURITY_ADMIN"))
    assert resp_sec.status_code == 200


def test_incident_lifecycle_and_state_machine():
    """Verify manual creation, valid transitions, invalid transitions (422), comments, and assignment."""
    admin_headers = get_headers("ADMIN")

    # 1. Create incident
    create_payload = {
        "title": "Unrestricted Admin Role Target",
        "description": "Policy admin-broad targets all locations without restriction.",
        "severity": "HIGH",
        "status": "OPEN",
        "source_type": "MANUAL",
        "policy_id": "admin-mfa",
    }
    create_resp = client.post("/api/v1/incidents", json=create_payload, headers=admin_headers)
    assert create_resp.status_code == 201
    inc_data = create_resp.json()
    inc_id = inc_data["id"]
    assert inc_data["status"] == "OPEN"
    assert inc_data["severity"] == "HIGH"

    # 2. Test invalid transition OPEN -> REOPENED (422)
    invalid_resp = client.post(f"/api/v1/incidents/{inc_id}/reopen", headers=admin_headers)
    assert invalid_resp.status_code == 422
    assert "Invalid incident status transition" in invalid_resp.json()["detail"]

    # 3. Acknowledge incident OPEN -> ACKNOWLEDGED
    ack_resp = client.post(f"/api/v1/incidents/{inc_id}/acknowledge", headers=admin_headers)
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    # 4. Assign incident
    assign_resp = client.post(
        f"/api/v1/incidents/{inc_id}/assign?assigned_to=sec_officer_1",
        headers=admin_headers,
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assigned_to"] == "sec_officer_1"

    # 5. Add comment
    comment_resp = client.post(
        f"/api/v1/incidents/{inc_id}/comment?comment=Inspecting+target+roles+and+exclusions",
        headers=admin_headers,
    )
    assert comment_resp.status_code == 200

    # 6. Resolve incident ACKNOWLEDGED -> RESOLVED
    resolve_resp = client.post(
        f"/api/v1/incidents/{inc_id}/resolve?resolution_summary=Exclusions+configured",
        headers=admin_headers,
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["resolution_summary"] == "Exclusions configured"

    # 7. Reopen incident RESOLVED -> REOPENED
    reopen_resp = client.post(f"/api/v1/incidents/{inc_id}/reopen", headers=admin_headers)
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "REOPENED"

    # 8. Fetch timeline events
    events_resp = client.get(f"/api/v1/incidents/{inc_id}/events", headers=admin_headers)
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 5
    event_types = [ev["event_type"] for ev in events]
    assert "INCIDENT_CREATED" in event_types
    assert "INCIDENT_ACKNOWLEDGED" in event_types
    assert "INCIDENT_ASSIGNED" in event_types
    assert "INCIDENT_COMMENTED" in event_types
    assert "INCIDENT_RESOLVED" in event_types
    assert "INCIDENT_REOPENED" in event_types


def test_incidents_stats():
    """Verify GET /api/v1/incidents/stats endpoint."""
    headers = get_headers("SECURITY_ADMIN")
    resp = client.get("/api/v1/incidents/stats", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_incidents" in stats
    assert "open_incidents" in stats
    assert "critical_incidents" in stats
    assert "high_incidents" in stats
    assert "unassigned_incidents" in stats
    assert "policies_at_risk_count" in stats
