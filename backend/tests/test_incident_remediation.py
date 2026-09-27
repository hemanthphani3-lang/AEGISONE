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


def test_sync_intelligence_and_deduplication():
    """Verify automated sync creates incidents for HIGH/CRITICAL findings and deduplicates active incidents."""
    admin_headers = get_headers("ADMIN")

    # 1. Sync intelligence
    sync_resp1 = client.post("/api/v1/incidents/sync-intelligence", headers=admin_headers)
    assert sync_resp1.status_code == 200
    res1 = sync_resp1.json()
    assert res1["success"] is True

    # 2. Sync intelligence second time -> created_count should be 0 due to fingerprint deduplication
    sync_resp2 = client.post("/api/v1/incidents/sync-intelligence", headers=admin_headers)
    assert sync_resp2.status_code == 200
    res2 = sync_resp2.json()
    assert res2["created_count"] == 0


def test_incident_remediation_disable_policy():
    """Verify remediating an incident by disabling the target policy."""
    admin_headers = get_headers("ADMIN")

    # 1. Ensure test policy exists
    pol_id = "test-remediate-dis-1"
    client.delete(f"/api/v1/policies/{pol_id}", headers=admin_headers)

    create_pol_resp = client.post(
        "/api/v1/policies",
        json={
            "id": pol_id,
            "name": "Remediation Disable Test Policy",
            "description": "Policy to test remediation disable",
            "enabled": True,
            "action": "BLOCK",
            "target_roles": ["STUDENT"],
        },
        headers=admin_headers,
    )
    assert create_pol_resp.status_code == 201

    # 2. Create incident linked to test policy
    inc_resp = client.post(
        "/api/v1/incidents",
        json={
            "title": f"Test Incident for {pol_id}",
            "description": "Remediation test incident",
            "severity": "HIGH",
            "status": "OPEN",
            "policy_id": pol_id,
        },
        headers=admin_headers,
    )
    assert inc_resp.status_code == 201
    inc_id = inc_resp.json()["id"]

    # 3. Remediate -> DISABLE_POLICY
    remediate_resp = client.post(
        f"/api/v1/incidents/{inc_id}/remediate",
        json={
            "action": "DISABLE_POLICY",
            "reason": "Disabling policy due to critical finding",
        },
        headers=admin_headers,
    )
    assert remediate_resp.status_code == 200
    rem_data = remediate_resp.json()
    assert rem_data["success"] is True
    assert rem_data["policy_id"] == pol_id

    # 4. Verify policy is now disabled
    get_pol_resp = client.get(f"/api/v1/policies/{pol_id}", headers=admin_headers)
    assert get_pol_resp.status_code == 200
    assert get_pol_resp.json()["enabled"] is False

    # Clean up
    client.delete(f"/api/v1/policies/{pol_id}", headers=admin_headers)


def test_incident_remediation_occ_conflict():
    """Verify remediation with stale expected_version triggers 409 POLICY_CONCURRENCY_CONFLICT."""
    admin_headers = get_headers("ADMIN")

    pol_id = "test-remediate-occ-1"
    client.delete(f"/api/v1/policies/{pol_id}", headers=admin_headers)

    client.post(
        "/api/v1/policies",
        json={
            "id": pol_id,
            "name": "Remediation OCC Policy",
            "description": "Policy for OCC conflict test",
            "enabled": True,
            "action": "BLOCK",
            "target_roles": ["STUDENT"],
        },
        headers=admin_headers,
    )

    inc_resp = client.post(
        "/api/v1/incidents",
        json={
            "title": f"OCC Test Incident for {pol_id}",
            "description": "OCC conflict test",
            "severity": "CRITICAL",
            "status": "OPEN",
            "policy_id": pol_id,
        },
        headers=admin_headers,
    )
    inc_id = inc_resp.json()["id"]

    # Remediate with mismatched expected_version (e.g. 99) -> 409 Conflict
    remediate_resp = client.post(
        f"/api/v1/incidents/{inc_id}/remediate",
        json={
            "action": "DISABLE_POLICY",
            "expected_version": 99,
            "reason": "Stale version test",
        },
        headers=admin_headers,
    )
    assert remediate_resp.status_code == 409
    assert "POLICY_CONCURRENCY_CONFLICT" in str(remediate_resp.json()["detail"])

    # Clean up
    client.delete(f"/api/v1/policies/{pol_id}", headers=admin_headers)


def test_incident_secret_safety():
    """Verify secret credentials are never leaked in incident responses or timeline events."""
    admin_headers = get_headers("ADMIN")
    resp = client.get("/api/v1/incidents", headers=admin_headers)
    assert resp.status_code == 200
    resp_text = resp.text
    forbidden_tokens = ["secret", "password", "Bearer ", "private_key", "client_secret"]
    for token in forbidden_tokens:
        assert token not in resp_text
