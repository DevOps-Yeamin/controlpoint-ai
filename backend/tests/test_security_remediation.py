import pytest
from backend.app.core.config import settings
from backend.app.models.entities import AuditLog, Agent

ADMIN_HEADERS = {"X-Admin-Key": settings.ADMIN_API_KEY}
HR_KEY = "cp_live_hr_specialist_agent_key_2026"
FINANCE_KEY = "cp_live_finance_analyst_key_2026"

def test_admin_authentication_unauthorized(client):
    """Verify unauthenticated requests to protected admin endpoints return HTTP 401."""
    res = client.post("/api/agents", json={
        "id": "unauth-agent",
        "name": "Attacker Agent",
        "role": "Superuser",
        "rate_limit_per_minute": 60
    })
    assert res.status_code == 401
    assert "Admin authentication required" in res.json()["detail"]

    res_policy = client.post("/api/policies", json={
        "id": "malicious-policy",
        "name": "Malicious Bypass Policy",
        "version": "1.0",
        "target_role": "Guest",
        "target_tool": "*",
        "allowed_operations": ["*"],
        "allowed_fields": ["*"],
        "denied_fields": [],
        "default_action": "ALLOW"
    })
    assert res_policy.status_code == 401

def test_agent_privilege_escalation_forbidden(client):
    """Verify an ordinary agent attempting to invoke administrative endpoints receives HTTP 403."""
    res = client.post(
        "/api/agents",
        json={
            "id": "escalated-agent",
            "name": "Escalated Agent",
            "role": "SuperAdmin",
            "rate_limit_per_minute": 100
        },
        headers={"X-Admin-Key": HR_KEY}  # Agent token used as admin key
    )
    assert res.status_code == 403
    assert "Privilege escalation denied" in res.json()["detail"]

def test_admin_authorized_agent_lifecycle(client):
    """Verify admin key succeeds, and test agent revocation and key rotation."""
    agent_id = "test-lifecycle-agent-99"
    create_res = client.post(
        "/api/agents",
        json={
            "id": agent_id,
            "name": "Lifecycle Test Agent",
            "role": "HR Specialist",
            "rate_limit_per_minute": 50
        },
        headers=ADMIN_HEADERS
    )
    assert create_res.status_code == 200
    agent_data = create_res.json()
    initial_key = agent_data["raw_api_key"]
    assert initial_key is not None

    # Test tool evaluation with new key
    eval_res = client.post("/api/security/evaluate", json={
        "agent_id": agent_id,
        "api_key": initial_key,
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "attendance"]
    })
    assert eval_res.status_code == 200
    assert eval_res.json()["decision"] == "ALLOW"

    # Revoke agent
    revoke_res = client.post(f"/api/agents/{agent_id}/revoke", headers=ADMIN_HEADERS)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["is_active"] is False

    # Evaluation with revoked agent must be denied
    eval_revoked = client.post("/api/security/evaluate", json={
        "agent_id": agent_id,
        "api_key": initial_key,
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    })
    assert eval_revoked.status_code == 200
    assert eval_revoked.json()["decision"] == "DENY"
    assert "revoked" in eval_revoked.json()["reason"].lower()

    # Rotate key (re-activates agent)
    rotate_res = client.post(f"/api/agents/{agent_id}/rotate-key", headers=ADMIN_HEADERS)
    assert rotate_res.status_code == 200
    new_key = rotate_res.json()["new_api_key"]
    assert new_key != initial_key

    # Old key must now fail
    eval_old = client.post("/api/security/evaluate", json={
        "agent_id": agent_id,
        "api_key": initial_key,
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    })
    assert eval_old.json()["decision"] == "DENY"

    # New key must succeed
    eval_new = client.post("/api/security/evaluate", json={
        "agent_id": agent_id,
        "api_key": new_key,
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    })
    assert eval_new.json()["decision"] == "ALLOW"

def test_strict_nlip_authentication_and_identity_binding(client):
    """Verify strict NLIP authentication and identity binding preventing spoofing."""
    nlip_payload = {
        "messagetype": "request",
        "format": "structured",
        "subformat": "tool_invocation",
        "content": {
            "tool_name": "employee_directory",
            "operation": "read",
            "requested_fields": ["name", "salary"],
            "parameters": {}
        }
    }

    # 1. Missing authentication key -> HTTP 401
    res_no_auth = client.post("/api/nlip/process", json=nlip_payload)
    assert res_no_auth.status_code == 401

    # 2. Invalid authentication key -> HTTP 401
    res_bad_auth = client.post(
        "/api/nlip/process",
        json=nlip_payload,
        headers={"X-Agent-Key": "cp_invalid_fake_key_0000"}
    )
    assert res_bad_auth.status_code == 401

    # 3. Valid HR key passed with spoofed query param agent_id="finance-agent-01"
    # Even if query param says finance-agent-01, it must strictly bind to authenticated HR agent!
    # HR requesting name & salary gets REDACT, whereas finance would get ALLOW for salary.
    res_valid = client.post(
        "/api/nlip/process?agent_id=finance-agent-01",
        json=nlip_payload,
        headers={"X-Agent-Key": HR_KEY}
    )
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["messagetype"] == "response"
    # Under HR policy, salary is unauthorized and redacted
    assert data["content"]["decision"] == "REDACT"
    assert data["content"]["audit_hash"] is not None

def test_audit_log_hash_chain_tamper_detection(client, db_session):
    """Verify that tampering with any audit log entry invalidates the SHA-256 chain."""
    # First, generate a clean audit record
    client.post("/api/security/execute", json={
        "agent_id": "hr-agent-01",
        "api_key": HR_KEY,
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "attendance"]
    })

    # Verify initial chain integrity
    res_clean = client.get("/api/audit-logs/verify-chain", headers=ADMIN_HEADERS)
    assert res_clean.status_code == 200
    assert res_clean.json()["is_valid"] is True

    # Intentionally corrupt the latest audit record in the database
    latest_entry = db_session.query(AuditLog).order_by(AuditLog.sequence_number.desc()).first()
    assert latest_entry is not None
    original_decision = latest_entry.decision
    latest_entry.decision = "TAMPERED_DECISION"
    db_session.commit()

    # Chain verification must now detect tamper
    res_tampered = client.get("/api/audit-logs/verify-chain", headers=ADMIN_HEADERS)
    assert res_tampered.status_code == 200
    tamper_data = res_tampered.json()
    assert tamper_data["is_valid"] is False
    assert tamper_data["broken_sequence"] == latest_entry.sequence_number
    assert "Tampering detected" in tamper_data["error_message"]

    # Restore original decision for test cleanliness
    latest_entry.decision = original_decision
    db_session.commit()

def test_security_headers_and_payload_limit(client):
    """Verify security headers are attached and excessive payloads rejected."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert "strict-origin" in res.headers.get("referrer-policy")
    assert res.headers.get("permissions-policy") is not None

    # Oversized payload (> 5MB)
    huge_data = "x" * (5 * 1024 * 1024 + 1024)
    res_huge = client.post(
        "/api/security/evaluate",
        content=huge_data,
        headers={"Content-Type": "application/json"}
    )
    assert res_huge.status_code == 413
