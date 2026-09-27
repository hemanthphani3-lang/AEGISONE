from fastapi.testclient import TestClient
from app.auth.verifier import jwt_verifier
from app.main import app
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    jwt_verifier._signing_key = SECRET_KEY


def get_auth_headers():
    token = generate_test_token(sub="eval-tester", roles=["ADMIN"])
    return {"Authorization": f"Bearer {token}"}


def test_api_evaluate_success_admin_mfa_required():
    """API Test: Admin + Modern + MFA not completed -> MFA_REQUIRED."""
    payload = {
        "user_id": "admin01",
        "role": "ADMIN",
        "location": "IN",
        "device": {"managed": True, "compliant": True},
        "authentication": {"protocol": "MODERN", "mfa_completed": False},
    }
    response = client.post("/api/v1/evaluate", json=payload, headers=get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "MFA_REQUIRED"
    assert "admin-mfa" in data["matched_policies"]
    assert len(data["reasons"]) > 0


def test_api_evaluate_legacy_auth_block():
    """API Test: Legacy auth -> BLOCK."""
    payload = {
        "user_id": "user01",
        "role": "STUDENT",
        "location": "IN",
        "device": {"managed": False, "compliant": False},
        "authentication": {"protocol": "LEGACY", "mfa_completed": False},
    }
    response = client.post("/api/v1/evaluate", json=payload, headers=get_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert "block-legacy-auth" in data["matched_policies"]


def test_api_evaluate_invalid_role_422():
    """19. Test POST /api/v1/evaluate with invalid role returns HTTP 422."""
    payload = {
        "user_id": "u1",
        "role": "SUPERMAN",  # Invalid role
        "location": "IN",
        "device": {"managed": True, "compliant": True},
        "authentication": {"protocol": "MODERN", "mfa_completed": False},
    }
    response = client.post("/api/v1/evaluate", json=payload, headers=get_auth_headers())
    assert response.status_code == 422


def test_api_evaluate_invalid_auth_protocol_422():
    """20. Test POST /api/v1/evaluate with invalid auth protocol returns HTTP 422."""
    payload = {
        "user_id": "u1",
        "role": "ADMIN",
        "location": "IN",
        "device": {"managed": True, "compliant": True},
        "authentication": {"protocol": "MAGIC_PROTOCOL", "mfa_completed": False},
    }
    response = client.post("/api/v1/evaluate", json=payload, headers=get_auth_headers())
    assert response.status_code == 422


def test_api_evaluate_missing_required_field_422():
    """21. Test POST /api/v1/evaluate missing required user_id returns HTTP 422."""
    payload = {
        # "user_id" is missing
        "role": "ADMIN",
        "location": "IN",
        "device": {"managed": True, "compliant": True},
        "authentication": {"protocol": "MODERN", "mfa_completed": False},
    }
    response = client.post("/api/v1/evaluate", json=payload, headers=get_auth_headers())
    assert response.status_code == 422
