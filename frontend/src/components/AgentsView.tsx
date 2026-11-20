import React, { useEffect, useState } from 'react';
import { Bot, Plus, Key, Clock, ShieldCheck, Check } from 'lucide-react';
import { api } from '../services/api';
import { Agent } from '../types';

export const AgentsView: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);

  // Form state
  const [newId, setNewId] = useState<string>('');
  const [newName, setNewName] = useState<string>('');
  const [newRole, setNewRole] = useState<string>('HR Specialist');
  const [newDesc, setNewDesc] = useState<string>('');
  const [newRateLimit, setNewRateLimit] = useState<number>(20);

  const [createdApiKey, setCreatedApiKey] = useState<string | null>(null);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const res = await api.getAgents();
      setAgents(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createAgent({
        id: newId,
        name: newName,
        role: newRole,
        description: newDesc,
        rate_limit_per_minute: Number(newRateLimit)
      });
      setCreatedApiKey(res.raw_api_key);
      loadAgents();
    } catch (err: any) {
      alert(err.message || 'Failed to create agent');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#21262d] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Agent Identity Directory</h1>
          <p className="text-sm text-gray-400">
            Registered autonomous agents, cryptographic credentials, roles, and allocated rate quotas
          </p>
        </div>
        <button
          onClick={() => {
            setCreatedApiKey(null);
            setShowModal(true);
          }}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition shadow-md shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          Register New Agent
        </button>
      </div>

      {/* Agents Table */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0d1117] text-gray-400 uppercase font-mono border-b border-[#21262d]">
              <tr>
                <th className="py-3 px-4">Agent Name</th>
                <th className="py-3 px-4">Identifier</th>
                <th className="py-3 px-4">Role Assignment</th>
                <th className="py-3 px-4">Credential Prefix</th>
                <th className="py-3 px-4">Rate Limit</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262d]">
              {agents.map((agent) => (
                <tr key={agent.id} className="hover:bg-[#1c2128] transition-colors">
                  <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-blue-900/40 border border-blue-700/50 flex items-center justify-center text-blue-300">
                      <Bot className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div>{agent.name}</div>
                      <div className="text-[10px] text-gray-500">{agent.description}</div>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-blue-400">{agent.id}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-[#0d1117] border border-[#30363d] text-gray-300 font-medium">
                      {agent.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-gray-400 flex items-center gap-1.5">
                    <Key className="w-3 h-3 text-amber-400" />
                    {agent.api_key_prefix}
                  </td>
                  <td className="py-3 px-4 font-mono text-gray-300">
                    {agent.rate_limit_per_minute} req/min
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                      ACTIVE
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-500 whitespace-nowrap">
                    {new Date(agent.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Register Agent Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg max-w-md w-full p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-400" />
              Register Autonomous AI Agent
            </h2>

            {createdApiKey ? (
              <div className="space-y-4">
                <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded text-emerald-300 text-xs">
                  Agent registered successfully! Copy the cryptographic API key below. It will not be shown again.
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Generated API Key Token</label>
                  <div className="p-2.5 bg-[#0d1117] border border-[#30363d] rounded font-mono text-xs text-amber-300 break-all select-all">
                    {createdApiKey}
                  </div>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreateAgent} className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Agent Identifier (slug)</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. audit-agent-01"
                    value={newId}
                    onChange={(e) => setNewId(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Agent Display Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Compliance Auditor Agent"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Role Assignment</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
                  >
                    <option value="HR Specialist">HR Specialist</option>
                    <option value="Financial Analyst">Financial Analyst</option>
                    <option value="External Guest">External Guest</option>
                    <option value="Security Auditor">Security Auditor</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Description</label>
                  <input
                    type="text"
                    placeholder="e.g. Authorized to verify compliance logs"
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Rate Limit (req/min)</label>
                  <input
                    type="number"
                    min={1}
                    max={1000}
                    value={newRateLimit}
                    onChange={(e) => setNewRateLimit(Number(e.target.value))}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white font-mono"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-1.5 bg-[#21262d] text-gray-300 rounded text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium"
                  >
                    Register Agent
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
