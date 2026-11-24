import pytest
from backend.app.adapters.python_agent import SecurePythonAgent, ControlPointLocalInterceptor
from backend.app.adapters.framework_adapters import (
    ControlPointLangChainToolWrapper,
    ControlPointLlamaIndexToolWrapper,
    ControlPointCrewAIToolWrapper
)

def test_secure_python_agent_allowed(client):
    """Test SecurePythonAgent making an authorized request."""
    agent = SecurePythonAgent(
        agent_id="hr-agent-01",
        name="HR Specialist Agent",
        role="HR Specialist",
        api_key="cp_live_hr_specialist_agent_key_2026"
    )

    result = agent.query_employee_directory(
        department="Engineering",
        fields=["name", "attendance"]
    )

    assert result["decision"] == "ALLOW"
    assert result["allowed"] is True
    assert len(result["data"]) > 0
    assert "name" in result["data"][0]
    assert result["audit_hash"] is not None

def test_secure_python_agent_denied(client):
    """Test SecurePythonAgent blocked when requesting unauthorized salary."""
    agent = SecurePythonAgent(
        agent_id="hr-agent-01",
        name="HR Specialist Agent",
        role="HR Specialist",
        api_key="cp_live_hr_specialist_agent_key_2026"
    )

    result = agent.query_employee_directory(
        department="Engineering",
        fields=["salary"]
    )

    assert result["decision"] == "DENY"
    assert result["allowed"] is False
    assert result["data"] is None

def test_langchain_tool_wrapper(client):
    """Test LangChain tool adapter interception."""
    class MockLangChainTool:
        name = "employee_directory"
        def run(self, **kwargs):
            return "raw_unprotected_output"

    wrapper = ControlPointLangChainToolWrapper(
        underlying_tool=MockLangChainTool(),
        agent_id="finance-agent-01",
        api_key="cp_live_finance_analyst_agent_key_2026",
        tool_name="employee_directory"
    )

    res = wrapper.run({"department": "Engineering", "fields": ["salary"]})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "salary" in res[0]

def test_crewai_tool_wrapper(client):
    """Test CrewAI tool adapter interception."""
    wrapper = ControlPointCrewAIToolWrapper(
        tool=None,
        agent_id="guest-agent-01",
        api_key="cp_live_guest_external_agent_key_2026",
        tool_name="employee_directory"
    )

    # Unauthorized national_id query
    res = wrapper.execute(department="Engineering", fields=["national_id"])
    assert "[ERROR: ACCESS_DENIED]" in res
