from fastapi.testclient import TestClient
from app.auth.verifier import jwt_verifier
from app.main import app
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation and clean up non-default test policies."""
    jwt_verifier._signing_key = SECRET_KEY
    admin_token = generate_test_token(sub="cleanup-admin", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/policies", headers=headers)
    if resp.status_code == 200:
        default_ids = {"admin-mfa", "block-legacy-auth", "impossible-travel", "untrusted-device"}
        for policy in resp.json().get("policies", []):
            if policy["id"] not in default_ids:
                client.delete(f"/api/v1/policies/{policy['id']}", headers=headers)


def test_evaluate_me_no_token_401():
    """POST /api/v1/evaluate/me without token returns 401 Unauthorized."""
    response = client.post("/api/v1/evaluate/me")
    assert response.status_code == 401


def test_evaluate_me_invalid_token_401():
    """POST /api/v1/evaluate/me with bad token returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = client.post("/api/v1/evaluate/me", headers=headers)
    assert response.status_code == 401


def test_evaluate_me_admin_mfa_incomplete_mfa_required():
    """13. ADMIN + MFA incomplete -> MFA_REQUIRED."""
    token = generate_test_token(
        sub="keycloak-admin-sub-1", preferred_username="admin01", roles=["ADMIN"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/evaluate/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "MFA_REQUIRED"
    assert "admin-mfa" in data["matched_policies"]


def test_evaluate_me_student_allow():
    """14. STUDENT + no restrictive policy -> ALLOW."""
    token = generate_test_token(
        sub="keycloak-student-sub-1", preferred_username="student01", roles=["STUDENT"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/evaluate/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["matched_policies"] == []


def test_evaluate_me_breakglass_exclusion_allow():
    """15. BREAK_GLASS + Admin MFA exclusion -> Admin MFA policy does not match -> ALLOW."""
    token = generate_test_token(
        sub="keycloak-bg-sub-1", preferred_username="breakglass01", roles=["BREAK_GLASS"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/evaluate/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert "admin-mfa" not in data["matched_policies"]


def test_evaluate_me_anti_spoofing_prevented():
    """11 & 12. Authenticated STUDENT attempting to spoof role=ADMIN in body is evaluated as STUDENT."""
    token = generate_test_token(
        sub="keycloak-student-sub-2", preferred_username="student01", roles=["STUDENT"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    spoof_body = {
        "user_id": "admin01",
        "role": "ADMIN",
        "roles": ["ADMIN"],
    }
    response = client.post("/api/v1/evaluate/me", headers=headers, json=spoof_body)
    assert response.status_code == 200
    data = response.json()
    # Should evaluate as STUDENT -> ALLOW (not MFA_REQUIRED!)
    assert data["decision"] == "ALLOW"
    assert "admin-mfa" not in data["matched_policies"]
