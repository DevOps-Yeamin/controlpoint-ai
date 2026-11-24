export type DecisionType = "ALLOW" | "DENY" | "REDACT" | "THROTTLE";

export interface Agent {
  id: string;
  name: string;
  role: string;
  description?: string;
  api_key_prefix: string;
  rate_limit_per_minute: number;
  is_active: boolean;
  created_at: string;
}

export interface Policy {
  id: string;
  name: string;
  version: string;
  description?: string;
  target_role: string;
  target_tool: string;
  allowed_operations: string[];
  allowed_fields: string[];
  denied_fields: string[];
  default_action: string;
  is_active: boolean;
  created_at: string;
}

export interface AuditLog {
  id: number;
  sequence_number: number;
  timestamp: string;
  agent_id: string;
  agent_role: string;
  tool_name: string;
  operation: string;
  requested_fields: string[];
  decision: DecisionType;
  reason: string;
  redacted_fields: string[];
  request_payload_hash: string;
  response_payload_hash: string;
  prev_entry_hash: string;
  entry_hash: string;
}

export interface DashboardSummary {
  total_requests: number;
  allowed_requests: number;
  denied_requests: number;
  redacted_requests: number;
  throttled_requests: number;
  active_agents: number;
  active_policies: number;
  chain_integrity: boolean;
  recent_events: AuditLog[];
  decision_distribution: Record<string, number>;
}

export interface SecurityExecuteResponse {
  decision: DecisionType;
  allowed: boolean;
  reason: string;
  agent_id: string;
  tool_name: string;
  requested_fields: string[];
  redacted_fields: string[];
  raw_result_count: number;
  enforced_data: any;
  audit_log_id?: number;
  audit_entry_hash?: string;
  execution_time_ms: number;
}

export interface BenchmarkScenarioResult {
  scenario_id: number;
  name: string;
  agent_id: string;
  requested_fields: string[];
  expected_decision: string;
  actual_decision: string;
  passed: boolean;
  latency_ms: number;
  details: string;
}

export interface BaselineMetric {
  name: string;
  description: string;
  attack_success_rate_pct: number;
  attack_prevention_rate_pct: number;
  false_positive_rate_pct: number;
  false_negative_rate_pct: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  throughput_rps: number;
  enforcement_overhead_ms: number;
  audit_chain_verified: boolean;
}

export interface BenchmarkReport {
  total_scenarios: number;
  passed_scenarios: number;
  failed_scenarios: number;
  prevention_rate_pct: number;
  accuracy_rate_pct: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  scenarios: BenchmarkScenarioResult[];
  timestamp: string;
  baselines?: BaselineMetric[];
}

export interface AuditChainVerifyResponse {
  is_valid: boolean;
  total_records: number;
  verified_records: number;
  broken_sequence?: number;
  error_message?: string;
}
