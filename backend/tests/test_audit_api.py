from fastapi.testclient import TestClient
from app.audit.repository import audit_repository
from app.auth.verifier import jwt_verifier
from app.main import app
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation."""
    jwt_verifier._signing_key = SECRET_KEY


def test_audit_api_permissions():
    """Verify role-based permissions for GET /api/v1/audit/events."""
    # 1. Unauthenticated -> 401
    assert client.get("/api/v1/audit/events").status_code == 401

    # 2. STUDENT -> 403
    student_token = generate_test_token(sub="student-1", roles=["STUDENT"])
    assert (
        client.get(
            "/api/v1/audit/events",
            headers={"Authorization": f"Bearer {student_token}"},
        ).status_code
        == 403
    )

    # 3. STAFF -> 403
    staff_token = generate_test_token(sub="staff-1", roles=["STAFF"])
    assert (
        client.get(
            "/api/v1/audit/events",
            headers={"Authorization": f"Bearer {staff_token}"},
        ).status_code
        == 403
    )

    # 4. BREAK_GLASS -> 403
    bg_token = generate_test_token(sub="bg-1", roles=["BREAK_GLASS"])
    assert (
        client.get(
            "/api/v1/audit/events",
            headers={"Authorization": f"Bearer {bg_token}"},
        ).status_code
        == 403
    )

    # 5. ADMIN -> 200
    admin_token = generate_test_token(sub="admin-1", roles=["ADMIN"])
    resp_admin = client.get(
        "/api/v1/audit/events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200
    assert "events" in resp_admin.json()

    # 6. SECURITY_ADMIN -> 200
    sec_token = generate_test_token(sub="sec-1", roles=["SECURITY_ADMIN"])
    resp_sec = client.get(
        "/api/v1/audit/events",
        headers={"Authorization": f"Bearer {sec_token}"},
    )
    assert resp_sec.status_code == 200


def test_correlation_id_header_propagation():
    """Verify X-Correlation-ID is extracted/generated and returned in response headers."""
    # Test generated correlation ID
    resp1 = client.get("/api/v1/health")
    assert "X-Correlation-ID" in resp1.headers

    # Test custom valid correlation ID propagation
    custom_cid = "custom-test-correlation-id-999"
    resp2 = client.get(
        "/api/v1/health", headers={"X-Correlation-ID": custom_cid}
    )
    assert resp2.headers.get("X-Correlation-ID") == custom_cid


def test_authorization_denied_audit_logging():
    """Verify STAFF attempting policy creation generates AUTHORIZATION_DENIED audit event."""
    staff_token = generate_test_token(sub="staff-denied-user", roles=["STAFF"])
    resp = client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"id": "denied-p", "name": "N", "description": "D", "action": "BLOCK"},
    )
    assert resp.status_code == 403

    # Verify event recorded
    admin_token = generate_test_token(sub="admin-auditor", roles=["ADMIN"])
    audit_resp = client.get(
        "/api/v1/audit/events?event_type=AUTHORIZATION_DENIED",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == 200
    events = audit_resp.json()["events"]
    assert any(e["actor_user_id"] == "staff-denied-user" for e in events)


def test_policy_mutation_audit_events():
    """Verify policy create, enable, disable, update, delete record appropriate audit events."""
    admin_token = generate_test_token(sub="admin-mutator", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}

    policy_id = "audit-mutation-p1"
    # Pre-cleanup in case of leftover record
    client.delete(f"/api/v1/policies/{policy_id}", headers=headers)

    # 1. Create policy -> POLICY_CREATED
    create_payload = {
        "id": policy_id,
        "name": "Mutation Test Policy",
        "description": "Audited policy",
        "enabled": True,
        "action": "MFA_REQUIRED",
    }
    assert client.post("/api/v1/policies", headers=headers, json=create_payload).status_code == 201

    # 2. Disable policy -> POLICY_DISABLED
    assert client.patch(
        f"/api/v1/policies/{policy_id}", headers=headers, json={"enabled": False}
    ).status_code == 200

    # 3. Enable policy -> POLICY_ENABLED
    assert client.patch(
        f"/api/v1/policies/{policy_id}", headers=headers, json={"enabled": True}
    ).status_code == 200

    # 4. Update policy name -> POLICY_UPDATED
    assert client.patch(
        f"/api/v1/policies/{policy_id}",
        headers=headers,
        json={"name": "New Name", "expected_version": 1},
    ).status_code == 200

    # 5. Delete policy -> POLICY_DELETED
    assert client.delete(f"/api/v1/policies/{policy_id}", headers=headers).status_code == 200


    # Query audit events
    audit_resp = client.get(
        f"/api/v1/audit/events?resource_id={policy_id}",
        headers=headers,
    )
    assert audit_resp.status_code == 200
    event_types = [e["event_type"] for e in audit_resp.json()["events"]]

    assert "POLICY_CREATED" in event_types
    assert "POLICY_DISABLED" in event_types
    assert "POLICY_ENABLED" in event_types
    assert "POLICY_UPDATED" in event_types
    assert "POLICY_DELETED" in event_types


def test_policy_decision_traces():
    """Verify decision traces for BLOCK, MFA_REQUIRED, ALLOW, and BREAK_GLASS exclusion."""
    admin_token = generate_test_token(sub="admin-eval-user", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Pre-cleanup non-default policies
    resp_list = client.get("/api/v1/policies", headers=admin_headers)
    if resp_list.status_code == 200:
        default_ids = {"admin-mfa", "block-legacy-auth"}
        for policy in resp_list.json().get("policies", []):
            if policy["id"] not in default_ids:
                client.delete(f"/api/v1/policies/{policy['id']}", headers=admin_headers)

    # 1. Admin without MFA -> MFA_REQUIRED trace
    resp_mfa = client.post("/api/v1/evaluate/me", headers=admin_headers)
    assert resp_mfa.status_code == 200
    mfa_json = resp_mfa.json()
    assert mfa_json["decision"] == "MFA_REQUIRED"
    assert "admin-mfa" in mfa_json["matched_policies"]

    # 2. Legacy protocol -> BLOCK trace
    legacy_context = {
        "user_id": "legacy-user-1",
        "role": "STUDENT",
        "roles": ["STUDENT"],
        "location": "UNKNOWN",
        "device": {},
        "authentication": {"protocol": "LEGACY", "mfa_completed": False},
    }
    legacy_resp = client.post("/api/v1/evaluate", json=legacy_context, headers=admin_headers)
    assert legacy_resp.status_code == 200
    legacy_json = legacy_resp.json()
    assert legacy_json["decision"] == "BLOCK"
    assert "block-legacy-auth" in legacy_json["matched_policies"]



    # 3. Student without restrictive policy -> ALLOW trace
    student_token = generate_test_token(sub="student-eval-user", roles=["STUDENT"])
    student_resp = client.post(
        "/api/v1/evaluate/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_resp.status_code == 200
    student_json = student_resp.json()
    assert student_json["decision"] == "ALLOW"
    assert "No matching restrictive policy" in student_json["reasons"][0]

    # 4. BREAK_GLASS user excluded from admin-mfa -> ALLOW
    bg_token = generate_test_token(sub="bg-eval-user", roles=["BREAK_GLASS", "ADMIN"])
    bg_resp = client.post(
        "/api/v1/evaluate/me",
        headers={"Authorization": f"Bearer {bg_token}"},
    )
    assert bg_resp.status_code == 200
    assert bg_resp.json()["decision"] == "ALLOW"



def test_audit_pagination_and_filtering():
    """Verify limit, offset, page, page_size, and query filtering for GET /api/v1/audit/events."""
    admin_token = generate_test_token(sub="admin-paginator", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test limit and offset
    resp = client.get(
        "/api/v1/audit/events?limit=5&offset=0",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["events"]) <= 5
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert "total" in data

    # Test page and page_size
    resp_page = client.get(
        "/api/v1/audit/events?page=1&page_size=10",
        headers=headers,
    )
    assert resp_page.status_code == 200
    data_page = resp_page.json()
    assert data_page["page"] == 1
    assert data_page["page_size"] == 10
    assert "items" in data_page


def test_audit_security_sanitization_no_secrets_exposed():
    """Verify secrets, tokens, passwords, and authorization headers are redacted in metadata."""
    from app.audit.service import sanitize_metadata

    raw_meta = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret",
        "refresh_token": "ref_12345",
        "password": "SuperSecretPassword123",
        "client_secret": "cs_99999",
        "authorization": "Bearer eyJhbG...",
        "cookie": "AUTH_SESSION_ID=xyz",
        "normal_key": "safe_value",
        "nested": {
            "jwt": "eyJhbG...",
            "safe_nested": 42,
        },
    }

    clean_meta = sanitize_metadata(raw_meta)

    assert clean_meta["access_token"] == "[REDACTED]"
    assert clean_meta["refresh_token"] == "[REDACTED]"
    assert clean_meta["password"] == "[REDACTED]"
    assert clean_meta["client_secret"] == "[REDACTED]"
    assert clean_meta["authorization"] == "[REDACTED]"
    assert clean_meta["cookie"] == "[REDACTED]"
    assert clean_meta["normal_key"] == "safe_value"
    assert clean_meta["nested"]["jwt"] == "[REDACTED]"
    assert clean_meta["nested"]["safe_nested"] == 42

