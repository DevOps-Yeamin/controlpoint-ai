"""
ControlPoint-AI NLIP Adapter
Official Integration using verified `nlip_sdk` (v0.1.3).
Complies with NLIP (Natural Language Interaction Protocol) message specification.
"""
from typing import Dict, Any, Optional, Tuple, List
import json

try:
    from nlip_sdk.nlip import (
        NLIP_Message,
        NLIP_SubMessage,
        AllowedFormats,
        NLIP_Factory,
        loads as nlip_loads
    )
    HAS_OFFICIAL_NLIP = True
except ImportError:
    HAS_OFFICIAL_NLIP = False

from backend.app.schemas.schemas import NormalizedRequest, DecisionEnum

class NLIPAdapter:
    """
    Adapter between NLIP Protocol Messages and ControlPoint-AI Security Engine.
    Uses verified official nlip_sdk interfaces.
    """
    @staticmethod
    def is_available() -> bool:
        return HAS_OFFICIAL_NLIP

    @staticmethod
    def parse_to_normalized_request(
        nlip_payload: Dict[str, Any],
        agent_id: str
    ) -> NormalizedRequest:
        """
        Parses an incoming NLIP_Message structure into a NormalizedRequest.
        """
        if not HAS_OFFICIAL_NLIP:
            raise RuntimeError("Official nlip-sdk is not installed or available.")

        # Validate against NLIP_Message Pydantic model
        msg = NLIP_Message(**nlip_payload)
        
        content = msg.content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                content = {"raw_text": content}

        tool_name = content.get("tool_name", "employee_directory")
        operation = content.get("operation", "read")
        requested_fields = content.get("requested_fields", [])
        parameters = content.get("parameters", {})

        return NormalizedRequest(
            agent_id=agent_id,
            tool_name=tool_name,
            operation=operation,
            requested_fields=requested_fields,
            parameters=parameters,
            raw_payload=nlip_payload
        )

    @staticmethod
    def format_security_response(
        decision: DecisionEnum,
        reason: str,
        enforced_data: Any,
        redacted_fields: List[str],
        audit_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Encapsulates ControlPoint-AI security decision and sanitized data
        into an official NLIP_Message structure.
        """
        if not HAS_OFFICIAL_NLIP:
            # Fallback schema compliant with NLIP spec
            return {
                "messagetype": "response",
                "format": "structured",
                "subformat": "controlpoint_security_payload",
                "content": {
                    "decision": decision.value,
                    "reason": reason,
                    "redacted_fields": redacted_fields,
                    "data": enforced_data,
                    "audit_hash": audit_hash
                }
            }

        submessages = []
        if redacted_fields:
            submessages.append(
                NLIP_SubMessage(
                    format=AllowedFormats.structured,
                    subformat="security_redactions",
                    content={"redacted_fields": redacted_fields},
                    label="Redaction Notice"
                )
            )

        if audit_hash:
            submessages.append(
                NLIP_SubMessage(
                    format=AllowedFormats.token,
                    subformat="audit_proof",
                    content={"audit_hash": audit_hash},
                    label="Cryptographic Audit Proof"
                )
            )

        msg = NLIP_Message(
            messagetype="response",
            format=AllowedFormats.structured if decision != DecisionEnum.DENY else AllowedFormats.error,
            subformat="controlpoint_security_decision",
            content={
                "decision": decision.value,
                "reason": reason,
                "data": enforced_data if decision != DecisionEnum.DENY else None
            },
            label=f"ControlPoint Enforcement: {decision.value}",
            submessages=submessages if submessages else None
        )

        return msg.model_dump()
