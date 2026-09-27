import json
import time
import urllib.error
import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.mfa.service import OTPService, otp_service
from app.email.resend_service import resend_service
from app.auth.verifier import jwt_verifier
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation."""
    jwt_verifier._signing_key = SECRET_KEY


def test_otp_service_generate_and_verify():
    srv = OTPService(ttl_seconds=300, cooldown_seconds=60, max_attempts=5)
    user_id = "test-user-mfa-1"

    # Generate OTP
    code, can_send, cooldown, msg = srv.generate_otp(user_id)
    assert can_send is True
    assert len(code) == 6
    assert code.isdigit()

    # Cooldown enforcement
    code2, can_send2, cooldown2, msg2 = srv.generate_otp(user_id)
    assert can_send2 is False
    assert cooldown2 > 0

    # Wrong OTP code attempt
    ok, err_msg = srv.verify_otp(user_id, "000000" if code != "000000" else "111111")
    assert ok is False
    assert "remaining" in err_msg.lower()

    # Valid OTP code attempt
    ok, ok_msg = srv.verify_otp(user_id, code)
    assert ok is True
    assert "verified" in ok_msg.lower()

    # Reused OTP code attempt -> Should fail
    ok_again, _ = srv.verify_otp(user_id, code)
    assert ok_again is False


def test_mfa_endpoints_flow(monkeypatch):
    """Verify full MFA endpoint flow with mocked Resend delivery and upgraded JWT token."""
    # Mock Resend API success
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key_mfa_endpoint")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    user_id = "mfa-user-endpoint-test"
    token = generate_test_token(sub=user_id, preferred_username="mfauser", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}

    with patch("urllib.request.urlopen", return_value=mock_resp):
        # 1. Send OTP
        res_send = client.post("/api/v1/auth/mfa/send-otp", headers=headers, json={})
        assert res_send.status_code == 200
        data_send = res_send.json()
        assert data_send["success"] is True

        # 2. Retrieve active generated OTP code from service store (to bypass 60s resend cooldown)
        record = otp_service._store.get(user_id)
        assert record is not None

        # Test wrong code first
        res_wrong = client.post("/api/v1/auth/mfa/verify-otp", headers=headers, json={"otp_code": "000000"})
        assert res_wrong.status_code == 400

        # 3. Regenerate single OTP for verification test
        otp_service._store.pop(user_id, None)
        code, can_send, _, _ = otp_service.generate_otp(user_id)
        assert can_send is True

        # Verify with correct code
        res_verify = client.post("/api/v1/auth/mfa/verify-otp", headers=headers, json={"otp_code": code})
        assert res_verify.status_code == 200
        data_verify = res_verify.json()
        assert data_verify["success"] is True
        assert data_verify["mfa_completed"] is True
        assert "access_token" in data_verify


def test_resend_configuration_missing_key(monkeypatch):
    """Verify missing Resend API key returns UNAVAILABLE status without crashing."""
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    success, status, msg = resend_service.send_email(
        to_email="test@aegisone.local",
        subject="Test",
        html="<p>Test</p>",
        text="Test",
    )
    assert success is False
    assert status == "UNAVAILABLE"
    assert "currently unavailable" in msg.lower()


def test_resend_delivery_success(monkeypatch):
    """Verify Resend HTTP request construction and successful delivery handling."""
    monkeypatch.setenv("RESEND_API_KEY", "re_mock_test_key_12345")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    captured_req = None

    def fake_urlopen(req, timeout=10):
        nonlocal captured_req
        captured_req = req
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        success, status, msg = resend_service.send_email(
            to_email="user@aegisone.dev",
            subject="AegisOne — Your MFA Verification Code",
            html="<p>123456</p>",
            text="Your code is: 123456",
        )

    assert success is True
    assert status == "DELIVERED"
    assert captured_req is not None
    assert captured_req.full_url == "https://api.resend.com/emails"
    assert captured_req.headers["Authorization"] == "Bearer re_mock_test_key_12345"
    assert captured_req.headers["Content-type"] == "application/json"

    body_json = json.loads(captured_req.data.decode("utf-8"))
    assert body_json["to"] == ["user@aegisone.dev"]
    assert body_json["from"] == "onboarding@resend.dev"
    assert body_json["subject"] == "AegisOne — Your MFA Verification Code"


def test_resend_error_sanitization(monkeypatch, caplog):
    """Verify secrets (API key, Auth header, plaintext OTP) are never logged on Resend API errors."""
    secret_key = "re_super_secret_resend_key_9999"
    monkeypatch.setenv("RESEND_API_KEY", secret_key)
    monkeypatch.setenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    http_err = urllib.error.HTTPError(
        url="https://api.resend.com/emails",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b'{"message":"Invalid API Key"}'),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        success, status, msg = resend_service.send_email(
            to_email="user@aegisone.dev",
            subject="AegisOne — Your MFA Verification Code",
            html="<p>987654</p>",
            text="Your code is: 987654",
        )

    assert success is False
    assert status == "ERROR"
    assert "currently unavailable" in msg.lower()

    # Strict secret leak audit on logs and error response
    log_text = caplog.text
    assert secret_key not in log_text
    assert secret_key not in msg
    assert "Authorization" not in log_text
    assert "987654" not in log_text
