import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Search, 
  Hash, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw,
  Filter,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';
import { AuditLog, AuditChainVerifyResponse } from '../types';

export const AuditLogsView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [agentFilter, setAgentFilter] = useState<string>('');
  const [decisionFilter, setDecisionFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const [verifyStatus, setVerifyStatus] = useState<AuditChainVerifyResponse | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getAuditLogs(agentFilter || undefined, decisionFilter || undefined);
      setLogs(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const verifyChain = async () => {
    try {
      setVerifying(true);
      const res = await api.verifyAuditChain();
      setVerifyStatus(res);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    loadLogs();
    verifyChain();
  }, [agentFilter, decisionFilter]);

  const filteredLogs = logs.filter(l => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      l.agent_id.toLowerCase().includes(term) ||
      l.tool_name.toLowerCase().includes(term) ||
      l.reason.toLowerCase().includes(term) ||
      l.entry_hash.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#21262d] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Tamper-Evident Audit Records</h1>
          <p className="text-sm text-gray-400">
            Immutable, SHA-256 hash-chained security event log proving every policy decision and redaction
          </p>
        </div>
        <button
          onClick={verifyChain}
          disabled={verifying}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition shadow-md shadow-blue-500/20"
        >
          <ShieldCheck className={`w-4 h-4 ${verifying ? 'animate-spin' : ''}`} />
          {verifying ? 'Verifying Hashes...' : 'Verify Hash-Chain Integrity'}
        </button>
      </div>

      {/* Verification Banner */}
      {verifyStatus && (
        <div className={`p-4 rounded-lg border flex items-center justify-between text-xs ${
          verifyStatus.is_valid
            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
            : 'bg-rose-950/40 border-rose-800 text-rose-300'
        }`}>
          <div className="flex items-center gap-3">
            {verifyStatus.is_valid ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-400" />
            )}
            <div>
              <div className="font-bold text-sm">
                {verifyStatus.is_valid ? 'Cryptographic Hash-Chain Integrity Verified' : 'Cryptographic Hash-Chain Broken!'}
              </div>
              <p className="text-gray-400">
                {verifyStatus.is_valid
                  ? `All ${verifyStatus.verified_records} blocks verified from genesis (block #1) to tip without tampering or gap.`
                  : verifyStatus.error_message}
              </p>
            </div>
          </div>
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-black/40 border border-current font-semibold">
            {verifyStatus.is_valid ? 'CHAIN 100% VALID' : 'ALERT: COMPROMISED'}
          </span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-3 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
          <input
            type="text"
            placeholder="Search by agent, tool, reason, or entry hash..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#0d1117] border border-[#30363d] rounded pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-gray-400" />
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="bg-[#0d1117] border border-[#30363d] rounded px-2.5 py-1.5 text-xs text-gray-300"
          >
            <option value="">All Decisions</option>
            <option value="ALLOW">ALLOW</option>
            <option value="DENY">DENY</option>
            <option value="REDACT">REDACT</option>
            <option value="THROTTLE">THROTTLE</option>
          </select>

          <button
            onClick={loadLogs}
            className="p-1.5 bg-[#0d1117] hover:bg-[#21262d] border border-[#30363d] rounded text-gray-400"
            title="Refresh logs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0d1117] text-gray-400 uppercase font-mono border-b border-[#21262d]">
              <tr>
                <th className="py-3 px-3">Block #</th>
                <th className="py-3 px-3">Timestamp</th>
                <th className="py-3 px-3">Agent</th>
                <th className="py-3 px-3">Role</th>
                <th className="py-3 px-3">Tool</th>
                <th className="py-3 px-3">Decision</th>
                <th className="py-3 px-3">Reason</th>
                <th className="py-3 px-3">Redactions</th>
                <th className="py-3 px-3 font-mono">Previous Block Hash</th>
                <th className="py-3 px-3 font-mono">Current Block Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262d]">
              {filteredLogs.map((log) => {
                let badgeClass = "bg-gray-800 text-gray-300";
                if (log.decision === "ALLOW") badgeClass = "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60";
                else if (log.decision === "DENY") badgeClass = "bg-rose-950/80 text-rose-400 border border-rose-800/60";
                else if (log.decision === "REDACT") badgeClass = "bg-amber-950/80 text-amber-400 border border-amber-800/60";
                else if (log.decision === "THROTTLE") badgeClass = "bg-purple-950/80 text-purple-400 border border-purple-800/60";

                return (
                  <tr key={log.sequence_number} className="hover:bg-[#1c2128] transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-white">#{log.sequence_number}</td>
                    <td className="py-3 px-3 text-gray-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-3 font-medium text-white">{log.agent_id}</td>
                    <td className="py-3 px-3 text-gray-400">{log.agent_role}</td>
                    <td className="py-3 px-3 font-mono text-blue-400">{log.tool_name}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeClass}`}>
                        {log.decision}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-gray-300 max-w-xs truncate" title={log.reason}>
                      {log.reason}
                    </td>
                    <td className="py-3 px-3">
                      {log.redacted_fields && log.redacted_fields.length > 0 ? (
                        <span className="text-amber-400 font-mono text-[11px]">
                          {log.redacted_fields.join(', ')}
                        </span>
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-500 text-[10px]" title={log.prev_entry_hash}>
                      {log.prev_entry_hash.substring(0, 10)}...
                    </td>
                    <td className="py-3 px-3 font-mono text-blue-400 text-[10px]" title={log.entry_hash}>
                      {log.entry_hash.substring(0, 10)}...
                    </td>
                  </tr>
                );
              })}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={10} className="text-center py-8 text-gray-500">
                    No matching audit records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
