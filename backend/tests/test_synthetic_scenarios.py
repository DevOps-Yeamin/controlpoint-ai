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

    # 6th request
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
    # When HR requests only 'name', tool execution returns all fields, but ResponseInspector must redact unauthorized fields
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
    # Check that salary and national_id were redacted by the outbound inspector
    assert first_record.get("salary") == "[REDACTED: SENSITIVE_FIELD]"
    assert first_record.get("national_id") == "[REDACTED: SENSITIVE_FIELD]"
