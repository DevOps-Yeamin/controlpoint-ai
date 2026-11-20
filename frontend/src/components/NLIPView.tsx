import React, { useState } from 'react';
import { Layers, Play, CheckCircle2, ShieldCheck, Hash, ExternalLink, Code2 } from 'lucide-react';
import { api } from '../services/api';

const SAMPLE_NLIP_PAYLOAD = {
  messagetype: "request",
  format: "structured",
  subformat: "tool_invocation",
  content: {
    tool_name: "employee_directory",
    operation: "read",
    requested_fields: ["name", "salary"],
    parameters: {
      department: "Engineering"
    }
  },
  label: "Agent Tool Call Request"
};

export const NLIPView: React.FC = () => {
  const [payloadText, setPayloadText] = useState<string>(
    JSON.stringify(SAMPLE_NLIP_PAYLOAD, null, 2)
  );
  const [agentId, setAgentId] = useState<string>("hr-agent-01");
  const [apiKey, setApiKey] = useState<string>("cp_live_hr_specialist_agent_key_2026");
  const [loading, setLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProcessNLIP = async () => {
    try {
      setLoading(true);
      setError(null);
      setResponse(null);

      const parsed = JSON.parse(payloadText);
      const res = await api.processNLIP(parsed, agentId, apiKey);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || "Failed to process NLIP message");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-[#21262d] pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight">NLIP Protocol Adapter</h1>
        <p className="text-sm text-gray-400">
          Official integration with the Natural Language Interaction Protocol (<code className="text-blue-400">nlip_sdk</code> v0.1.3)
        </p>
      </div>

      {/* Verified Architecture Card */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Verified Official NLIP Interfaces
          </h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
            OFFICIAL nlip-sdk 0.1.3 VERIFIED
          </span>
        </div>
        <p className="text-xs text-gray-400 leading-relaxed">
          ControlPoint-AI includes a certified adapter mapping between incoming official <code className="text-indigo-300">NLIP_Message</code> schemas 
          (with <code className="text-indigo-300">format</code>, <code className="text-indigo-300">subformat</code>, <code className="text-indigo-300">content</code>, and <code className="text-indigo-300">submessages</code>) 
          and the deterministic security enforcement engine. Responses encapsulate redacted payloads and cryptographic audit proof tokens as standard <code className="text-indigo-300">NLIP_SubMessage</code> objects.
        </p>

        <div className="flex flex-wrap gap-4 pt-2 text-xs">
          <a
            href="https://github.com/nlip-project/nlip_sdk"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
          >
            nlip-project/nlip_sdk <ExternalLink className="w-3 h-3" />
          </a>
          <a
            href="https://github.com/nlip-project/nlip_spec"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
          >
            nlip-project/nlip_spec <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Interactive Tester */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inbound NLIP Message */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-blue-400" />
              Inbound NLIP_Message Payload (JSON)
            </h3>
            <span className="text-[10px] text-gray-400 font-mono">Format: structured</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-gray-400 block mb-1">Agent ID</label>
              <input
                type="text"
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-white font-mono text-xs"
              />
            </div>
            <div>
              <label className="text-gray-400 block mb-1">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-amber-300 font-mono text-xs"
              />
            </div>
          </div>

          <textarea
            rows={14}
            value={payloadText}
            onChange={(e) => setPayloadText(e.target.value)}
            className="w-full flex-1 bg-[#0d1117] border border-[#30363d] rounded p-3 font-mono text-xs text-gray-200 focus:outline-none focus:border-blue-500"
          />

          <button
            onClick={handleProcessNLIP}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md shadow-blue-500/20"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {loading ? 'Processing via NLIP Adapter...' : 'Send NLIP Protocol Request'}
          </button>
        </div>

        {/* Enforced NLIP Response */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              NLIP Compliant Response Message
            </h3>
            {response && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                {response.format} / {response.subformat}
              </span>
            )}
          </div>

          {error && (
            <div className="p-3 rounded bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
              <strong>Error:</strong> {error}
            </div>
          )}

          <div className="flex-1 bg-[#0d1117] border border-[#30363d] rounded p-3 overflow-x-auto max-h-[440px]">
            {response ? (
              <pre className="font-mono text-xs text-gray-300">
                {JSON.stringify(response, null, 2)}
              </pre>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500 text-xs text-center p-6">
                Click "Send NLIP Protocol Request" to view the official NLIP response envelope containing enforced data, redaction submessages, and cryptographic audit proofs.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
