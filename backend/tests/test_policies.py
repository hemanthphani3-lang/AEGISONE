from fastapi.testclient import TestClient
from app.auth.verifier import jwt_verifier
from app.main import app
from tests.test_auth import SECRET_KEY, generate_test_token

client = TestClient(app)


def setup_module():
    """Configure static signing key for test token generation."""
    jwt_verifier._signing_key = SECRET_KEY


def test_policies_unauthenticated_401():
    """Verify unauthenticated calls to policies endpoints return 401 Unauthorized."""
    assert client.get("/api/v1/policies").status_code == 401
    assert client.get("/api/v1/policies/admin-mfa").status_code == 401
    assert client.post("/api/v1/policies", json={}).status_code == 401
    assert client.patch("/api/v1/policies/admin-mfa", json={}).status_code == 401
    assert client.delete("/api/v1/policies/admin-mfa").status_code == 401


def test_student_policy_crud_permissions():
    """Verify STUDENT is denied policy viewing, creation, update, and deletion (403)."""
    token = generate_test_token(sub="student-sub", roles=["STUDENT"])
    headers = {"Authorization": f"Bearer {token}"}

    # GET denied for STUDENT (lacks READ_POLICY permission)
    assert client.get("/api/v1/policies", headers=headers).status_code == 403
    assert client.get("/api/v1/policies/admin-mfa", headers=headers).status_code == 403

    # Write operations forbidden
    create_resp = client.post(
        "/api/v1/policies",
        headers=headers,
        json={"id": "st-p", "name": "N", "description": "D", "action": "BLOCK"},
    )
    assert create_resp.status_code == 403

    patch_resp = client.patch(
        "/api/v1/policies/admin-mfa", headers=headers, json={"name": "X"}
    )
    assert patch_resp.status_code == 403

    del_resp = client.delete("/api/v1/policies/admin-mfa", headers=headers)
    assert del_resp.status_code == 403


def test_staff_policy_crud_permissions():
    """Verify STAFF can view policies but is denied creation/update/deletion (403)."""
    token = generate_test_token(sub="staff-sub", roles=["STAFF"])
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/policies", headers=headers).status_code == 200
    assert client.post("/api/v1/policies", headers=headers, json={}).status_code == 403


def test_break_glass_alone_policy_crud_permissions():
    """Verify BREAK_GLASS alone can view policies but is denied policy write operations (403)."""
    token = generate_test_token(sub="bg-sub", roles=["BREAK_GLASS"])
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/policies", headers=headers).status_code == 200
    assert client.post("/api/v1/policies", headers=headers, json={}).status_code == 403


def test_admin_full_policy_crud_and_conflict():
    """Verify ADMIN has full CRUD access, and duplicate ID returns 409 Conflict."""
    token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}

    # Pre-cleanup in case of leftover from previous test run
    client.delete("/api/v1/policies/admin-created-p1", headers=headers)

    # 1. Create policy
    create_payload = {
        "id": "admin-created-p1",
        "name": "Admin Created Policy",
        "description": "Created by ADMIN",
        "enabled": True,
        "target_roles": ["STUDENT"],
        "action": "BLOCK",
    }
    resp1 = client.post("/api/v1/policies", headers=headers, json=create_payload)
    assert resp1.status_code == 201
    assert resp1.json()["id"] == "admin-created-p1"

    # 2. Duplicate creation returns 409 Conflict
    resp_dup = client.post("/api/v1/policies", headers=headers, json=create_payload)
    assert resp_dup.status_code == 409

    # 3. Patch policy (true partial update)
    patch_payload = {"enabled": False}
    resp_patch = client.patch(
        "/api/v1/policies/admin-created-p1", headers=headers, json=patch_payload
    )
    assert resp_patch.status_code == 200
    data = resp_patch.json()
    assert data["enabled"] is False
    assert data["name"] == "Admin Created Policy"  # Unmodified field preserved!

    # 4. Delete policy
    resp_del = client.delete("/api/v1/policies/admin-created-p1", headers=headers)
    assert resp_del.status_code == 200

    # 5. Non-existent policy returns 404
    assert client.get("/api/v1/policies/admin-created-p1", headers=headers).status_code == 404


