import {
  DashboardSummary,
  Agent,
  Policy,
  AuditLog,
  AuditChainVerifyResponse,
  SecurityExecuteResponse,
  BenchmarkReport
} from "../types";

const API_BASE = "/api";

export const api = {
  // System Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  // Dashboard Summary
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    if (!res.ok) throw new Error("Failed to fetch dashboard summary");
    return res.json();
  },

  // Agents
  async getAgents(): Promise<Agent[]> {
    const res = await fetch(`${API_BASE}/agents`);
    if (!res.ok) throw new Error("Failed to fetch agents");
    return res.json();
  },

  async createAgent(data: {
    id: string;
    name: string;
    role: string;
    description?: string;
    rate_limit_per_minute: number;
  }) {
    const res = await fetch(`${API_BASE}/agents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create agent");
    }
    return res.json();
  },

  // Policies
  async getPolicies(): Promise<Policy[]> {
    const res = await fetch(`${API_BASE}/policies`);
    if (!res.ok) throw new Error("Failed to fetch policies");
    return res.json();
  },

  async createPolicy(data: {
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
  }) {
    const res = await fetch(`${API_BASE}/policies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create policy");
    }
    return res.json();
  },

  // Security Evaluation & Execution
  async evaluateTool(payload: {
    agent_id: string;
    api_key?: string;
    tool_name: string;
    operation: string;
    requested_fields: string[];
    parameters?: Record<string, any>;
  }) {
    const res = await fetch(`${API_BASE}/security/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Evaluation request failed");
    return res.json();
  },

  async executeTool(payload: {
    agent_id: string;
    api_key?: string;
    tool_name: string;
    operation: string;
    requested_fields: string[];
    parameters?: Record<string, any>;
  }): Promise<SecurityExecuteResponse> {
    const res = await fetch(`${API_BASE}/security/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Execution request failed");
    return res.json();
  },

  // Audit Logs
  async getAuditLogs(agent_id?: string, decision?: string): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    if (agent_id) params.set("agent_id", agent_id);
    if (decision) params.set("decision", decision);
    params.set("limit", "100");

    const res = await fetch(`${API_BASE}/audit-logs?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch audit logs");
    return res.json();
  },

  async verifyAuditChain(): Promise<AuditChainVerifyResponse> {
    const res = await fetch(`${API_BASE}/audit-logs/verify-chain`);
    if (!res.ok) throw new Error("Failed to verify audit hash-chain");
    return res.json();
  },

  // Benchmarks
  async getBenchmarkResults(): Promise<BenchmarkReport> {
    const res = await fetch(`${API_BASE}/benchmark/results`);
    if (!res.ok) throw new Error("Failed to load benchmark results");
    return res.json();
  },

  async runBenchmark(): Promise<BenchmarkReport> {
    const res = await fetch(`${API_BASE}/benchmark/run`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to execute benchmark suite");
    return res.json();
  },

  // NLIP Protocol
  async processNLIP(nlipMessage: any, agent_id: string, api_key?: string) {
    const params = new URLSearchParams({ agent_id });
    if (api_key) params.set("api_key", api_key);

    const res = await fetch(`${API_BASE}/nlip/process?${params.toString()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(nlipMessage)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "NLIP processing failed");
    }
    return res.json();
  }
};
