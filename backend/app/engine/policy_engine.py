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
        Supports multi-policy conflict resolution using most-restrictive (default-deny) semantics.
        
        Returns:
            Tuple of:
            - decision (DecisionEnum: ALLOW, DENY, REDACT)
            - reason (str)
            - permitted_fields (List[str])
            - denied_fields (List[str])
            - redacted_fields (List[str])
        """
        # Find active policies matching agent role and tool name
        policies = db.query(Policy).filter(
            Policy.is_active == True,
            (Policy.target_role == agent.role) | (Policy.target_role == "*")
        ).all()

        matching_policies: List[Policy] = []
        for p in policies:
            if p.target_tool == "*" or p.target_tool.lower() == req.tool_name.lower():
                matching_policies.append(p)

        # 1. Default-deny check
        if not matching_policies:
            return (
                DecisionEnum.DENY,
                f"Default Deny: No active policy allows agent role '{agent.role}' to access tool '{req.tool_name}'",
                [],
                req.requested_fields,
                []
            )

        # Multi-policy conflict resolution: intersection of allowed, union of denied (most restrictive)
        # 2. Operation check across matching policies
        for p in matching_policies:
            allowed_ops = [op.lower().strip() for op in p.get_allowed_operations()]
            if allowed_ops and req.operation.lower() not in allowed_ops and "*" not in allowed_ops:
                return (
                    DecisionEnum.DENY,
                    f"Operation '{req.operation}' is not authorized for tool '{req.tool_name}' under policy '{p.id}' ({p.name})",
                    [],
                    req.requested_fields,
                    []
                )

        # Calculate permitted & denied fields across all matching policies
        # Start with intersection of allowed fields from all matching policies
        intersect_allowed: Optional[Set[str]] = None
        union_denied: Set[str] = set()

        for p in matching_policies:
            p_allowed = {f.lower().strip() for f in p.get_allowed_fields()}
            p_denied = {f.lower().strip() for f in p.get_denied_fields()}
            if intersect_allowed is None:
                intersect_allowed = set(p_allowed)
            else:
                intersect_allowed = intersect_allowed.intersection(p_allowed)
            union_denied = union_denied.union(p_denied)

        intersect_allowed = intersect_allowed or set()
        requested_fields_set = {f.lower().strip() for f in req.requested_fields}

        # If agent requested no specific fields, assess against all policy known fields
        if not requested_fields_set:
            requested_fields_set = intersect_allowed | union_denied

        # Field authorization split
        permitted = (requested_fields_set.intersection(intersect_allowed)) - union_denied
        denied = (requested_fields_set.intersection(union_denied)) | (requested_fields_set - intersect_allowed)

        permitted_list = sorted(list(permitted))
        denied_list = sorted(list(denied))

        policy_names = ", ".join([p.name for p in matching_policies])
        conflict_note = f" (Resolved across {len(matching_policies)} overlapping policies via most-restrictive rule)" if len(matching_policies) > 1 else ""

        # 3. Decision Matrix
        if len(permitted) > 0 and len(denied) == 0:
            return (
                DecisionEnum.ALLOW,
                f"Access granted under policy '{policy_names}'{conflict_note}. All {len(permitted_list)} requested fields are authorized.",
                permitted_list,
                [],
                []
            )
        elif len(permitted) > 0 and len(denied) > 0:
            return (
                DecisionEnum.REDACT,
                f"Partial authorization under policy '{policy_names}'{conflict_note}. Permitted: [{', '.join(permitted_list)}]. Redacting unauthorized fields: [{', '.join(denied_list)}].",
                permitted_list,
                denied_list,
                denied_list
            )
        else:
            return (
                DecisionEnum.DENY,
                f"Access denied under policy '{policy_names}'{conflict_note}. None of the requested fields are permitted for role '{agent.role}': [{', '.join(denied_list)}].",
                [],
                denied_list,
                []
            )