def test_security_admin_full_policy_crud():
    """Verify SECURITY_ADMIN has full CRUD access."""
    token = generate_test_token(sub="secadmin-sub", roles=["SECURITY_ADMIN"])
    headers = {"Authorization": f"Bearer {token}"}

    # Pre-cleanup
    client.delete("/api/v1/policies/secadmin-p1", headers=headers)

    create_payload = {
        "id": "secadmin-p1",
        "name": "SecAdmin Policy",
        "description": "Created by SECURITY_ADMIN",
        "action": "MFA_REQUIRED",
    }
    assert client.post("/api/v1/policies", headers=headers, json=create_payload).status_code == 201
    assert client.delete("/api/v1/policies/secadmin-p1", headers=headers).status_code == 200


def test_enable_disable_policy_evaluation_flow():
    """Test creating policy -> evaluating (matches) -> disabling -> evaluating (ignored)."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    student_token = generate_test_token(sub="student-sub", roles=["STUDENT"])
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Clean up pre-existing test policy if present
    client.delete("/api/v1/policies/block-student-flow", headers=admin_headers)

    # 1. Create policy blocking STUDENT
    create_payload = {
        "id": "block-student-flow",
        "name": "Block Student Flow",
        "description": "Temporary student block",
        "enabled": True,
        "target_roles": ["STUDENT"],
        "action": "BLOCK",
    }
    assert client.post("/api/v1/policies", headers=admin_headers, json=create_payload).status_code == 201

    # 2. Evaluate student -> BLOCK
    eval_resp1 = client.post("/api/v1/evaluate/me", headers=student_headers, json={"auth_protocol": "OAUTH2"})
    assert eval_resp1.status_code == 200
    assert eval_resp1.json()["decision"] == "BLOCK"
    assert "block-student-flow" in eval_resp1.json()["matched_policies"]

    # 3. Disable policy via PATCH
    assert client.patch(
        "/api/v1/policies/block-student-flow",
        headers=admin_headers,
        json={"enabled": False},
    ).status_code == 200

    # 4. Evaluate student again -> ALLOW (Disabled policy ignored!)
    eval_resp2 = client.post("/api/v1/evaluate/me", headers=student_headers, json={"auth_protocol": "OAUTH2"})
    assert eval_resp2.status_code == 200
    assert eval_resp2.json()["decision"] == "ALLOW"
    assert "block-student-flow" not in eval_resp2.json()["matched_policies"]

    # Clean up
    client.delete("/api/v1/policies/block-student-flow", headers=admin_headers)


def test_policy_validation_endpoint():
    """Verify POST /api/v1/policies/validate performs server-side safety checks."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    staff_token = generate_test_token(sub="staff-sub", roles=["STAFF"])
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 1. Staff denied 403
    assert client.post("/api/v1/policies/validate", headers=staff_headers, json={}).status_code == 403

    # 2. Valid payload check
    valid_payload = {
        "id": "valid-p1",
        "name": "Valid Policy",
        "description": "Valid description",
        "action": "MFA_REQUIRED",
        "target_roles": ["STAFF"],
    }
    resp1 = client.post("/api/v1/policies/validate", headers=admin_headers, json=valid_payload)
    assert resp1.status_code == 200
    assert resp1.json()["valid"] is True
    assert len(resp1.json()["errors"]) == 0

    # 3. Invalid payload check (conflict: role both targeted and excluded)
    invalid_payload = {
        "id": "invalid-p1",
        "name": "Invalid Policy",
        "description": "Invalid description",
        "action": "BLOCK",
        "target_roles": ["ADMIN"],
        "exclusions": ["ADMIN"],
    }
    resp2 = client.post("/api/v1/policies/validate", headers=admin_headers, json=invalid_payload)
    assert resp2.status_code == 200
    assert resp2.json()["valid"] is False
    assert any("cannot be both targeted and excluded" in err for err in resp2.json()["errors"])

    # 4. Empty target scope warning check
    empty_scope_payload = {
        "id": "empty-scope-p1",
        "name": "Empty Scope Policy",
        "description": "Description",
        "action": "MFA_REQUIRED",
    }
    resp3 = client.post("/api/v1/policies/validate", headers=admin_headers, json=empty_scope_payload)
    assert resp3.status_code == 200
    assert resp3.json()["valid"] is True
    assert any("empty target scope" in w for w in resp3.json()["warnings"])


