"""
ControlPoint-AI Agent Framework Adapters
Documented adapter interfaces for LangChain, LlamaIndex, and CrewAI.
Ensures unified Type-3 boundary enforcement without changing agent application code.
"""
from typing import Dict, Any, List, Optional, Callable
from backend.app.adapters.python_agent import ControlPointLocalInterceptor
from backend.app.schemas.schemas import DecisionEnum

class ControlPointLangChainToolWrapper:
    """
    Adapter for LangChain tools (langchain.tools.BaseTool).
    Intercepts tool calls prior to execution and filters returned observation outputs.
    
    Usage:
        raw_tool = EmployeeDirectoryTool()
        secure_tool = ControlPointLangChainToolWrapper(
            underlying_tool=raw_tool,
            agent_id="hr-agent-01",
            api_key="cp_live_hr_specialist_agent_key_2026"
        )
        agent = create_openai_tools_agent(llm, [secure_tool], prompt)
    """
    def __init__(
        self,
        underlying_tool: Any,
        agent_id: str,
        api_key: str,
        tool_name: Optional[str] = None
    ):
        self.underlying_tool = underlying_tool
        self.agent_id = agent_id
        self.api_key = api_key
        self.tool_name = tool_name or getattr(underlying_tool, "name", "employee_directory")
        self.interceptor = ControlPointLocalInterceptor(agent_id=agent_id, api_key=api_key)

    def run(self, tool_input: Dict[str, Any]) -> Any:
        requested_fields = tool_input.get("fields", tool_input.get("requested_fields", []))
        if isinstance(requested_fields, str):
            requested_fields = [f.strip() for f in requested_fields.split(",")]

        response = self.interceptor.call_tool_securely(
            tool_name=self.tool_name,
            operation="read",
            requested_fields=requested_fields,
            parameters=tool_input
        )

        if not response.allowed:
            return f"[SECURITY_VIOLATION_DENIED] Tool execution blocked by ControlPoint-AI: {response.reason}"

        return response.enforced_data

class ControlPointLlamaIndexToolWrapper:
    """
    Adapter for LlamaIndex tools (llama_index.core.tools.FunctionTool / BaseTool).
    
    Usage:
        tool = FunctionTool.from_defaults(fn=query_db)
        secure_tool = ControlPointLlamaIndexToolWrapper(
            tool=tool,
            agent_id="finance-agent-01",
            api_key="cp_live_finance_analyst_agent_key_2026"
        )
    """
    def __init__(self, tool: Any, agent_id: str, api_key: str, tool_name: str = "employee_directory"):
        self.tool = tool
        self.agent_id = agent_id
        self.api_key = api_key
        self.tool_name = tool_name
        self.interceptor = ControlPointLocalInterceptor(agent_id=agent_id, api_key=api_key)

    def __call__(self, *args, **kwargs) -> Any:
        fields = kwargs.get("fields", kwargs.get("requested_fields", []))
        response = self.interceptor.call_tool_securely(
            tool_name=self.tool_name,
            operation="read",
            requested_fields=fields if isinstance(fields, list) else [],
            parameters=kwargs
        )

        if not response.allowed:
            raise PermissionError(f"ControlPoint-AI Policy Denied: {response.reason}")

        return response.enforced_data

class ControlPointCrewAIToolWrapper:
    """
    Adapter for CrewAI tools (crewai.tools.BaseTool).
    
    Usage:
        @tool("Employee Query")
        def query_emp(dept: str, fields: list) -> str:
            return run_query(dept, fields)

        secure_tool = ControlPointCrewAIToolWrapper(
            tool=query_emp,
            agent_id="hr-agent-01",
            api_key="cp_live_hr_specialist_agent_key_2026"
        )
    """
    def __init__(self, tool: Any, agent_id: str, api_key: str, tool_name: str = "employee_directory"):
        self.tool = tool
        self.agent_id = agent_id
        self.api_key = api_key
        self.tool_name = tool_name
        self.interceptor = ControlPointLocalInterceptor(agent_id=agent_id, api_key=api_key)

    def execute(self, **kwargs) -> Any:
        fields = kwargs.get("fields", kwargs.get("requested_fields", []))
        response = self.interceptor.call_tool_securely(
            tool_name=self.tool_name,
            operation="read",
            requested_fields=fields if isinstance(fields, list) else [],
            parameters=kwargs
        )

        if not response.allowed:
            return f"[ERROR: ACCESS_DENIED] {response.reason}"

        return response.enforced_data
