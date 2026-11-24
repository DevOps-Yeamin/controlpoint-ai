"""
ControlPoint-AI Plain Python Agent Integration
Demonstrates zero-friction Type-3 security enforcement in native Python agent environments.
"""
from typing import Dict, Any, List, Optional, Callable
from backend.app.schemas.schemas import SecurityExecuteRequest, SecurityExecuteResponse, DecisionEnum
from backend.app.api.endpoints import execute_tool_request
from backend.app.database import SessionLocal

class ControlPointLocalInterceptor:
    """
    Direct in-process interceptor connecting an agent runtime to the ControlPoint-AI Security Engine.
    """
    def __init__(self, agent_id: str, api_key: str):
        self.agent_id = agent_id
        self.api_key = api_key

    def call_tool_securely(
        self,
        tool_name: str,
        operation: str = "read",
        requested_fields: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> SecurityExecuteResponse:
        """
        Execute tool call under ControlPoint-AI policy enforcement.
        """
        req = SecurityExecuteRequest(
            agent_id=self.agent_id,
            api_key=self.api_key,
            tool_name=tool_name,
            operation=operation,
            requested_fields=requested_fields or [],
            parameters=parameters or {}
        )
        db = SessionLocal()
        try:
            return execute_tool_request(req, db=db)
        finally:
            db.close()

class SecurePythonAgent:
    """
    Example autonomous agent operating with ControlPoint-AI Type-3 security guardrails.
    """
    def __init__(self, agent_id: str, name: str, role: str, api_key: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.interceptor = ControlPointLocalInterceptor(agent_id=agent_id, api_key=api_key)

    def query_employee_directory(
        self,
        department: str,
        fields: List[str]
    ) -> Dict[str, Any]:
        """
        Autonomous action: Queries the employee directory tool with policy protection.
        """
        response = self.interceptor.call_tool_securely(
            tool_name="employee_directory",
            operation="read",
            requested_fields=fields,
            parameters={"department": department}
        )

        return {
            "decision": response.decision.value,
            "allowed": response.allowed,
            "reason": response.reason,
            "redacted_fields": response.redacted_fields,
            "data": response.enforced_data,
            "audit_hash": response.audit_entry_hash
        }