def test_policy_versioning_and_audit():
    """Verify policy version increments sequentially on updates."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Pre-cleanup
    client.delete("/api/v1/policies/version-test-p1", headers=admin_headers)

    # 1. Create policy -> version 1
    create_payload = {
        "id": "version-test-p1",
        "name": "Version Test Policy",
        "description": "Initial creation",
        "action": "MFA_REQUIRED",
        "target_roles": ["STAFF"],
    }
    create_resp = client.post("/api/v1/policies", headers=admin_headers, json=create_payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["version"] == 1

    # 2. Update policy -> version 2
    patch_resp1 = client.patch(
        "/api/v1/policies/version-test-p1",
        headers=admin_headers,
        json={"name": "Version Test Policy Updated"},
    )
    assert patch_resp1.status_code == 200
    assert patch_resp1.json()["version"] == 2

    # 3. Update policy again -> version 3
    patch_resp2 = client.patch(
        "/api/v1/policies/version-test-p1",
        headers=admin_headers,
        json={"enabled": False},
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["version"] == 3

    # Cleanup
    client.delete("/api/v1/policies/version-test-p1", headers=admin_headers)


def test_policy_optimistic_concurrency_conflict():
    """Verify 409 Conflict is returned when attempting to update with an outdated expected_version."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Pre-cleanup
    client.delete("/api/v1/policies/occ-test-p1", headers=admin_headers)

    # 1. Create policy -> version 1
    create_payload = {
        "id": "occ-test-p1",
        "name": "OCC Test Policy",
        "description": "Initial policy",
        "action": "BLOCK",
        "target_roles": ["STUDENT"],
    }
    res_create = client.post("/api/v1/policies", headers=admin_headers, json=create_payload)
    assert res_create.status_code == 201
    assert res_create.json()["version"] == 1

    # 2. Admin A updates policy with expected_version = 1 -> succeeds, version becomes 2
    res_admin_a = client.patch(
        "/api/v1/policies/occ-test-p1",
        headers=admin_headers,
        json={"name": "OCC Policy Updated by Admin A", "expected_version": 1},
    )
    assert res_admin_a.status_code == 200
    assert res_admin_a.json()["version"] == 2

    # 3. Admin B attempts update using outdated expected_version = 1 -> returns 409 Conflict
    res_admin_b_conflict = client.patch(
        "/api/v1/policies/occ-test-p1",
        headers=admin_headers,
        json={"name": "OCC Policy Overwrite Attempt by Admin B", "expected_version": 1},
    )
    assert res_admin_b_conflict.status_code == 409
    err_detail = res_admin_b_conflict.json()["detail"]
    assert err_detail["code"] == "POLICY_CONCURRENCY_CONFLICT"
    assert err_detail["expected_version"] == 1
    assert err_detail["current_version"] == 2

    # 4. Admin B refreshes, uses expected_version = 2 -> succeeds, version becomes 3
    res_admin_b_retry = client.patch(
        "/api/v1/policies/occ-test-p1",
        headers=admin_headers,
        json={"name": "OCC Policy Updated by Admin B after Refresh", "expected_version": 2},
    )
    assert res_admin_b_retry.status_code == 200
    assert res_admin_b_retry.json()["version"] == 3

    # Cleanup
    client.delete("/api/v1/policies/occ-test-p1", headers=admin_headers)


def test_policy_version_history_and_detail():
    """Verify version snapshots are recorded and queryable via history APIs."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    client.delete("/api/v1/policies/hist-test-p1", headers=admin_headers)

    # 1. Create policy (v1)
    c_res = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={"id": "hist-test-p1", "name": "History Test Policy", "description": "Initial", "action": "BLOCK"},
    )
    assert c_res.status_code == 201

    # 2. Update policy (v2)
    u_res = client.patch(
        "/api/v1/policies/hist-test-p1",
        headers=admin_headers,
        json={"name": "History Test Policy v2", "expected_version": 1},
    )
    assert u_res.status_code == 200

    # 3. Get version history list
    v_list = client.get("/api/v1/policies/hist-test-p1/versions", headers=admin_headers)
    assert v_list.status_code == 200
    versions = v_list.json()["versions"]
    assert len(versions) >= 2
    assert versions[0]["version"] == 2
    assert versions[1]["version"] == 1

    # 4. Get detail of version 1
    v1_detail = client.get("/api/v1/policies/hist-test-p1/versions/1", headers=admin_headers)
    assert v1_detail.status_code == 200
    assert v1_detail.json()["snapshot"]["name"] == "History Test Policy"

    client.delete("/api/v1/policies/hist-test-p1", headers=admin_headers)


def test_policy_version_diff():
    """Verify policy diff calculates field-level differences between versions."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    client.delete("/api/v1/policies/diff-test-p1", headers=admin_headers)

    client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={"id": "diff-test-p1", "name": "Diff Test v1", "description": "Desc v1", "action": "BLOCK", "target_roles": ["STUDENT"]},
    )
    client.patch(
        "/api/v1/policies/diff-test-p1",
        headers=admin_headers,
        json={"name": "Diff Test v2", "action": "MFA_REQUIRED", "target_roles": ["STUDENT", "STAFF"], "expected_version": 1},
    )

    diff_res = client.get("/api/v1/policies/diff-test-p1/versions/1/diff?against_version=2", headers=admin_headers)
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert "name" in diff_data["changed_fields"]
    assert diff_data["field_diffs"]["name"]["previous"] == "Diff Test v1"
    assert diff_data["field_diffs"]["name"]["new"] == "Diff Test v2"
    assert "STAFF" in diff_data["added_collection_items"]["target_roles"]

    client.delete("/api/v1/policies/diff-test-p1", headers=admin_headers)


