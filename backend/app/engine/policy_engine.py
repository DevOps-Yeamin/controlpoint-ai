from typing import Dict, Any, List, Set, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models.entities import Agent, Policy
from backend.app.schemas.schemas import DecisionEnum, NormalizedRequest

class PolicyEngine:
    @staticmethod
    def evaluate(
        db: Session,
        agent: Agent,
        req: NormalizedRequest
    ) -> Tuple[DecisionEnum, str, List[str], List[str], List[str]]:
        """
        Evaluate security policy deterministically against normalized request.
        
        Returns:
            Tuple of:
            - decision (DecisionEnum: ALLOW, DENY, REDACT)
            - reason (str)
            - permitted_fields (List[str])
            - denied_fields (List[str])
            - redacted_fields (List[str])
        """
        # Find active policy matching agent role and tool name
        policies = db.query(Policy).filter(
            Policy.is_active == True,
            (Policy.target_role == agent.role) | (Policy.target_role == "*")
        ).all()

        matching_policy: Optional[Policy] = None
        for p in policies:
            if p.target_tool == "*" or p.target_tool.lower() == req.tool_name.lower():
                matching_policy = p
                break

        # 1. Default-deny check
        if not matching_policy:
            return (
                DecisionEnum.DENY,
                f"Default Deny: No active policy allows agent role '{agent.role}' to access tool '{req.tool_name}'",
                [],
                req.requested_fields,
                []
            )

        # 2. Operation check
        allowed_ops = [op.lower() for op in matching_policy.get_allowed_operations()]
        if allowed_ops and req.operation.lower() not in allowed_ops and "*" not in allowed_ops:
            return (
                DecisionEnum.DENY,
                f"Operation '{req.operation}' is not authorized for tool '{req.tool_name}' under policy '{matching_policy.id}'",
                [],
                req.requested_fields,
                []
            )

        policy_allowed_fields = {f.lower().strip() for f in matching_policy.get_allowed_fields()}
        policy_denied_fields = {f.lower().strip() for f in matching_policy.get_denied_fields()}
        requested_fields_set = {f.lower().strip() for f in req.requested_fields}

        # If agent requested no specific fields, assess against all policy known fields
        if not requested_fields_set:
            requested_fields_set = policy_allowed_fields | policy_denied_fields

        # Field authorization split
        permitted = requested_fields_set.intersection(policy_allowed_fields) - policy_denied_fields
        denied = (requested_fields_set.intersection(policy_denied_fields)) | (requested_fields_set - policy_allowed_fields)

        permitted_list = sorted(list(permitted))
        denied_list = sorted(list(denied))

        # 3. Decision Matrix
        if len(permitted) > 0 and len(denied) == 0:
            return (
                DecisionEnum.ALLOW,
                f"Access granted under policy '{matching_policy.name}' ({matching_policy.version}). All {len(permitted_list)} requested fields are authorized.",
                permitted_list,
                [],
                []
            )
        elif len(permitted) > 0 and len(denied) > 0:
            return (
                DecisionEnum.REDACT,
                f"Partial authorization under policy '{matching_policy.name}'. Permitted: [{', '.join(permitted_list)}]. Redacting unauthorized fields: [{', '.join(denied_list)}].",
                permitted_list,
                denied_list,
                denied_list
            )
        else:
            return (
                DecisionEnum.DENY,
                f"Access denied under policy '{matching_policy.name}'. None of the requested fields are permitted for role '{agent.role}': [{', '.join(denied_list)}].",
                [],
                denied_list,
                []
            )
