import pytest

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ControlPoint-AI"
    assert "database" in data

def test_api_agents_crud(client):
    # List initial seeded agents
    res = client.get("/api/agents")
    assert res.status_code == 200
    agents = res.json()
    assert len(agents) >= 3

    admin_headers = {"X-Admin-Key": "cp_live_admin_secret_key_2026"}

    # Create new agent
    new_agent_payload = {
        "id": "compliance-agent-01",
        "name": "Regulatory Compliance Agent",
        "role": "Compliance Officer",
        "description": "Auditing and compliance checking assistant",
        "rate_limit_per_minute": 30
    }
    create_res = client.post("/api/agents", json=new_agent_payload, headers=admin_headers)
    assert create_res.status_code == 200
    data = create_res.json()
    assert data["id"] == "compliance-agent-01"
    assert "raw_api_key" in data
    assert data["raw_api_key"].startswith("cp_live_compliance")

def test_api_policies_crud(client):
    res = client.get("/api/policies")
    assert res.status_code == 200
    policies = res.json()
    assert len(policies) >= 3

    new_policy = {
        "id": "policy-compliance-v1",
        "name": "Compliance Access Policy",
        "version": "v1.0.0",
        "target_role": "Compliance Officer",
        "target_tool": "employee_directory",
        "allowed_operations": ["read"],
        "allowed_fields": ["employee_id", "name", "department"],
        "denied_fields": ["salary", "national_id"],
        "default_action": "DENY"
    }
    admin_headers = {"X-Admin-Key": "cp_live_admin_secret_key_2026"}
    create_res = client.post("/api/policies", json=new_policy, headers=admin_headers)
    assert create_res.status_code == 200
    assert create_res.json()["id"] == "policy-compliance-v1"

def test_api_security_evaluate(client):
    payload = {
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "attendance"]
    }
    res = client.post("/api/security/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    assert data["allowed"] is True

def test_api_security_execute(client):
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
    assert len(data["enforced_data"]) > 0
    assert "audit_log_id" in data
    assert "audit_entry_hash" in data

def test_api_audit_logs_and_verify(client):
    # Execute a request to generate audit record
    client.post("/api/security/execute", json={
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"]
    })

    res = client.get("/api/audit-logs")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0

    verify_res = client.get("/api/audit-logs/verify-chain")
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True

def test_api_dashboard_summary(client):
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_requests" in data
    assert "chain_integrity" in data
    assert "decision_distribution" in data

def test_api_benchmark_suite(client):
    res = client.post("/api/benchmark/run")
    assert res.status_code == 200
    report = res.json()
    assert report["total_scenarios"] == 15
    assert report["passed_scenarios"] == 15
    assert report["failed_scenarios"] == 0
    assert report["accuracy_rate_pct"] == 100.0

    # Test export CSV
    csv_res = client.get("/api/benchmark/export?format=csv")
    assert csv_res.status_code == 200
    assert "Scenario ID,Name,Agent ID" in csv_res.text
