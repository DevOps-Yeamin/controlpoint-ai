import time
import json
import csv
import io
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.entities import Agent, Policy, AuditLog, SyntheticEmployee
from backend.app.schemas.schemas import (
    DecisionEnum,
    AgentCreate,
    AgentResponse,
    AgentCreateResult,
    PolicyCreate,
    PolicyResponse,
    SecurityEvaluateRequest,
    SecurityEvaluateResponse,
    SecurityExecuteRequest,
    SecurityExecuteResponse,
    AuditLogResponse,
    AuditChainVerifyResponse,
    DashboardSummary,
    BenchmarkReport,
    BenchmarkScenarioResult
)
from backend.app.engine.normalizer import RequestNormalizer
from backend.app.engine.identity import IdentityValidator, generate_agent_key, hash_api_key
from backend.app.engine.rate_limiter import rate_limiter
from backend.app.engine.policy_engine import PolicyEngine
from backend.app.engine.response_inspector import ResponseInspector
from backend.app.engine.audit import AuditLogger
from backend.app.engine.nlip_adapter import NLIPAdapter
from backend.app.tools.hr_tool import EmployeeDirectoryTool
from backend.app.core.config import settings

router = APIRouter()

# ----------------- Health -----------------
@router.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint providing system status and component readiness."""
    try:
        # Check DB connectivity
        db.execute(func.now()).scalar()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "organization": settings.ORGANIZATION,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "database": db_status,
        "nlip_sdk_available": NLIPAdapter.is_available(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ----------------- Dashboard -----------------
@router.get("/dashboard/summary", response_model=DashboardSummary, tags=["Dashboard"])
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Retrieve security enforcement metrics, audit stats, and decision analytics."""
    total_logs = db.query(AuditLog).count()
    allowed = db.query(AuditLog).filter(AuditLog.decision == DecisionEnum.ALLOW.value).count()
    denied = db.query(AuditLog).filter(AuditLog.decision == DecisionEnum.DENY.value).count()
    redacted = db.query(AuditLog).filter(AuditLog.decision == DecisionEnum.REDACT.value).count()
    throttled = db.query(AuditLog).filter(AuditLog.decision == DecisionEnum.THROTTLE.value).count()

    active_agents = db.query(Agent).filter(Agent.is_active == True).count()
    active_policies = db.query(Policy).filter(Policy.is_active == True).count()

    recent_logs = db.query(AuditLog).order_by(AuditLog.sequence_number.desc()).limit(8).all()
    chain_check = AuditLogger.verify_chain(db)

    recent_events_data = []
    for log in recent_logs:
        recent_events_data.append(
            AuditLogResponse(
                id=log.id,
                sequence_number=log.sequence_number,
                timestamp=log.timestamp,
                agent_id=log.agent_id,
                agent_role=log.agent_role,
                tool_name=log.tool_name,
                operation=log.operation,
                requested_fields=log.get_requested_fields(),
                decision=log.decision,
                reason=log.reason,
                redacted_fields=log.get_redacted_fields(),
                request_payload_hash=log.request_payload_hash,
                response_payload_hash=log.response_payload_hash,
                prev_entry_hash=log.prev_entry_hash,
                entry_hash=log.entry_hash
            )
        )

    return DashboardSummary(
        total_requests=total_logs,
        allowed_requests=allowed,
        denied_requests=denied,
        redacted_requests=redacted,
        throttled_requests=throttled,
        active_agents=active_agents,
        active_policies=active_policies,
        chain_integrity=chain_check.is_valid,
        recent_events=recent_events_data,
        decision_distribution={
            "ALLOW": allowed,
            "DENY": denied,
            "REDACT": redacted,
            "THROTTLE": throttled
        }
    )

# ----------------- Agent Management -----------------
@router.get("/agents", response_model=List[AgentResponse], tags=["Agents"])
def list_agents(db: Session = Depends(get_db)):
    """List registered AI agents."""
    agents = db.query(Agent).all()
    return agents

