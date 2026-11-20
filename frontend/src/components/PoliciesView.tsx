import React, { useEffect, useState } from 'react';
import { Lock, Plus, ShieldCheck, ShieldAlert, EyeOff, Tag, Check } from 'lucide-react';
import { api } from '../services/api';
import { Policy } from '../types';

export const PoliciesView: React.FC = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);

  // New policy form
  const [id, setId] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [version, setVersion] = useState<string>('v1.0.0');
  const [targetRole, setTargetRole] = useState<string>('HR Specialist');
  const [targetTool, setTargetTool] = useState<string>('employee_directory');
  const [allowedOps, setAllowedOps] = useState<string>('read, query');
  const [allowedFields, setAllowedFields] = useState<string>('employee_id, name, department');
  const [deniedFields, setDeniedFields] = useState<string>('salary, national_id');
  const [description, setDescription] = useState<string>('');

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const res = await api.getPolicies();
      setPolicies(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const ops = allowedOps.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
      const allowed = allowedFields.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
      const denied = deniedFields.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);

      await api.createPolicy({
        id,
        name,
        version,
        target_role: targetRole,
        target_tool: targetTool,
        allowed_operations: ops,
        allowed_fields: allowed,
        denied_fields: denied,
        default_action: 'DENY',
        description
      });
      setShowModal(false);
      loadPolicies();
    } catch (err: any) {
      alert(err.message || 'Failed to create policy');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#21262d] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security Policy Registry</h1>
          <p className="text-sm text-gray-400">
            Explicit, granular, deterministic Type-3 policies with default-deny enforcement and version control
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition shadow-md shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          Create New Policy
        </button>
      </div>

      {/* Policy Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {policies.map((policy) => (
          <div key={policy.id} className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 space-y-4 hover:border-blue-500/50 transition">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                  {policy.version}
                </span>
                <h2 className="text-sm font-bold text-white mt-2">{policy.name}</h2>
                <p className="text-xs text-gray-400 mt-1">{policy.description}</p>
              </div>
              <Lock className="w-5 h-5 text-blue-400 shrink-0" />
            </div>

            <div className="space-y-2 text-xs pt-2 border-t border-[#21262d]">
              <div className="flex justify-between">
                <span className="text-gray-400">Target Role:</span>
                <span className="font-semibold text-white font-mono">{policy.target_role}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Target Tool:</span>
                <span className="font-mono text-blue-400">{policy.target_tool}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Default Fallback:</span>
                <span className="font-mono text-rose-400 font-bold">DEFAULT-{policy.default_action}</span>
              </div>
            </div>

            {/* Allowed Fields */}
            <div className="space-y-1.5">
              <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Authorized Fields ({policy.allowed_fields.length})
              </span>
              <div className="flex flex-wrap gap-1">
                {policy.allowed_fields.map((f) => (
                  <span key={f} className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 font-mono text-[10px] border border-emerald-800/60">
                    {f}
                  </span>
                ))}
              </div>
            </div>

            {/* Denied Fields */}
            <div className="space-y-1.5">
              <span className="text-[11px] text-rose-400 font-medium flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                Explicitly Denied Fields ({policy.denied_fields.length})
              </span>
              <div className="flex flex-wrap gap-1">
                {policy.denied_fields.map((f) => (
                  <span key={f} className="px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 font-mono text-[10px] border border-rose-800/60">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Policy Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg max-w-lg w-full p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Lock className="w-5 h-5 text-blue-400" />
              Define New Type-3 Security Policy
            </h2>

            <form onSubmit={handleCreatePolicy} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Policy Identifier</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. policy-auditor-v1"
                    value={id}
                    onChange={(e) => setId(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Version</label>
                  <input
                    type="text"
                    required
                    value={version}
                    onChange={(e) => setVersion(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Policy Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Auditor Read-Only Inspection Policy"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Target Role</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Security Auditor"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Target Tool</label>
                  <input
                    type="text"
                    required
                    value={targetTool}
                    onChange={(e) => setTargetTool(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-blue-400 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Allowed Operations (comma-separated)</label>
                <input
                  type="text"
                  value={allowedOps}
                  onChange={(e) => setAllowedOps(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white font-mono"
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Authorized Fields (comma-separated)</label>
                <input
                  type="text"
                  value={allowedFields}
                  onChange={(e) => setAllowedFields(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-emerald-400 font-mono"
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Explicitly Denied Fields (comma-separated)</label>
                <input
                  type="text"
                  value={deniedFields}
                  onChange={(e) => setDeniedFields(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-rose-400 font-mono"
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Description</label>
                <input
                  type="text"
                  placeholder="Policy scope and reasoning"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5 text-xs text-white"
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
                  Save Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
