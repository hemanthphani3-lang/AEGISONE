import time
import jwt
import pytest
from fastapi.testclient import TestClient
from app.auth.verifier import JWTVerifier, jwt_verifier
from app.config import KEYCLOAK_CLIENT_ID, KEYCLOAK_REALM, KEYCLOAK_URL
from app.main import app

client = TestClient(app)

SECRET_KEY = "test-secret-key-for-jwt-unit-tests"
TEST_ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"


@pytest.fixture(autouse=True)
def configure_test_jwt_verifier():
    """Configure jwt_verifier to use static test secret for unit tests."""
    original_key = jwt_verifier._signing_key
    jwt_verifier._signing_key = SECRET_KEY
    yield
    jwt_verifier._signing_key = original_key


def generate_test_token(
    sub: str = "admin01",
    preferred_username: str = "admin01",
    roles: list[str] | None = None,
    issuer: str = TEST_ISSUER,
    expires_in: int = 3600,
    secret: str = SECRET_KEY,
) -> str:
    """Helper to generate signed JWT tokens for testing."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "preferred_username": preferred_username,
        "iss": issuer,
        "exp": now + expires_in,
        "iat": now,
        "realm_access": {"roles": roles if roles is not None else ["ADMIN"]},
        "resource_access": {
            KEYCLOAK_CLIENT_ID: {"roles": roles if roles is not None else ["ADMIN"]}
        },
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# =====================================================================
# Unit Tests for JWTVerifier
# =====================================================================


def test_verifier_valid_token_claims():
    """Verify claim extraction from valid JWT token."""
    token = generate_test_token(
        sub="user-123", preferred_username="staff01", roles=["STAFF"]
    )
    user = jwt_verifier.verify_token(token)
    assert user.user_id == "user-123"
    assert user.username == "staff01"
    assert user.roles == ["STAFF"]


def test_verifier_expired_token():
    """Verify expired token raises ValueError."""
    token = generate_test_token(expires_in=-10)
    with pytest.raises(ValueError, match="expired"):
        jwt_verifier.verify_token(token)


def test_verifier_invalid_issuer():
    """Verify invalid issuer raises ValueError."""
    token = generate_test_token(issuer="http://wrong-issuer/realms/wrong")
    with pytest.raises(ValueError, match="Invalid issuer"):
        jwt_verifier.verify_token(token)


def test_verifier_invalid_signature():
    """Verify token signed with wrong secret raises ValueError."""
    token = generate_test_token(secret="wrong-secret-key")
    with pytest.raises(ValueError, match="Invalid token"):
        jwt_verifier.verify_token(token)


def test_verifier_empty_or_none_token():
    """Verify empty or None token raises ValueError."""
    with pytest.raises(ValueError, match="missing or invalid"):
        jwt_verifier.verify_token("")


# =====================================================================
# Integration API Tests for GET /api/v1/auth/me
# =====================================================================


def test_auth_me_no_token_401():
    """GET /api/v1/auth/me without token returns 401 Unauthorized."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_auth_me_malformed_token_401():
    """GET /api/v1/auth/me with malformed bearer token returns 401."""
    headers = {"Authorization": "Bearer not.a.valid.jwt"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_expired_token_401():
    """GET /api/v1/auth/me with expired token returns 401."""
    token = generate_test_token(expires_in=-60)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_invalid_signature_401():
    """GET /api/v1/auth/me with bad signature returns 401."""
    token = generate_test_token(secret="invalid-secret")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_invalid_issuer_401():
    """GET /api/v1/auth/me with bad issuer returns 401."""
    token = generate_test_token(issuer="http://untrusted-idp/realm")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_valid_token_200():
    """GET /api/v1/auth/me with valid Keycloak token returns 200 OK and user details."""
    token = generate_test_token(
        sub="admin01-guid", preferred_username="admin01", roles=["ADMIN"]
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "admin01-guid"
    assert data["username"] == "admin01"
    assert data["roles"] == ["ADMIN"]
    # Ensure sensitive token details are NOT returned
    assert "access_token" not in data
    assert "secret" not in data