@router.post("/agents", response_model=AgentCreateResult, tags=["Agents"])
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    """Register a new autonomous AI agent with cryptographic credentials."""
    existing = db.query(Agent).filter(Agent.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Agent '{payload.id}' already exists")

    raw_key, key_hash, prefix = generate_agent_key(payload.id)

    new_agent = Agent(
        id=payload.id,
        name=payload.name,
        role=payload.role,
        description=payload.description,
        api_key_hash=key_hash,
        api_key_prefix=prefix,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        is_active=True
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    return AgentCreateResult(
        id=new_agent.id,
        name=new_agent.name,
        role=new_agent.role,
        description=new_agent.description,
        rate_limit_per_minute=new_agent.rate_limit_per_minute,
        api_key_prefix=new_agent.api_key_prefix,
        is_active=new_agent.is_active,
        created_at=new_agent.created_at,
        raw_api_key=raw_key
    )

# ----------------- Policy Management -----------------
@router.get("/policies", response_model=List[PolicyResponse], tags=["Policies"])
def list_policies(db: Session = Depends(get_db)):
    """List all security enforcement policies."""
    policies = db.query(Policy).all()
    result = []
    for p in policies:
        result.append(
            PolicyResponse(
                id=p.id,
                name=p.name,
                version=p.version,
                description=p.description,
                target_role=p.target_role,
                target_tool=p.target_tool,
                allowed_operations=p.get_allowed_operations(),
                allowed_fields=p.get_allowed_fields(),
                denied_fields=p.get_denied_fields(),
                default_action=p.default_action,
                is_active=p.is_active,
                created_at=p.created_at
            )
        )
    return result

@router.post("/policies", response_model=PolicyResponse, tags=["Policies"])
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    """Create a new granular security policy."""
    existing = db.query(Policy).filter(Policy.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Policy '{payload.id}' already exists")

    new_policy = Policy(
        id=payload.id,
        name=payload.name,
        version=payload.version,
        description=payload.description,
        target_role=payload.target_role,
        target_tool=payload.target_tool,
        allowed_operations=json.dumps(payload.allowed_operations),
        allowed_fields=json.dumps(payload.allowed_fields),
        denied_fields=json.dumps(payload.denied_fields),
        default_action=payload.default_action,
        is_active=payload.is_active
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    return PolicyResponse(
        id=new_policy.id,
        name=new_policy.name,
        version=new_policy.version,
        description=new_policy.description,
        target_role=new_policy.target_role,
        target_tool=new_policy.target_tool,
        allowed_operations=new_policy.get_allowed_operations(),
        allowed_fields=new_policy.get_allowed_fields(),
        denied_fields=new_policy.get_denied_fields(),
        default_action=new_policy.default_action,
        is_active=new_policy.is_active,
        created_at=new_policy.created_at
    )

# ----------------- Security Evaluation & Execution -----------------
@router.post("/security/evaluate", response_model=SecurityEvaluateResponse, tags=["Security Engine"])
def evaluate_tool_request(req: SecurityEvaluateRequest, db: Session = Depends(get_db)):
    """
    Dry-run policy evaluation.
    Checks identity, rate limits, and explicit policies without executing the underlying tool.
    """
    # 1. Normalize
    norm_req = RequestNormalizer.normalize_tool_call(
        agent_id=req.agent_id,
        tool_name=req.tool_name,
        operation=req.operation,
        requested_fields=req.requested_fields,
        parameters=req.parameters
    )

    # 2. Validate Agent Identity
    agent, identity_error = IdentityValidator.validate(db, norm_req.agent_id, req.api_key)
    if not agent:
        return SecurityEvaluateResponse(
            decision=DecisionEnum.DENY,
            allowed=False,
            reason=f"Identity Validation Failed: {identity_error}",
            agent_id=norm_req.agent_id,
            target_tool=norm_req.tool_name,
            operation=norm_req.operation,
            requested_fields=norm_req.requested_fields,
            permitted_fields=[],
            denied_fields=norm_req.requested_fields,
            redacted_fields=[],
            timestamp=datetime.now(timezone.utc),
            rate_limit_remaining=0
        )

    # 3. Rate Limit Check
    is_rate_allowed, remaining, _ = rate_limiter.check_limit(
        agent.id,
        max_requests=agent.rate_limit_per_minute,
        window_seconds=60
    )
    if not is_rate_allowed:
        return SecurityEvaluateResponse(
            decision=DecisionEnum.THROTTLE,
            allowed=False,
            reason=f"Rate limit exceeded for agent '{agent.id}' ({agent.rate_limit_per_minute} req/min)",
            agent_id=agent.id,
            agent_role=agent.role,
            target_tool=norm_req.tool_name,
            operation=norm_req.operation,
            requested_fields=norm_req.requested_fields,
            permitted_fields=[],
            denied_fields=norm_req.requested_fields,
            redacted_fields=[],
            timestamp=datetime.now(timezone.utc),
            rate_limit_remaining=0
        )

    # 4. Policy Evaluation
    decision, reason, permitted, denied, redacted = PolicyEngine.evaluate(db, agent, norm_req)

    return SecurityEvaluateResponse(
        decision=decision,
        allowed=(decision in [DecisionEnum.ALLOW, DecisionEnum.REDACT]),
        reason=reason,
        agent_id=agent.id,
        agent_role=agent.role,
        target_tool=norm_req.tool_name,
        operation=norm_req.operation,
        requested_fields=norm_req.requested_fields,
        permitted_fields=permitted,
        denied_fields=denied,
        redacted_fields=redacted,
        timestamp=datetime.now(timezone.utc),
        rate_limit_remaining=remaining
    )

@router.post("/security/execute", response_model=SecurityExecuteResponse, tags=["Security Engine"])
def execute_tool_request(req: SecurityExecuteRequest, db: Session = Depends(get_db)):
    """
    Enforces policy on live tool calls.
    Blocks execution if DENY or THROTTLE.
    Inspects and redacts unauthorized data in responses.
    Creates tamper-evident hash-chained audit record.
    """
    start_time = time.perf_counter()

    # 1. Normalize
    norm_req = RequestNormalizer.normalize_tool_call(
        agent_id=req.agent_id,
        tool_name=req.tool_name,
        operation=req.operation,
        requested_fields=req.requested_fields,
        parameters=req.parameters
    )

    # 2. Validate Identity
    agent, identity_error = IdentityValidator.validate(db, norm_req.agent_id, req.api_key)
    if not agent:
        decision = DecisionEnum.DENY
        reason = f"Identity Verification Failed: {identity_error}"
        audit_entry = AuditLogger.log_event(
            db=db,
            agent_id=norm_req.agent_id,
            agent_role="UNAUTHENTICATED",
            tool_name=norm_req.tool_name,
            operation=norm_req.operation,
            requested_fields=norm_req.requested_fields,
            decision=decision.value,
            reason=reason,
            redacted_fields=[],
            request_payload=req.model_dump(),
            response_payload={"error": reason}
        )
        elapsed = (time.perf_counter() - start_time) * 1000
        return SecurityExecuteResponse(
            decision=decision,
            allowed=False,
            reason=reason,
            agent_id=norm_req.agent_id,
            tool_name=norm_req.tool_name,
            requested_fields=norm_req.requested_fields,
            redacted_fields=[],
            raw_result_count=0,
            enforced_data=None,
            audit_log_id=audit_entry.id,
            audit_entry_hash=audit_entry.entry_hash,
            execution_time_ms=round(elapsed, 2)
        )

    # 3. Rate Limit Check
    is_rate_allowed, remaining, retry_after = rate_limiter.check_limit(
        agent.id,
        max_requests=agent.rate_limit_per_minute,
        window_seconds=60
    )
    if not is_rate_allowed:
        decision = DecisionEnum.THROTTLE
        reason = f"Throttled: Agent '{agent.id}' exceeded quota of {agent.rate_limit_per_minute} req/min. Retry after {round(retry_after, 1)}s."
        audit_entry = AuditLogger.log_event(
            db=db,
            agent_id=agent.id,
            agent_role=agent.role,
            tool_name=norm_req.tool_name,
            operation=norm_req.operation,
            requested_fields=norm_req.requested_fields,
            decision=decision.value,
            reason=reason,
            redacted_fields=[],
            request_payload=req.model_dump(),
            response_payload={"throttled": True}
        )
        elapsed = (time.perf_counter() - start_time) * 1000
        return SecurityExecuteResponse(
            decision=decision,
            allowed=False,
            reason=reason,
            agent_id=agent.id,
            tool_name=norm_req.tool_name,
            requested_fields=norm_req.requested_fields,
            redacted_fields=[],
            raw_result_count=0,
            enforced_data=None,
            audit_log_id=audit_entry.id,
            audit_entry_hash=audit_entry.entry_hash,
            execution_time_ms=round(elapsed, 2)
        )

    # 4. Policy Evaluation
    decision, reason, permitted, denied, initial_redactions = PolicyEngine.evaluate(db, agent, norm_req)

    # If DENIED: Tool execution MUST be prevented
    if decision == DecisionEnum.DENY:
        audit_entry = AuditLogger.log_event(
            db=db,
            agent_id=agent.id,
            agent_role=agent.role,
            tool_name=norm_req.tool_name,
            operation=norm_req.operation,
            requested_fields=norm_req.requested_fields,
            decision=decision.value,
            reason=reason,
            redacted_fields=[],
            request_payload=req.model_dump(),
            response_payload={"blocked": True}
        )
        elapsed = (time.perf_counter() - start_time) * 1000
        return SecurityExecuteResponse(
            decision=decision,
            allowed=False,
            reason=reason,
            agent_id=agent.id,
            tool_name=norm_req.tool_name,
            requested_fields=norm_req.requested_fields,
            redacted_fields=[],
            raw_result_count=0,
            enforced_data=None,
            audit_log_id=audit_entry.id,
            audit_entry_hash=audit_entry.entry_hash,
            execution_time_ms=round(elapsed, 2)
        )

    # 5. Tool Execution (Only reached if ALLOW or REDACT)
    force_leak = bool(norm_req.parameters.get("force_leak", False)) if norm_req.parameters else False
    raw_results = EmployeeDirectoryTool.execute(
        db=db,
        operation=norm_req.operation,
        parameters=norm_req.parameters,
        requested_fields=norm_req.requested_fields,
        force_leak_unauthorized_data=force_leak
    )

    # 6. Response Inspection & Outbound Redaction
    sanitized_results, redacted_fields = ResponseInspector.inspect_and_sanitize(
        raw_data=raw_results,
        permitted_fields=permitted,
        denied_fields=denied
    )

    # If response inspection detected unpermitted tool leak, upgrade decision to REDACT
    final_decision = decision
    if redacted_fields and final_decision == DecisionEnum.ALLOW:
        final_decision = DecisionEnum.REDACT
        reason = f"Tool response inspection: Sanitized {len(redacted_fields)} unauthorized leaked fields ({', '.join(redacted_fields)})."

    # 7. Tamper-evident Audit Logging
    audit_entry = AuditLogger.log_event(
        db=db,
        agent_id=agent.id,
        agent_role=agent.role,
        tool_name=norm_req.tool_name,
        operation=norm_req.operation,
        requested_fields=norm_req.requested_fields,
        decision=final_decision.value,
        reason=reason,
        redacted_fields=redacted_fields,
        request_payload=req.model_dump(),
        response_payload=sanitized_results
    )

    elapsed = (time.perf_counter() - start_time) * 1000

    return SecurityExecuteResponse(
        decision=final_decision,
        allowed=True,
        reason=reason,
        agent_id=agent.id,
        tool_name=norm_req.tool_name,
        requested_fields=norm_req.requested_fields,
        redacted_fields=redacted_fields,
        raw_result_count=len(raw_results),
        enforced_data=sanitized_results,
        audit_log_id=audit_entry.id,
        audit_entry_hash=audit_entry.entry_hash,
        execution_time_ms=round(elapsed, 2)
    )

# ----------------- Audit Logs -----------------
@router.get("/audit-logs", response_model=List[AuditLogResponse], tags=["Audit"])
def get_audit_logs(
    agent_id: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Query tamper-evident audit logs with optional filtering."""
    query = db.query(AuditLog)
    if agent_id:
        query = query.filter(AuditLog.agent_id == agent_id)
    if decision:
        query = query.filter(AuditLog.decision == decision.upper())

    logs = query.order_by(AuditLog.sequence_number.desc()).offset(offset).limit(limit).all()

    results = []
    for log in logs:
        results.append(
            AuditLogResponse(
                id=log.id,
                sequence_number=log.sequence_number,
                timestamp=log.timestamp,
                agent_id=log.agent_id,
                agent_role=log.agent_role,
                tool_name=log.tool_name,
                operation=log.operation,
                requested_fields=log.get_requested_fields(),
                decision=log.decision,
                reason=log.reason,
                redacted_fields=log.get_redacted_fields(),
                request_payload_hash=log.request_payload_hash,
                response_payload_hash=log.response_payload_hash,
                prev_entry_hash=log.prev_entry_hash,
                entry_hash=log.entry_hash
            )
        )
    return results

@router.get("/audit-logs/verify-chain", response_model=AuditChainVerifyResponse, tags=["Audit"])
def verify_audit_hash_chain(db: Session = Depends(get_db)):
    """Verifies cryptographic hash-chain integrity across all audit records."""
    return AuditLogger.verify_chain(db)

# ----------------- Security Testing & Benchmark Suite -----------------
SCENARIOS_SPEC = [
    {
        "id": 1,
        "name": "HR requests name and attendance",
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "attendance"],
        "expected_decision": "ALLOW",
        "description": "Legitimate authorized tool query matching HR policy"
    },
    {
        "id": 2,
        "name": "HR requests salary",
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["salary"],
        "expected_decision": "DENY",
        "description": "Unauthorized access to confidential compensation field"
    },
    {
        "id": 3,
        "name": "HR requests name and salary",
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name", "salary"],
        "expected_decision": "REDACT",
        "description": "Mixed authorized and unauthorized fields requiring partial redaction"
    },
    {
        "id": 4,
        "name": "Guest requests national_id",
        "agent_id": "guest-agent-01",
        "api_key": "cp_live_guest_external_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["national_id"],
        "expected_decision": "DENY",
        "description": "Strict denial of sensitive PII to external guest agent"
    },
    {
        "id": 5,
        "name": "Finance requests salary",
        "agent_id": "finance-agent-01",
        "api_key": "cp_live_finance_analyst_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["salary"],
        "expected_decision": "ALLOW",
        "description": "Authorized financial operations agent accessing compensation"
    },
    {
        "id": 6,
        "name": "Invalid identity verification",
        "agent_id": "hr-agent-01",
        "api_key": "cp_invalid_forged_agent_token_9999",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"],
        "expected_decision": "DENY",
        "description": "Spoofed/forged credential rejected by identity validation"
    },
    {
        "id": 7,
        "name": "Rate limit exceeded (Throttling)",
        "agent_id": "guest-agent-01",
        "api_key": "cp_live_guest_external_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"],
        "expected_decision": "THROTTLE",
        "trigger_burst": True,
        "description": "Agent exceeding allocated requests-per-minute quota"
    },
    {
        "id": 8,
        "name": "Tool returns unauthorized sensitive data (Response Inspection)",
        "agent_id": "hr-agent-01",
        "api_key": "cp_live_hr_specialist_agent_key_2026",
        "tool_name": "employee_directory",
        "operation": "read",
        "requested_fields": ["name"],
        "expected_decision": "REDACT",
        "force_leak": True,
        "description": "External tool leak sanitized by outbound response inspector"
    }
]

def run_scenarios(db: Session) -> BenchmarkReport:
    """Execute all security benchmark scenarios deterministically."""
    results: List[BenchmarkScenarioResult] = []
    latencies: List[float] = []

    for sc in SCENARIOS_SPEC:
        start = time.perf_counter()

        if sc.get("trigger_burst"):
            # Consume rate limit quota for agent
            for _ in range(7):
                rate_limiter.check_limit(sc["agent_id"], max_requests=5, window_seconds=60)

        params = {"department": "Engineering"}
        if sc.get("force_leak"):
            params["force_leak"] = True

        # Build execution request
        req = SecurityExecuteRequest(
            agent_id=sc["agent_id"],
            api_key=sc["api_key"],
            tool_name=sc["tool_name"],
            operation=sc["operation"],
            requested_fields=sc["requested_fields"],
            parameters=params
        )

        res = execute_tool_request(req, db=db)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)

        passed = (res.decision.value == sc["expected_decision"])
        results.append(
            BenchmarkScenarioResult(
                scenario_id=sc["id"],
                name=sc["name"],
                agent_id=sc["agent_id"],
                requested_fields=sc["requested_fields"],
                expected_decision=sc["expected_decision"],
                actual_decision=res.decision.value,
                passed=passed,
                latency_ms=round(elapsed, 2),
                details=res.reason
            )
        )

    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[int(len(latencies_sorted) * 0.5)]
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if len(latencies_sorted) > 1 else latencies_sorted[-1]

    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)

    # Attack prevention rate: of scenarios that expected DENY, REDACT, or THROTTLE
    security_scenarios = [r for r in results if r.expected_decision in ["DENY", "REDACT", "THROTTLE"]]
    prevention_passed = sum(1 for r in security_scenarios if r.passed)
    prevention_rate = (prevention_passed / len(security_scenarios) * 100) if security_scenarios else 100.0

    return BenchmarkReport(
        total_scenarios=total_count,
        passed_scenarios=passed_count,
        failed_scenarios=total_count - passed_count,
        prevention_rate_pct=round(prevention_rate, 2),
        accuracy_rate_pct=round((passed_count / total_count) * 100, 2),
        p50_latency_ms=round(p50, 2),
        p95_latency_ms=round(p95, 2),
        scenarios=results,
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/benchmark/results", response_model=BenchmarkReport, tags=["Benchmark"])
def get_benchmark_results(db: Session = Depends(get_db)):
    """Run security evaluation suite and report actual benchmark metrics."""
    return run_scenarios(db)

@router.post("/benchmark/run", response_model=BenchmarkReport, tags=["Benchmark"])
def trigger_benchmark(db: Session = Depends(get_db)):
    """Trigger a live run of all security scenarios."""
    return run_scenarios(db)

@router.get("/benchmark/export", tags=["Benchmark"])
def export_benchmark_results(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """Export benchmark evaluation results in JSON or CSV format."""
    report = run_scenarios(db)

    if format == "json":
        return Response(
            content=report.model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=controlpoint_benchmark_results.json"}
        )
    else:
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Scenario ID", "Name", "Agent ID", "Requested Fields", "Expected Decision", "Actual Decision", "Passed", "Latency (ms)", "Details"])
        for s in report.scenarios:
            writer.writerow([
                s.scenario_id,
                s.name,
                s.agent_id,
                ";".join(s.requested_fields),
                s.expected_decision,
                s.actual_decision,
                s.passed,
                s.latency_ms,
                s.details
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=controlpoint_benchmark_results.csv"}
        )

# ----------------- NLIP Integration Endpoint -----------------
@router.post("/nlip/process", tags=["NLIP"])
def process_nlip_message(
    payload: Dict[str, Any],
    agent_id: str = Query("hr-agent-01"),
    api_key: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Process an incoming official NLIP message through the ControlPoint-AI security pipeline.
    Uses official nlip_sdk formatting and returns an NLIP-compliant response.
    """
    if not NLIPAdapter.is_available():
        raise HTTPException(status_code=501, detail="NLIP SDK not installed on host")

    try:
        norm_req = NLIPAdapter.parse_to_normalized_request(payload, agent_id=agent_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid NLIP message format: {str(e)}")

    exec_req = SecurityExecuteRequest(
        agent_id=norm_req.agent_id,
        api_key=api_key or "cp_live_hr_specialist_agent_key_2026",
        tool_name=norm_req.tool_name,
        operation=norm_req.operation,
        requested_fields=norm_req.requested_fields,
        parameters=norm_req.parameters
    )

    result = execute_tool_request(exec_req, db=db)

    return NLIPAdapter.format_security_response(
        decision=result.decision,
        reason=result.reason,
        enforced_data=result.enforced_data,
        redacted_fields=result.redacted_fields,
        audit_hash=result.audit_entry_hash
    )
