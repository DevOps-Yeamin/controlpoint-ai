import re
from typing import Dict, Any, List, Tuple, Optional
from backend.app.schemas.schemas import NormalizedRequest

# Catalog of known tools authorized in ControlPoint-AI
REGISTERED_TOOLS = {
    "employee_directory"
}

# Malicious argument detection patterns
DANGEROUS_ARG_PATTERNS = [
    re.compile(r"(--|;|'|\"|\b(UNION|SELECT|DROP|INSERT|DELETE|UPDATE|ALTER|EXEC|SHUTDOWN)\b)", re.IGNORECASE),
    re.compile(r"(<script|javascript:|eval\(|base64_decode)", re.IGNORECASE),
    re.compile(r"(\.\./|\.\.\\|/etc/passwd|/proc/|cmd\.exe|powershell)", re.IGNORECASE)
]

class RequestNormalizer:
    @staticmethod
    def normalize_fields(fields: List[str]) -> List[str]:
        """Normalize, strip, lowercase, and deduplicate requested field names."""
        if not fields:
            return []
        cleaned = []
        for f in fields:
            if isinstance(f, str):
                c = f.strip().lower()
                if c and c not in cleaned:
                    cleaned.append(c)
        return cleaned

    @staticmethod
    def validate_tool_name(tool_name: str) -> Tuple[bool, Optional[str]]:
        """Validate that the requested tool is registered in the system tool catalog."""
        t = str(tool_name or "").strip().lower()
        if not t:
            return False, "Tool Identification Failed: Empty tool name provided"
        if t not in REGISTERED_TOOLS:
            return False, f"Tool Identification Failed: Unknown tool '{tool_name}' is not registered in system catalog"
        return True, None

    @staticmethod
    def validate_arguments(parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate tool arguments for syntactic correctness, valid bounds,
        and absence of injection attack signatures.
        """
        if not isinstance(parameters, dict):
            return False, "Argument Validation Failed: Tool parameters must be a JSON object"

        # Check numeric parameter limits
        if "limit" in parameters:
            try:
                limit_val = int(parameters["limit"])
                if limit_val < 0 or limit_val > 1000:
                    return False, f"Argument Validation Failed: Parameter 'limit' must be between 0 and 1000 (received {limit_val})"
            except (ValueError, TypeError):
                return False, f"Argument Validation Failed: Parameter 'limit' must be an integer"

        # Check string parameters against injection patterns
        for key, val in parameters.items():
            if isinstance(val, str):
                for pattern in DANGEROUS_ARG_PATTERNS:
                    if pattern.search(val):
                        return False, f"Argument Validation Failed: Malformed or malicious parameter payload detected in '{key}'"

        return True, None

    @staticmethod
    def normalize_tool_call(
        agent_id: str,
        tool_name: str,
        operation: str = "read",
        requested_fields: List[str] = None,
        parameters: Dict[str, Any] = None,
        raw_payload: Dict[str, Any] = None
    ) -> NormalizedRequest:
        """Create a canonical NormalizedRequest from heterogeneous inputs."""
        norm_agent_id = str(agent_id or "").strip()
        norm_tool = str(tool_name or "").strip().lower()
        norm_op = str(operation or "read").strip().lower()
        norm_fields = RequestNormalizer.normalize_fields(requested_fields or [])
        norm_params = parameters if isinstance(parameters, dict) else {}

        # If fields weren't explicitly provided, check if parameters contain 'fields' or 'attributes'
        if not norm_fields and "fields" in norm_params and isinstance(norm_params["fields"], list):
            norm_fields = RequestNormalizer.normalize_fields(norm_params["fields"])
        elif not norm_fields and "attributes" in norm_params and isinstance(norm_params["attributes"], list):
            norm_fields = RequestNormalizer.normalize_fields(norm_params["attributes"])

        return NormalizedRequest(
            agent_id=norm_agent_id,
            tool_name=norm_tool,
            operation=norm_op,
            requested_fields=norm_fields,
            parameters=norm_params,
            raw_payload=raw_payload or {}
        )
