import pytest
from fastapi.testclient import TestClient
from app.auth.authorization import Permission
from app.auth.verifier import JWTVerifier
from app.main import app

client = TestClient(app)


def test_evaluate_unauthenticated_returns_401():
    """Verify POST /api/v1/evaluate returns 401 Unauthorized when Bearer token is missing."""
    payload = {
        "user_id": "test-user-001",
        "roles": ["STUDENT"],
        "protocol": "OIDC",
        "location": "US",
    }
    response = client.post("/api/v1/evaluate", json=payload)
    assert response.status_code == 401


def test_intelligence_endpoint_requires_read_permission():
    """Verify GET /api/v1/policies/intelligence returns 401 without auth token."""
    response = client.get("/api/v1/policies/intelligence")
    assert response.status_code == 401


def test_jwt_verifier_audience_validation(monkeypatch):
    """Verify JWTVerifier handles audience validation and rejects invalid audience when aud is present."""
    verifier = JWTVerifier(client_id="accessguard-backend")
    
    import jwt
    # Generate token with mismatched audience
    payload = {
        "sub": "user-123",
        "preferred_username": "user123",
        "roles": ["ADMIN"],
        "iss": verifier.issuer,
        "aud": "wrong-client-id",
    }
    secret = "test-secret-key-32-bytes-minimum!!"
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    verifier._signing_key = secret

    with pytest.raises(ValueError) as exc_info:
        verifier.verify_token(token)
    assert "audience" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
