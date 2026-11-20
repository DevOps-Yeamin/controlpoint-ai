from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REDACT = "REDACT"
    THROTTLE = "THROTTLE"

# --- Agent Schemas ---
class AgentBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "HR Specialist Agent"})
    role: str = Field(..., json_schema_extra={"example": "HR Specialist"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Automated agent for HR record queries"})
    rate_limit_per_minute: int = Field(15, ge=1, le=1000)

class AgentCreate(AgentBase):
    id: str = Field(..., json_schema_extra={"example": "hr-agent-01"})

class AgentResponse(AgentBase):
    id: str
    api_key_prefix: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AgentCreateResult(AgentResponse):
    raw_api_key: str # Shown once upon creation

# --- Policy Schemas ---
class PolicyBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "HR Employee Read Policy"})
    version: str = Field("v1.0.0", json_schema_extra={"example": "v1.0.0"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Policy controlling HR field access"})
    target_role: str = Field(..., json_schema_extra={"example": "HR Specialist"})
    target_tool: str = Field("employee_directory", json_schema_extra={"example": "employee_directory"})
    allowed_operations: List[str] = Field(default_factory=list, json_schema_extra={"example": ["read", "query"]})
    allowed_fields: List[str] = Field(default_factory=list, json_schema_extra={"example": ["employee_id", "name", "email", "department", "attendance"]})
    denied_fields: List[str] = Field(default_factory=list, json_schema_extra={"example": ["salary", "national_id"]})
    default_action: str = Field("DENY", json_schema_extra={"example": "DENY"})
    is_active: bool = True

class PolicyCreate(PolicyBase):
    id: str = Field(..., json_schema_extra={"example": "policy-hr-directory-v1"})

class PolicyResponse(PolicyBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Tool Call / Request Normalization ---
class NormalizedRequest(BaseModel):
    agent_id: str
    tool_name: str
    operation: str
    requested_fields: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Optional[Dict[str, Any]] = None

# --- Security Evaluation & Execution ---
class SecurityEvaluateRequest(BaseModel):
    agent_id: str = Field(..., json_schema_extra={"example": "hr-agent-01"})
    api_key: Optional[str] = Field(None, description="API Key token for agent identity validation")
    tool_name: str = Field(..., json_schema_extra={"example": "employee_directory"})
    operation: str = Field("read", json_schema_extra={"example": "read"})
    requested_fields: List[str] = Field(default_factory=list, json_schema_extra={"example": ["name", "attendance"]})
    parameters: Dict[str, Any] = Field(default_factory=dict, json_schema_extra={"example": {"department": "Engineering"}})

class SecurityEvaluateResponse(BaseModel):
    decision: DecisionEnum
    allowed: bool
    reason: str
    agent_id: str
    agent_role: Optional[str] = None
    target_tool: str
    operation: str
    requested_fields: List[str]
    permitted_fields: List[str]
    denied_fields: List[str]
    redacted_fields: List[str]
    timestamp: datetime
    rate_limit_remaining: int

class SecurityExecuteRequest(BaseModel):
    agent_id: str = Field(..., json_schema_extra={"example": "hr-agent-01"})
    api_key: Optional[str] = Field(None, description="Secret API key proving agent identity")
    tool_name: str = Field(..., json_schema_extra={"example": "employee_directory"})
    operation: str = Field("read", json_schema_extra={"example": "read"})
    requested_fields: List[str] = Field(default_factory=list, json_schema_extra={"example": ["name", "attendance"]})
    parameters: Dict[str, Any] = Field(default_factory=dict, json_schema_extra={"example": {"department": "Engineering"}})

class SecurityExecuteResponse(BaseModel):
    decision: DecisionEnum
    allowed: bool
    reason: str
    agent_id: str
    tool_name: str
    requested_fields: List[str]
    redacted_fields: List[str]
    raw_result_count: int = 0
    enforced_data: Optional[Any] = None
    audit_log_id: Optional[int] = None
    audit_entry_hash: Optional[str] = None
    execution_time_ms: float

# --- Audit Logs ---
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
