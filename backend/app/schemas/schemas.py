from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

# --- Core Enums ---
class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REDACT = "REDACT"
    THROTTLE = "THROTTLE"

# --- Agent Schemas ---
class AgentBase(BaseModel):
    id: str = Field(..., description="Unique agent identifier (e.g. hr-agent-01)")
    name: str = Field(..., description="Human-readable name")
    role: str = Field(..., description="Agent role (e.g. HR Specialist, Finance Analyst, External Guest)")
    description: Optional[str] = None
    rate_limit_per_minute: int = Field(default=20, ge=1, le=1000)

class AgentCreate(AgentBase):
    api_key: Optional[str] = Field(None, description="Optional custom API key. If omitted, a secure key is auto-generated.")

class AgentResponse(AgentBase):
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AgentCreateResult(AgentResponse):
    raw_api_key: str = Field(..., description="The plain API key shown only once upon registration")

# --- Policy Schemas ---
class PolicyBase(BaseModel):
    id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    version: str = Field(default="v1.0.0", description="Policy version tracking")
    target_role: str = Field(..., description="Target role (or '*' for all)")
    target_tool: str = Field(..., description="Target tool (or '*' for all)")
    allowed_operations: List[str] = Field(default_factory=lambda: ["read"])
    allowed_fields: List[str] = Field(default_factory=list)
    denied_fields: List[str] = Field(default_factory=list)
    default_action: DecisionEnum = Field(default=DecisionEnum.DENY)
    is_active: bool = True
    description: Optional[str] = None

class PolicyCreate(PolicyBase):
    pass

class PolicyResponse(PolicyBase):
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Normalization & Security Request/Response Schemas ---
class NormalizedRequest(BaseModel):
    agent_id: str
    tool_name: str
    operation: str
    requested_fields: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

class SecurityEvaluateRequest(BaseModel):
    agent_id: str
    api_key: str
    tool_name: str
    operation: str = "read"
    requested_fields: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)

class SecurityEvaluateResponse(BaseModel):
    decision: DecisionEnum
    allowed: bool
    reason: str
    agent_id: str
    target_tool: str
    requested_fields: List[str]
    permitted_fields: List[str]
    denied_fields: List[str]
    redacted_fields: List[str]
    agent_role: Optional[str] = None
    operation: Optional[str] = None
    timestamp: Optional[datetime] = None
    rate_limit_remaining: Optional[int] = None

class SecurityExecuteRequest(BaseModel):
    agent_id: str
    api_key: str
    tool_name: str
    operation: str = "read"
    requested_fields: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)

class SecurityExecuteResponse(BaseModel):
    decision: DecisionEnum
    allowed: bool
    reason: str
    agent_id: str
    tool_name: str
    requested_fields: List[str]
    redacted_fields: List[str]
    raw_result_count: int
    enforced_data: Optional[Any] = None
    audit_log_id: Optional[int] = None
    audit_entry_hash: Optional[str] = None
    execution_time_ms: float

# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: int
    sequence_number: int
    timestamp: datetime
    agent_id: str
    agent_role: str
    tool_name: str
    operation: str
    requested_fields: List[str]
    decision: str
    reason: str
    redacted_fields: List[str]
    request_payload_hash: str
    response_payload_hash: str
    prev_entry_hash: str
    entry_hash: str
    model_config = ConfigDict(from_attributes=True)

class AuditChainVerifyResponse(BaseModel):
    is_valid: bool
    total_records: int
    verified_records: int
    broken_sequence: Optional[int] = None
    error_message: Optional[str] = None

# --- Dashboard & Benchmarks ---
class DashboardSummary(BaseModel):
    total_requests: int
    allowed_requests: int
    denied_requests: int
    redacted_requests: int
    throttled_requests: int
    active_agents: int
    active_policies: int
    chain_integrity: bool
    recent_events: List[AuditLogResponse]
    decision_distribution: Dict[str, int]

class BenchmarkScenarioResult(BaseModel):
    scenario_id: int
    name: str
    agent_id: str
    requested_fields: List[str]
    expected_decision: str
    actual_decision: str
    passed: bool
    latency_ms: float
    details: str

class BaselineMetric(BaseModel):
    name: str
    description: str
    attack_success_rate_pct: float
    attack_prevention_rate_pct: float
    false_positive_rate_pct: float
    false_negative_rate_pct: float
    p50_latency_ms: float
    p95_latency_ms: float
    throughput_rps: float
    enforcement_overhead_ms: float
    audit_chain_verified: bool

class BenchmarkReport(BaseModel):
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    prevention_rate_pct: float
    accuracy_rate_pct: float
    p50_latency_ms: float
    p95_latency_ms: float
    scenarios: List[BenchmarkScenarioResult]
    timestamp: datetime
    baselines: Optional[List[BaselineMetric]] = None