def test_policy_rollback_flow_and_concurrency():
    """Verify policy rollback restores historical definition as a brand new current version."""
    admin_token = generate_test_token(sub="admin-sub", roles=["ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    client.delete("/api/v1/policies/rollback-test-p1", headers=admin_headers)

    # v1: action = BLOCK
    client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={"id": "rollback-test-p1", "name": "Original v1", "description": "Desc", "action": "BLOCK"},
    )
    # v2: action = MFA_REQUIRED
    client.patch(
        "/api/v1/policies/rollback-test-p1",
        headers=admin_headers,
        json={"action": "MFA_REQUIRED", "expected_version": 1},
    )

    # Rollback OCC conflict check (expected_current_version = 1 vs actual 2) -> 409
    rb_conflict = client.post(
        "/api/v1/policies/rollback-test-p1/rollback",
        headers=admin_headers,
        json={"target_version": 1, "expected_current_version": 1},
    )
    assert rb_conflict.status_code == 409

    # Successful Rollback to v1 (expected_current_version = 2) -> creates v3
    rb_res = client.post(
        "/api/v1/policies/rollback-test-p1/rollback",
        headers=admin_headers,
        json={"target_version": 1, "expected_current_version": 2},
    )
    assert rb_res.status_code == 200
    rb_data = rb_res.json()
    assert rb_data["version"] == 3
    assert rb_data["action"] == "BLOCK"
    assert rb_data["name"] == "Original v1"

    # Verify history list has 3 entries: v3 (ROLLBACK), v2 (UPDATE), v1 (CREATE)
    v_list = client.get("/api/v1/policies/rollback-test-p1/versions", headers=admin_headers)
    assert v_list.status_code == 200
    summaries = v_list.json()["versions"]
    assert len(summaries) >= 3
    assert summaries[0]["version"] == 3
    assert summaries[0]["change_type"] == "ROLLBACK"

    client.delete("/api/v1/policies/rollback-test-p1", headers=admin_headers)


def test_policy_history_and_rollback_permissions():
    """Verify authorization checks on history and rollback endpoints."""
    staff_token = generate_test_token(sub="staff-sub", roles=["STAFF"])
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    student_token = generate_test_token(sub="student-sub", roles=["STUDENT"])
    student_headers = {"Authorization": f"Bearer {student_token}"}

    secadmin_token = generate_test_token(sub="secadmin-sub", roles=["SECURITY_ADMIN"])
    secadmin_headers = {"Authorization": f"Bearer {secadmin_token}"}

    client.delete("/api/v1/policies/perm-test-p1", headers=secadmin_headers)
    client.post(
        "/api/v1/policies",
        headers=secadmin_headers,
        json={"id": "perm-test-p1", "name": "Perm Policy", "description": "Desc", "action": "ALLOW"},
    )

    # 1. STAFF can read versions
    assert client.get("/api/v1/policies/perm-test-p1/versions", headers=staff_headers).status_code == 200

    # 2. STAFF forbidden from rollback (lacks WRITE_POLICY)
    rb_staff = client.post(
        "/api/v1/policies/perm-test-p1/rollback",
        headers=staff_headers,
        json={"target_version": 1},
    )
    assert rb_staff.status_code == 403

    # 3. STUDENT forbidden from reading versions (lacks READ_POLICY)
    assert client.get("/api/v1/policies/perm-test-p1/versions", headers=student_headers).status_code == 403

    # 4. SECURITY_ADMIN allowed rollback
    client.patch("/api/v1/policies/perm-test-p1", headers=secadmin_headers, json={"action": "BLOCK"})
    rb_sec = client.post(
        "/api/v1/policies/perm-test-p1/rollback",
        headers=secadmin_headers,
        json={"target_version": 1, "expected_current_version": 2},
    )
    assert rb_sec.status_code == 200

    client.delete("/api/v1/policies/perm-test-p1", headers=secadmin_headers)



