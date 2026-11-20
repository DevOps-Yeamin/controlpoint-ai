import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  EyeOff, 
  Gauge, 
  CheckCircle2, 
  Hash, 
  ArrowUpRight,
  RefreshCw,
  Clock
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { api } from '../services/api';
import { DashboardSummary } from '../types';

export const DashboardView: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboardSummary();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const chartData = data ? [
    { name: 'Allowed', value: data.allowed_requests, color: '#10b981' },
    { name: 'Denied', value: data.denied_requests, color: '#ef4444' },
    { name: 'Redacted', value: data.redacted_requests, color: '#f59e0b' },
    { name: 'Throttled', value: data.throttled_requests, color: '#8b5cf6' },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Top Banner & Refresh */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#21262d] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security Telemetry Dashboard</h1>
          <p className="text-sm text-gray-400">
            Real-time deterministic policy enforcement and cryptographic audit status
          </p>
        </div>
        <button
          onClick={fetchDashboard}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 bg-[#161b22] hover:bg-[#21262d] text-gray-300 rounded border border-[#30363d] text-xs font-medium transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Metrics
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Requests */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
            <span>Total Evaluated</span>
            <ArrowUpRight className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{data?.total_requests ?? 0}</div>
          <span className="text-[11px] text-gray-500">All inbound agent calls</span>
        </div>

        {/* Allowed */}
        <div className="bg-[#161b22] border border-emerald-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-emerald-400 text-xs mb-1">
            <span>Allowed</span>
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">{data?.allowed_requests ?? 0}</div>
          <span className="text-[11px] text-gray-500">Fully authorized</span>
        </div>

        {/* Denied */}
        <div className="bg-[#161b22] border border-rose-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-rose-400 text-xs mb-1">
            <span>Denied</span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">{data?.denied_requests ?? 0}</div>
          <span className="text-[11px] text-gray-500">Tool execution blocked</span>
        </div>

        {/* Redacted */}
        <div className="bg-[#161b22] border border-amber-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-amber-400 text-xs mb-1">
            <span>Redacted</span>
            <EyeOff className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">{data?.redacted_requests ?? 0}</div>
          <span className="text-[11px] text-gray-500">Field-level sanitization</span>
        </div>

        {/* Throttled */}
        <div className="bg-[#161b22] border border-purple-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-purple-400 text-xs mb-1">
            <span>Throttled</span>
            <Gauge className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold text-purple-400 font-mono">{data?.throttled_requests ?? 0}</div>
          <span className="text-[11px] text-gray-500">Rate limit enforced</span>
        </div>

        {/* Hash Chain Integrity */}
        <div className="bg-[#161b22] border border-blue-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-blue-400 text-xs mb-1">
            <span>Chain Integrity</span>
            <Hash className="w-4 h-4" />
          </div>
          <div className="text-base font-bold text-white flex items-center gap-1.5 mt-1 font-mono">
            {data?.chain_integrity ? (
              <span className="text-emerald-400 flex items-center gap-1 text-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
                VERIFIED
              </span>
            ) : (
              <span className="text-rose-500 flex items-center gap-1 text-sm">
                COMPROMISED
              </span>
            )}
          </div>
          <span className="text-[11px] text-gray-500">SHA-256 tamper-evident</span>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Donut Chart */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            Decision Distribution Ratio
          </h2>
          <div className="h-64 flex items-center justify-center">
            {chartData.every(d => d.value === 0) ? (
              <div className="text-gray-500 text-sm">No telemetry records yet. Execute queries in Playground.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0d1117', borderColor: '#30363d', color: '#e6edf3', borderRadius: '6px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="flex justify-center gap-6 mt-2 text-xs">
            {chartData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-gray-400">{item.name}: <strong className="text-white">{item.value}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <Gauge className="w-4 h-4 text-indigo-400" />
            Decision Count Breakdown
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#8b949e" fontSize={12} />
                <YAxis stroke="#8b949e" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0d1117', borderColor: '#30363d', color: '#e6edf3', borderRadius: '6px' }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-500 text-center mt-2">
            Autonomous agent tool interactions inspected under active security policies
          </p>
        </div>
      </div>

      {/* Recent Security Events Feed */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            Live Security Decision Stream
          </h2>
          <span className="text-xs text-gray-400 font-mono">
            {data?.recent_events.length ?? 0} most recent events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0d1117] text-gray-400 uppercase font-mono border-b border-[#21262d]">
              <tr>
                <th className="py-2.5 px-3">Seq #</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Agent</th>
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Tool</th>
                <th className="py-2.5 px-3">Decision</th>
                <th className="py-2.5 px-3">Enforcement Reason</th>
                <th className="py-2.5 px-3 font-mono">Proof Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262d]">
              {data?.recent_events.map((ev) => {
                let badgeClass = "bg-gray-800 text-gray-300";
                if (ev.decision === "ALLOW") badgeClass = "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60";
                else if (ev.decision === "DENY") badgeClass = "bg-rose-950/80 text-rose-400 border border-rose-800/60";
                else if (ev.decision === "REDACT") badgeClass = "bg-amber-950/80 text-amber-400 border border-amber-800/60";
                else if (ev.decision === "THROTTLE") badgeClass = "bg-purple-950/80 text-purple-400 border border-purple-800/60";

                return (
                  <tr key={ev.sequence_number} className="hover:bg-[#1c2128] transition-colors">
                    <td className="py-2.5 px-3 font-mono text-gray-400">#{ev.sequence_number}</td>
                    <td className="py-2.5 px-3 text-gray-400 whitespace-nowrap">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-3 font-medium text-white">{ev.agent_id}</td>
                    <td className="py-2.5 px-3 text-gray-400">{ev.agent_role}</td>
                    <td className="py-2.5 px-3 font-mono text-blue-400">{ev.tool_name}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase ${badgeClass}`}>
                        {ev.decision}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-gray-300 max-w-xs truncate" title={ev.reason}>
                      {ev.reason}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-gray-500 text-[10px]" title={ev.entry_hash}>
                      {ev.entry_hash.substring(0, 10)}...
                    </td>
                  </tr>
                );
              })}
              {(!data?.recent_events || data.recent_events.length === 0) && (
                <tr>
                  <td colSpan={8} className="text-center py-6 text-gray-500">
                    No security enforcement events recorded yet. Go to Security Playground to simulate requests.
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
