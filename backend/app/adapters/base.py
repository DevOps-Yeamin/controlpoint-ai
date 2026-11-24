"""
ControlPoint-AI Framework-Agnostic Interception Interface
Provides a standardized Type-3 security boundary interceptor for autonomous agent frameworks.
"""
from typing import Dict, Any, List, Optional, Callable, Tuple
from abc import ABC, abstractmethod

class BaseControlPointInterceptor(ABC):
    """
    Abstract Type-3 Security Interceptor.
    Enforces deterministic policy evaluation at pre-execution and post-execution boundaries.
    """
    @abstractmethod
    def intercept_tool_call(
        self,
        agent_id: str,
        api_key: str,
        tool_name: str,
        operation: str,
        requested_fields: List[str],
        parameters: Dict[str, Any],
        tool_executor: Callable[[Dict[str, Any]], Any]
    ) -> Dict[str, Any]:
        """
        Intercepts tool call, applies pre-execution checks, executes tool if permitted,
        sanitizes outbound tool responses, and logs cryptographic audit proofs.
        """
        pass
