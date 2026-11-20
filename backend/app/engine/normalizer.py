import re
from typing import Dict, Any, List
from backend.app.schemas.schemas import NormalizedRequest

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
