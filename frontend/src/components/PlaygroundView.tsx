import React, { useState } from 'react';
import { 
  Play, 
  Search, 
  ShieldAlert, 
  ShieldCheck, 
  EyeOff, 
  Gauge, 
  Key, 
  Database, 
  Layers, 
  Check, 
  Clock, 
  Hash,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { SecurityExecuteResponse } from '../types';

interface AgentPreset {
  id: string;
  name: string;
  role: string;
  apiKey: string;
  defaultFields: string[];
}

const AGENT_PRESETS: AgentPreset[] = [
  {
    id: "hr-agent-01",
    name: "HR Specialist Agent",
    role: "HR Specialist",
    apiKey: "cp_live_hr_specialist_agent_key_2026",
    defaultFields: ["name", "attendance"]
  },
  {
    id: "finance-agent-01",
    name: "Finance Operations Agent",
    role: "Financial Analyst",
    apiKey: "cp_live_finance_analyst_agent_key_2026",
    defaultFields: ["name", "salary"]
  },
  {
    id: "guest-agent-01",
    name: "Guest Directory Agent",
    role: "External Guest",
    apiKey: "cp_live_guest_external_agent_key_2026",
    defaultFields: ["name", "department"]
  }
];

const AVAILABLE_FIELDS = [
  "employee_id",
  "name",
  "email",
  "department",
  "attendance",
  "salary",
  "national_id"
];

export const PlaygroundView: React.FC = () => {
  const [selectedPreset, setSelectedPreset] = useState<string>("hr-agent-01");
  const [agentId, setAgentId] = useState<string>("hr-agent-01");
  const [apiKey, setApiKey] = useState<string>("cp_live_hr_specialist_agent_key_2026");
  const [toolName, setToolName] = useState<string>("employee_directory");
  const [operation, setOperation] = useState<string>("read");
  const [selectedFields, setSelectedFields] = useState<string[]>(["name", "attendance"]);
  const [simulateToolLeak, setSimulateToolLeak] = useState<boolean>(false);
  const [departmentFilter, setDepartmentFilter] = useState<string>("Engineering");

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SecurityExecuteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSelectPreset = (presetId: string) => {
    const preset = AGENT_PRESETS.find(p => p.id === presetId);
    if (preset) {
      setSelectedPreset(preset.id);
      setAgentId(preset.id);
      setApiKey(preset.apiKey);
      setSelectedFields(preset.defaultFields);
    }
  };

  const toggleField = (field: string) => {
    if (selectedFields.includes(field)) {
      setSelectedFields(selectedFields.filter(f => f !== field));
    } else {
      setSelectedFields([...selectedFields, field]);
    }
  };

  const handleExecute = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const payload = {
        agent_id: agentId,
        api_key: apiKey,
        tool_name: toolName,
        operation: operation,
        requested_fields: selectedFields,
        parameters: {
          department: departmentFilter,
          force_leak: simulateToolLeak
        }
      };

      const res = await api.executeTool(payload);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Execution failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDryRun = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const payload = {
        agent_id: agentId,
        api_key: apiKey,
        tool_name: toolName,
        operation: operation,
        requested_fields: selectedFields,
        parameters: {
          department: departmentFilter
        }
      };

      const res = await api.evaluateTool(payload);
      setResult({
        decision: res.decision,
        allowed: res.allowed,
        reason: res.reason,
        agent_id: res.agent_id,
        tool_name: res.target_tool,
        requested_fields: res.requested_fields,
        redacted_fields: res.redacted_fields,
        raw_result_count: 0,
        enforced_data: null,
        execution_time_ms: 1.2
      });
    } catch (err: any) {
      setError(err.message || "Evaluation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-[#21262d] pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight">Security Engine Playground</h1>
        <p className="text-sm text-gray-400">
          Simulate real autonomous agent tool requests against ControlPoint-AI's Type-3 Security Enforcement Engine
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Request Configuration Panel */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              1. Select Agent Identity
            </h2>

            {/* Agent Presets */}
            <div className="grid grid-cols-3 gap-2">
              {AGENT_PRESETS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleSelectPreset(p.id)}
                  className={`p-2.5 rounded text-left border text-xs transition ${
                    selectedPreset === p.id
                      ? 'bg-blue-600/20 border-blue-500 text-white font-medium'
                      : 'bg-[#0d1117] border-[#30363d] text-gray-400 hover:border-gray-500'
                  }`}
                >
                  <div className="font-semibold">{p.name.split(" ")[0]} Agent</div>
                  <div className="text-[10px] text-gray-400">{p.role}</div>
                </button>
              ))}
            </div>

            {/* Agent ID & Key */}
            <div className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Agent Identifier</label>
                <input
                  type="text"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1 flex items-center justify-between">
                  <span>Cryptographic API Key (Identity Proof)</span>
                  <Key className="w-3.5 h-3.5 text-amber-400" />
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-amber-300 font-mono focus:outline-none focus:border-amber-500"
                />
                <span className="text-[10px] text-gray-500 mt-1 block">
                  Never trusts user-supplied agent_id without secret verification.
                </span>
              </div>
            </div>
          </div>

          {/* Tool & Operation */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              2. Target Tool & Operation
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Tool Name</label>
                <input
                  type="text"
                  value={toolName}
                  onChange={(e) => setToolName(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-blue-400 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Operation</label>
                <select
                  value={operation}
                  onChange={(e) => setOperation(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
                >
                  <option value="read">read</option>
                  <option value="query">query</option>
                  <option value="export">export</option>
                  <option value="delete">delete (Unauthorized)</option>
                </select>
              </div>
            </div>

            {/* Requested Data Fields */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2">
                Requested Data Fields ({selectedFields.length} selected)
              </label>
              <div className="flex flex-wrap gap-1.5">
                {AVAILABLE_FIELDS.map((field) => {
                  const isSelected = selectedFields.includes(field);
                  const isSensitive = ["salary", "national_id"].includes(field);
                  return (
                    <button
                      key={field}
                      onClick={() => toggleField(field)}
                      className={`px-2.5 py-1 rounded text-xs font-mono transition flex items-center gap-1 border ${
                        isSelected
                          ? isSensitive
                            ? 'bg-rose-950/70 border-rose-600 text-rose-300'
                            : 'bg-blue-900/40 border-blue-500 text-blue-300'
                          : 'bg-[#0d1117] border-[#30363d] text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3" />}
                      {field}
                      {isSensitive && <span className="text-[9px] text-rose-400 font-bold ml-0.5">SENSITIVE</span>}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tool Leak Simulation */}
            <div className="pt-2 border-t border-[#21262d]">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simulateToolLeak}
                  onChange={(e) => setSimulateToolLeak(e.target.checked)}
                  className="rounded bg-[#0d1117] border-[#30363d] text-blue-600 focus:ring-0"
                />
                <span className="text-xs text-amber-300 font-medium flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  Simulate Insecure External Tool Leak (Scenario 8)
                </span>
              </label>
              <p className="text-[10px] text-gray-500 mt-1 pl-5">
                Simulates tool returning unrequested sensitive fields (e.g. salary, national_id); tests outbound response inspection.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="pt-2 flex gap-3">
              <button
                onClick={handleExecute}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition shadow-lg shadow-blue-500/20"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                {loading ? 'Evaluating & Executing...' : 'Execute Tool (Enforce Policy)'}
              </button>
              <button
                onClick={handleDryRun}
                disabled={loading}
                className="py-2 px-3 rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-300 text-xs font-medium border border-[#30363d]"
              >
                Dry Run
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Response & Enforcement Inspection Panel */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 min-h-[500px] flex flex-col">
            <div className="flex items-center justify-between border-b border-[#21262d] pb-3 mb-4">
              <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Deterministic Enforcement Output
              </h2>
              {result && (
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-gray-500" />
                    {result.execution_time_ms} ms
                  </span>
                  {result.audit_entry_hash && (
                    <span className="flex items-center gap-1 font-mono text-[11px] text-blue-400" title={result.audit_entry_hash}>
                      <Hash className="w-3.5 h-3.5" />
                      Block #{result.audit_log_id}
                    </span>
                  )}
                </div>
              )}
            </div>

            {error && (
              <div className="p-4 rounded-md bg-rose-950/50 border border-rose-800 text-rose-300 text-xs mb-4">
                <strong>Error:</strong> {error}
              </div>
            )}

            {!result && !error && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-gray-500">
                <Search className="w-12 h-12 text-gray-600 mb-3" />
                <h3 className="text-sm font-medium text-gray-300">Awaiting Tool-Call Request</h3>
                <p className="text-xs text-gray-500 max-w-sm mt-1">
                  Configure the agent parameters on the left and click "Execute Tool" to see real Type-3 policy evaluation and selective redaction.
                </p>
              </div>
            )}

            {result && (
              <div className="space-y-4 flex-1">
                {/* Decision Banner */}
                <div className={`p-4 rounded-lg border flex items-start justify-between ${
                  result.decision === 'ALLOW' ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300' :
                  result.decision === 'DENY' ? 'bg-rose-950/40 border-rose-800/80 text-rose-300' :
                  result.decision === 'REDACT' ? 'bg-amber-950/40 border-amber-800/80 text-amber-300' :
                  'bg-purple-950/40 border-purple-800/80 text-purple-300'
                }`}>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs uppercase font-extrabold px-2.5 py-0.5 rounded bg-black/40 border border-current">
                        {result.decision}
                      </span>
                      <span className="text-xs font-semibold">
                        {result.allowed ? 'Execution Permitted' : 'Execution Prevented'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-300 mt-2">{result.reason}</p>
                  </div>

                  <div className="text-right">
                    {result.decision === 'ALLOW' && <ShieldCheck className="w-8 h-8 text-emerald-400" />}
                    {result.decision === 'DENY' && <ShieldAlert className="w-8 h-8 text-rose-400" />}
                    {result.decision === 'REDACT' && <EyeOff className="w-8 h-8 text-amber-400" />}
                    {result.decision === 'THROTTLE' && <Gauge className="w-8 h-8 text-purple-400" />}
                  </div>
                </div>

                {/* Field-level Redaction Details */}
                {result.redacted_fields && result.redacted_fields.length > 0 && (
                  <div className="p-3 bg-[#0d1117] rounded border border-amber-900/50 text-xs">
                    <span className="text-amber-400 font-semibold block mb-1">
                      Selective Field Redactions Applied:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {result.redacted_fields.map((f) => (
                        <span key={f} className="px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 font-mono text-[11px] border border-amber-800/60">
                          {f}: [REDACTED: SENSITIVE_FIELD]
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sanitized Tool Data Payload */}
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                    <span>Enforced Response Payload</span>
                    <span className="font-mono">{result.raw_result_count} records returned</span>
                  </div>
                  <pre className="bg-[#0d1117] border border-[#21262d] rounded-md p-3 text-xs font-mono text-gray-300 overflow-x-auto max-h-72">
                    {result.enforced_data 
                      ? JSON.stringify(result.enforced_data, null, 2)
                      : '// No payload returned: Tool execution was strictly blocked by security policy'}
                  </pre>
                </div>

                {/* Audit Hash Proof */}
                {result.audit_entry_hash && (
                  <div className="p-3 rounded bg-[#0d1117] border border-[#21262d] text-xs space-y-1">
                    <div className="text-gray-400 flex items-center justify-between">
                      <span className="flex items-center gap-1 text-gray-300 font-semibold">
                        <Hash className="w-3.5 h-3.5 text-blue-400" />
                        Tamper-Evident SHA-256 Audit Proof
                      </span>
                      <span className="text-emerald-400 font-mono text-[10px]">Chained Block #{result.audit_log_id}</span>
                    </div>
                    <div className="font-mono text-gray-400 text-[11px] break-all">
                      {result.audit_entry_hash}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
