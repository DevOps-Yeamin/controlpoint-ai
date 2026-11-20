import pytest
from backend.app.models.entities import Agent, Policy, AuditLog
from backend.app.schemas.schemas import DecisionEnum
from backend.app.engine.normalizer import RequestNormalizer
from backend.app.engine.identity import IdentityValidator, hash_api_key
from backend.app.engine.rate_limiter import rate_limiter
from backend.app.engine.sensitive_data import SensitiveDataInspector
from backend.app.engine.policy_engine import PolicyEngine
from backend.app.engine.response_inspector import ResponseInspector
from backend.app.engine.audit import AuditLogger

def test_request_normalizer():
    raw_fields = ["  Name ", "SALARY", "name", "", None, "DEPARTMENT  "]
    cleaned = RequestNormalizer.normalize_fields(raw_fields)
    assert cleaned == ["name", "salary", "department"]

    norm = RequestNormalizer.normalize_tool_call(
        agent_id="  HR-AGENT-01  ",
        tool_name=" Employee_Directory ",
        operation=" READ ",
        requested_fields=["Name", "Email"],
        parameters={"foo": "bar"}
    )
    assert norm.agent_id == "HR-AGENT-01"
    assert norm.tool_name == "employee_directory"
    assert norm.operation == "read"
    assert norm.requested_fields == ["name", "email"]

def test_identity_validator(db_session):
    agent, err = IdentityValidator.validate(
        db_session,
        agent_id="hr-agent-01",
        api_key="cp_live_hr_specialist_agent_key_2026"
    )
    assert agent is not None
    assert err is None
    assert agent.role == "HR Specialist"

    # Test missing key
    agent, err = IdentityValidator.validate(db_session, agent_id="hr-agent-01", api_key="")
    assert agent is None
    assert "Unauthenticated" in err

    # Test forged/invalid key
    agent, err = IdentityValidator.validate(db_session, agent_id="hr-agent-01", api_key="wrong_key")
    assert agent is None
    assert "Authentication failed" in err

    # Test nonexistent agent
    agent, err = IdentityValidator.validate(db_session, agent_id="ghost-agent", api_key="any")
    assert agent is None
    assert "not registered" in err

def test_rate_limiter():
    rate_limiter.reset("test-agent")
    for _ in range(5):
        allowed, remaining, _ = rate_limiter.check_limit("test-agent", max_requests=5, window_seconds=60)
        assert allowed is True

    # 6th request must be throttled
    allowed, remaining, retry_after = rate_limiter.check_limit("test-agent", max_requests=5, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0

def test_sensitive_data_inspector():
    raw_text = "Employee record with SSN 123-45-6789 and API token cp_live_test_1234567890abcdef."
    findings = SensitiveDataInspector.inspect_text_for_patterns(raw_text)
    assert "national_id_pattern" in findings
    assert "api_key_pattern" in findings

    data = {
        "name": "Sarah",
        "salary": 150000,
        "note": "Secret SSN 982-12-8841",
        "nested": {
            "national_id": "SSN-123",
            "team": "Engineering"
        }
    }
    redacted, redacted_fields = SensitiveDataInspector.redact_data(data, denied_fields={"salary", "national_id"})
    assert redacted["name"] == "Sarah"
    assert redacted["salary"] == "[REDACTED: SENSITIVE_FIELD]"
    assert redacted["nested"]["national_id"] == "[REDACTED: SENSITIVE_FIELD]"
    assert redacted["nested"]["team"] == "Engineering"
    assert "[REDACTED: NATIONAL_ID]" in redacted["note"]

def test_policy_default_deny(db_session):
    agent = db_session.query(Agent).filter(Agent.id == "hr-agent-01").first()
    # Unapproved tool
    norm_req = RequestNormalizer.normalize_tool_call(
        agent_id=agent.id,
        tool_name="unauthorized_database_dump",
        operation="read",
        requested_fields=["everything"]
    )
    decision, reason, permitted, denied, _ = PolicyEngine.evaluate(db_session, agent, norm_req)
    assert decision == DecisionEnum.DENY
    assert "Default Deny" in reason

def test_response_inspector():
    tool_output = [
        {
            "name": "Sarah",
            "attendance": "99%",
            "salary": 185000,
            "national_id": "SSN-982-12-8841"
        }
    ]
    # Agent only authorized for name and attendance
    clean, redacted = ResponseInspector.inspect_and_sanitize(
        raw_data=tool_output,
        permitted_fields=["name", "attendance"],
        denied_fields=["salary", "national_id"]
    )
    assert clean[0]["name"] == "Sarah"
    assert clean[0]["attendance"] == "99%"
    assert clean[0]["salary"] == "[REDACTED: SENSITIVE_FIELD]"
    assert clean[0]["national_id"] == "[REDACTED: SENSITIVE_FIELD]"
    assert "salary" in redacted
    assert "national_id" in redacted

def test_audit_hash_chain_integrity(db_session):
    # Log 3 events
    AuditLogger.log_event(
        db=db_session,
        agent_id="hr-agent-01",
        agent_role="HR Specialist",
        tool_name="employee_directory",
        operation="read",
        requested_fields=["name"],
        decision="ALLOW",
        reason="Granted",
        redacted_fields=[]
    )
    AuditLogger.log_event(
        db=db_session,
        agent_id="guest-agent-01",
        agent_role="External Guest",
        tool_name="employee_directory",
        operation="read",
        requested_fields=["salary"],
        decision="DENY",
        reason="Unauthorized field",
        redacted_fields=[]
    )
    AuditLogger.log_event(
        db=db_session,
        agent_id="hr-agent-01",
        agent_role="HR Specialist",
        tool_name="employee_directory",
        operation="read",
        requested_fields=["name", "salary"],
        decision="REDACT",
        reason="Partial redaction",
        redacted_fields=["salary"]
    )

    verify_result = AuditLogger.verify_chain(db_session)
    assert verify_result.is_valid is True
    assert verify_result.total_records == 3
    assert verify_result.verified_records == 3

    # Now simulate tampering with record #2's entry hash
    record_2 = db_session.query(AuditLog).filter(AuditLog.sequence_number == 2).first()
    record_2.entry_hash = "tampered_hash_value_1234567890abcdef"
    db_session.commit()

    tamper_result = AuditLogger.verify_chain(db_session)
    assert tamper_result.is_valid is False
    assert tamper_result.broken_sequence == 2
    assert "Tampering detected" in tamper_result.error_message
