import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.verifier import jwt_verifier
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation."""
    jwt_verifier._signing_key = SECRET_KEY





def test_list_users_unauthenticated():
    res = client.get("/api/v1/users")
    assert res.status_code == 401


def test_list_users_student_forbidden():
    token = generate_test_token(sub="student-1", roles=["STUDENT"])
    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_list_users_admin_success():
    token = generate_test_token(sub="admin-1", roles=["ADMIN"])
    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_user_admin_success():
    token = generate_test_token(sub="admin-1", roles=["ADMIN"])
    payload = {
        "username": "newstaff01",
        "email": "newstaff01@aegisone.local",
        "first_name": "New",
        "last_name": "Staff",
        "role": "STAFF",
    }
    res = client.post("/api/v1/users", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "newstaff01"
    assert "STAFF" in data["roles"]


def test_security_admin_cannot_create_admin():
    token = generate_test_token(sub="secadmin-1", roles=["SECURITY_ADMIN"])
    payload = {
        "username": "rogueadmin",
        "email": "rogueadmin@aegisone.local",
        "role": "ADMIN",
    }
    res = client.post("/api/v1/users", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 403
    assert "privileged role" in res.json()["detail"].lower()


def test_toggle_user_status():
    admin_token = generate_test_token(sub="admin-1", roles=["ADMIN"])
    res = client.post(
        "/api/v1/users/user-staff-1/toggle",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"enabled": False},
    )
    assert res.status_code == 200
    assert "disabled" in res.json()["message"].lower()


def test_reset_user_password():
    admin_token = generate_test_token(sub="admin-1", roles=["ADMIN"])
    res = client.post(
        "/api/v1/users/user-staff-1/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"send_required_action_email": True},
    )
    assert res.status_code == 200
    assert "completed" in res.json()["message"].lower()
