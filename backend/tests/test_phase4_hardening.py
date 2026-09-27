import pytest
from fastapi.testclient import TestClient
from app.auth.verifier import jwt_verifier
from app.main import app
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation."""
    jwt_verifier._signing_key = SECRET_KEY


def test_occ_update_with_current_and_stale_version():
    """Verify update with current expected_version succeeds, while stale version returns 409 Conflict."""
    admin_token = generate_test_token(sub="admin-occ-user", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}
    policy_id = "phase4-occ-update-p1"

    # Pre-cleanup
    client.delete(f"/api/v1/policies/{policy_id}", headers=headers)

    # 1. Create policy -> version 1
    create_payload = {
        "id": policy_id,
        "name": "Phase 4 OCC Policy",
        "description": "Initial description",
        "action": "MFA_REQUIRED",
        "target_roles": ["STAFF"],
    }
    res_create = client.post("/api/v1/policies", headers=headers, json=create_payload)
    assert res_create.status_code == 201
    assert res_create.json()["version"] == 1

    # 2. Update with expected_version = 1 -> succeeds, version becomes 2
    res_update_v1 = client.patch(
        f"/api/v1/policies/{policy_id}",
        headers=headers,
        json={"name": "Phase 4 OCC Policy Updated", "expected_version": 1},
    )
    assert res_update_v1.status_code == 200
    assert res_update_v1.json()["version"] == 2

    # 3. Attempt update with stale expected_version = 1 -> 409 Conflict
    res_stale = client.patch(
        f"/api/v1/policies/{policy_id}",
        headers=headers,
        json={"name": "Stale Overwrite Attempt", "expected_version": 1},
    )
    assert res_stale.status_code == 409
    err = res_stale.json()["detail"]
    assert err["code"] == "POLICY_CONCURRENCY_CONFLICT"
    assert err["expected_version"] == 1
    assert err["current_version"] == 2

    # 4. Retry with refreshed expected_version = 2 -> succeeds, version becomes 3
    res_fresh = client.patch(
        f"/api/v1/policies/{policy_id}",
        headers=headers,
        json={"name": "Fresh Update", "expected_version": 2},
    )
    assert res_fresh.status_code == 200
    assert res_fresh.json()["version"] == 3

    # Cleanup
    client.delete(f"/api/v1/policies/{policy_id}", headers=headers)


def test_occ_rollback_with_current_and_stale_version():
    """Verify rollback with current expected_current_version succeeds, while stale version returns 409 Conflict."""
    admin_token = generate_test_token(sub="admin-occ-rollback", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}
    policy_id = "phase4-occ-rollback-p1"

    # Pre-cleanup
    client.delete(f"/api/v1/policies/{policy_id}", headers=headers)

    # v1: action = BLOCK
    client.post(
        "/api/v1/policies",
        headers=headers,
        json={"id": policy_id, "name": "Original v1", "description": "Desc", "action": "BLOCK"},
    )

    # v2: action = MFA_REQUIRED
    client.patch(
        f"/api/v1/policies/{policy_id}",
        headers=headers,
        json={"action": "MFA_REQUIRED", "expected_version": 1},
    )

    # Stale Rollback Check (expected_current_version = 1 vs actual current 2) -> 409 Conflict
    rb_stale = client.post(
        f"/api/v1/policies/{policy_id}/rollback",
        headers=headers,
        json={"target_version": 1, "expected_current_version": 1},
    )
    assert rb_stale.status_code == 409
    err = rb_stale.json()["detail"]
    assert err["code"] == "POLICY_CONCURRENCY_CONFLICT"

    # Valid Rollback (expected_current_version = 2) -> creates v3
    rb_valid = client.post(
        f"/api/v1/policies/{policy_id}/rollback",
        headers=headers,
        json={"target_version": 1, "expected_current_version": 2},
    )
    assert rb_valid.status_code == 200
    res_data = rb_valid.json()
    assert res_data["version"] == 3
    assert res_data["action"] == "BLOCK"
    assert res_data["name"] == "Original v1"

    # Cleanup
    client.delete(f"/api/v1/policies/{policy_id}", headers=headers)


def test_status_code_error_payloads():
    """Verify correct status code responses (401, 403, 404, 409, 422)."""
    admin_token = generate_test_token(sub="admin-err-user", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    student_token = generate_test_token(sub="student-err-user", roles=["STUDENT"])
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 401 Unauthenticated
    assert client.get("/api/v1/policies").status_code == 401

    # 403 Forbidden
    assert client.post("/api/v1/policies", headers=student_headers, json={}).status_code == 403

    # 404 Not Found
    assert client.get("/api/v1/policies/non-existent-policy-9999", headers=admin_headers).status_code == 404

    # 409 Duplicate ID Conflict on Create
    p_id = "phase4-dup-id-p1"
    client.delete(f"/api/v1/policies/{p_id}", headers=admin_headers)
    c_payload = {"id": p_id, "name": "Dup P", "description": "D", "action": "ALLOW"}
    assert client.post("/api/v1/policies", headers=admin_headers, json=c_payload).status_code == 201
    assert client.post("/api/v1/policies", headers=admin_headers, json=c_payload).status_code == 409
    client.delete(f"/api/v1/policies/{p_id}", headers=admin_headers)

    # 422 Validation Failure (conflict between targeted role and excluded role)
    invalid_payload = {
        "id": "phase4-invalid-p1",
        "name": "Invalid P",
        "description": "D",
        "action": "BLOCK",
        "target_roles": ["ADMIN"],
        "exclusions": ["ADMIN"],
    }
    res_val = client.post("/api/v1/policies/validate", headers=admin_headers, json=invalid_payload)
    assert res_val.status_code == 200
    assert res_val.json()["valid"] is False
    assert len(res_val.json()["errors"]) > 0


def test_secret_and_credential_sanitization_in_versioning():
    """Verify audit service metadata sanitization redacts secrets when version events are recorded."""
    from app.audit.service import sanitize_metadata

    sensitive_metadata = {
        "access_token": "Bearer eyJhbGciOi...",
        "refresh_token": "ref_abc123",
        "password": "Password123!",
        "client_secret": "secret_xyz",
        "authorization": "Bearer secret_header",
        "policy_id": "safe-policy-id",
        "version": 2,
    }

    sanitized = sanitize_metadata(sensitive_metadata)
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["refresh_token"] == "[REDACTED]"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["client_secret"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["policy_id"] == "safe-policy-id"
    assert sanitized["version"] == 2
