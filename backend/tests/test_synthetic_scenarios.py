import pytest

def test_scenario_1_hr_requests_name_and_attendance(client):
    """Scenario 1: HR requests name and attendance -> ALLOW."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "attendance"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    assert data["allowed"] is True
    # Verify data returned
    assert len(data["enforced_data"]) > 0
    assert "name" in data["enforced_data"][0]
    assert "attendance" in data["enforced_data"][0]

def test_scenario_2_hr_requests_salary(client):
    """Scenario 2: HR requests salary -> DENY."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["salary"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert data["allowed"] is False
    assert data["enforced_data"] is None

def test_scenario_3_hr_requests_name_and_salary(client):
    """Scenario 3: HR requests name and salary -> REDACT salary."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "salary"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REDACT"
    assert data["allowed"] is True
    assert "salary" in data["redacted_fields"]
    # Check that salary in output is redacted string
    first_record = data["enforced_data"][0]
    assert first_record["name"] is not None
    assert first_record["salary"] == "[REDACTED: SENSITIVE_FIELD]"

def test_scenario_4_guest_requests_national_id(client):
    """Scenario 4: Guest requests national_id -> DENY."""
    payload = {
        "agent_id": "guest-agent-01",
        "api_key": "cp_live_guest_external_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["national_id"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert data["allowed"] is False
    assert data["enforced_data"] is None

def test_scenario_5_finance_requests_salary(client):
    """Scenario 5: Finance requests salary -> ALLOW."""
    payload = {
        "agent_id": "finance-agent-01",
        "api_key": "cp_live_finance_analyst_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["salary"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    assert data["allowed"] is True
    first_record = data["enforced_data"][0]
    assert isinstance(first_record["salary"], (int, float))

def test_scenario_6_invalid_identity(client):
    """Scenario 6: Invalid identity -> DENY."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_invalid_forged_key_0000",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert data["allowed"] is False
    assert "Identity Verification Failed" in data["reason"]

def test_scenario_7_rate_limit_exceeded(client):
    """Scenario 7: Rate limit exceeded -> THROTTLE."""
    # Guest has rate limit of 5 requests/min
    for _ in range(5):
        client.post("/api/security/execute", json={
            "agent_id": "guest-agent-01",
            "api_key": "cp_live_guest_external_agent_key_2026",
            "tool_name": "employee_directory",
            "operation": "read",
            "requested_fields": ["name"]
        })

    # 6th request triggers throttle
    res = client.post("/api/security/execute", json={
        "agent_id": "guest-agent-01",
        "api_key": "cp_live_guest_external_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "THROTTLE"
    assert data["allowed"] is False
    assert "Throttled" in data["reason"]

def test_scenario_8_tool_leak_response_inspection(client):
    """Scenario 8: Tool returns unauthorized sensitive data -> REDACT before returning."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"],
        "parameters": {"department": "Engineering", "force_leak": True}
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REDACT"
    first_record = data["enforced_data"][0]
    assert first_record["name"] is not None
    # Check that salary and national_id were redacted by outbound inspector
    assert first_record.get("salary") == "[REDACTED: SENSITIVE_FIELD]"
    assert first_record.get("national_id") == "[REDACTED: SENSITIVE_FIELD]"

def test_scenario_9_malformed_arguments_denied(client):
    """Scenario 9: Malformed arguments with injection patterns -> DENY."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"],
        "parameters": {"department": "Engineering'; DROP TABLE synthetic_employees; --"}
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert data["allowed"] is False
    assert "Argument Validation Failed" in data["reason"]

def test_scenario_10_unknown_tool_denied(client):
    """Scenario 10: Unknown / unregistered tool call -> DENY."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "unregistered_shell_tool",
        "operation": "read",
        "requested_fields": ["command"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert data["allowed"] is False
    assert "Tool Identification Failed" in data["reason"]

def test_scenario_11_policy_conflict_resolution(client):
    """Scenario 11: Policy conflict resolved via most-restrictive rule -> REDACT."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "salary"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REDACT"
    assert "salary" in data["redacted_fields"]

def test_scenario_12_unauthorized_privilege_escalation(client):
    """Scenario 12: Unauthorized mutation operation attempt -> DENY."""
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "delete",
        "requested_fields": ["employee_id"]
    }
    res = client.post("/api/security/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert data["allowed"] is False
    assert "not authorized" in data["reason"]

def test_scenario_13_repeated_unauthorized_requests(client):
    """Scenario 13: Repeated unauthorized requests trigger progressive throttling -> THROTTLE."""
    from backend.app.engine.rate_limiter import rate_limiter
    rate_limiter.reset()

    # Trigger 3 unauthorized requests
    for _ in range(3):
        client.post("/api/security/execute", json={
            "agent_id": "guest-agent-01",
            "api_key": "cp_live_guest_external_agent_key_2026",
            "tool_name": "employee_directory",
            "operation": "read",
            "requested_fields": ["national_id"]
        })

    # 4th request must be locked out with THROTTLE
    res = client.post("/api/security/execute", json={
        "agent_id": "guest-agent-01",
        "api_key": "cp_live_guest_external_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "THROTTLE"
    assert "Progressive Lockout" in data["reason"]

def test_scenario_14_audit_chain_tamper_verification(client):
    """Scenario 14: Audit hash chain integrity verification."""
    res = client.get("/api/audit-logs/verify-chain")
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["broken_sequence"] is None

def test_scenario_15_nlip_adapter_roundtrip(client):
    """Scenario 15: Official NLIP message roundtrip."""
    payload = {
        "messagetype": "request",
        "format": "structured",
        "subformat": "tool_invocation",
        "content": {
            "tool_name": "employee_directory",
            "operation": "read",
            "requested_fields": ["name", "attendance"],
            "parameters": {"department": "Engineering"}
        }
    }
    res = client.post("/api/nlip/process?agent_id=hr-agent-01&api_key=cp_live_hr_specialist_agent_key_2026", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["messagetype"] == "response"
    assert data["content"]["decision"] == "ALLOW"
    assert data["content"]["audit_hash"] is not None
