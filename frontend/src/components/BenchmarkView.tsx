import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Activity, 
  Gauge, 
  FileSpreadsheet,
  FileCode,
  Layers,
  TrendingUp,
  Lock,
  ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import { BenchmarkReport } from '../types';

export const BenchmarkView: React.FC = () => {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runBenchmarkSuite = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await api.runBenchmark();
      setReport(res);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Benchmark execution failed');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    runBenchmarkSuite();
  }, []);

  const handleExportJSON = () => {
    window.open('/api/benchmark/export?format=json', '_blank');
  };

  const handleExportCSV = () => {
    window.open('/api/benchmark/export?format=csv', '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#21262d] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security Evaluation & Benchmarking</h1>
          <p className="text-sm text-gray-400">
            Automated test harness executing 15 synthetic HR security attack scenarios across three baseline architectures
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#161b22] hover:bg-[#21262d] text-gray-300 rounded border border-[#30363d] text-xs font-medium transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            Export CSV
          </button>
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#161b22] hover:bg-[#21262d] text-gray-300 rounded border border-[#30363d] text-xs font-medium transition"
          >
            <FileCode className="w-3.5 h-3.5 text-blue-400" />
            Export JSON
          </button>
          <button
            onClick={runBenchmarkSuite}
            disabled={running}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition shadow-md shadow-blue-500/20"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${running ? 'animate-pulse' : ''}`} />
            {running ? 'Executing Suite...' : 'Run Benchmark Suite'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1 flex items-center justify-between">
            <span>Attack Prevention Rate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {report?.prevention_rate_pct ?? 0}%
          </div>
          <span className="text-[11px] text-gray-500">Denied, redacted, or throttled</span>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1 flex items-center justify-between">
            <span>Policy Accuracy</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {report?.accuracy_rate_pct ?? 0}%
          </div>
          <span className="text-[11px] text-gray-500">
            {report?.passed_scenarios ?? 0} of {report?.total_scenarios ?? 0} scenarios passed
          </span>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1 flex items-center justify-between">
            <span>P50 Decision Latency</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400 font-mono">
            {report?.p50_latency_ms ?? 0} ms
          </div>
          <span className="text-[11px] text-gray-500">Median pipeline latency</span>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <div className="text-xs text-gray-400 mb-1 flex items-center justify-between">
            <span>P95 Tail Latency</span>
            <Gauge className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-400 font-mono">
            {report?.p95_latency_ms ?? 0} ms
          </div>
          <span className="text-[11px] text-gray-500">95th percentile under evaluation</span>
        </div>
      </div>

      {/* Tri-Baseline Comparison Card */}
      {report?.baselines && report.baselines.length > 0 && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
          <div className="p-4 border-b border-[#21262d] flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-400" />
              Comparative Tri-Baseline Evaluation (NDSS SafeOSE '27 Protocol)
            </h2>
            <span className="text-xs text-gray-400 font-mono">
              Live Comparative Analysis
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0d1117] text-gray-400 uppercase font-mono border-b border-[#21262d]">
                <tr>
                  <th className="py-3 px-3">Architecture Baseline</th>
                  <th className="py-3 px-3">Attack Success (ASR)</th>
                  <th className="py-3 px-3">Prevention (APR)</th>
                  <th className="py-3 px-3">False Positive</th>
                  <th className="py-3 px-3">P50 Latency</th>
                  <th className="py-3 px-3">Overhead</th>
                  <th className="py-3 px-3">Throughput</th>
                  <th className="py-3 px-3">Audit Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#21262d]">
                {report.baselines.map((b, i) => (
                  <tr key={i} className={`hover:bg-[#1c2128] transition-colors ${i === 2 ? 'bg-blue-950/20' : ''}`}>
                    <td className="py-3 px-3 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        {i === 2 && <span className="w-2 h-2 rounded-full bg-blue-400" />}
                        <span>{b.name}</span>
                      </div>
                      <div className="text-[10px] text-gray-400 font-normal">{b.description}</div>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold">
                      <span className={b.attack_success_rate_pct === 0 ? 'text-emerald-400' : 'text-rose-400'}>
                        {b.attack_success_rate_pct}%
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-emerald-400">
                      {b.attack_prevention_rate_pct}%
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-300">
                      {b.false_positive_rate_pct}%
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-300">
                      {b.p50_latency_ms} ms
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-400">
                      +{b.enforcement_overhead_ms} ms
                    </td>
                    <td className="py-3 px-3 font-mono text-indigo-300">
                      {b.throughput_rps} RPS
                    </td>
                    <td className="py-3 px-3 font-mono text-xs">
                      {b.audit_chain_verified ? (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> SHA-256 Verified
                        </span>
                      ) : (
                        <span className="text-gray-500">None</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 15 Scenarios Execution Table */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
        <div className="p-4 border-b border-[#21262d] flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            15 Synthetic HR Security Evaluation Scenarios (Real Backend Execution)
          </h2>
          <span className="text-xs text-gray-400 font-mono">
            Last Executed: {report ? new Date(report.timestamp).toLocaleTimeString() : '—'}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0d1117] text-gray-400 uppercase font-mono border-b border-[#21262d]">
              <tr>
                <th className="py-3 px-3">#</th>
                <th className="py-3 px-3">Scenario Name</th>
                <th className="py-3 px-3">Agent</th>
                <th className="py-3 px-3">Fields</th>
                <th className="py-3 px-3">Expected</th>
                <th className="py-3 px-3">Actual Result</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Latency</th>
                <th className="py-3 px-3">Enforcement Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262d]">
              {report?.scenarios.map((sc) => {
                let badgeClass = "bg-gray-800 text-gray-300";
                if (sc.actual_decision === "ALLOW") badgeClass = "bg-emerald-950/80 text-emerald-400 border border-emerald-800/60";
                else if (sc.actual_decision === "DENY") badgeClass = "bg-rose-950/80 text-rose-400 border border-rose-800/60";
                else if (sc.actual_decision === "REDACT") badgeClass = "bg-amber-950/80 text-amber-400 border border-amber-800/60";
                else if (sc.actual_decision === "THROTTLE") badgeClass = "bg-purple-950/80 text-purple-400 border border-purple-800/60";

                return (
                  <tr key={sc.scenario_id} className="hover:bg-[#1c2128] transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-gray-400">
                      #{sc.scenario_id}
                    </td>
                    <td className="py-3 px-3 font-medium text-white max-w-xs">
                      {sc.name}
                    </td>
                    <td className="py-3 px-3 font-mono text-blue-400">
                      {sc.agent_id}
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-300 text-[11px]">
                      {sc.requested_fields.length > 0 ? sc.requested_fields.join(", ") : "—"}
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-400 font-bold">
                      {sc.expected_decision}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeClass}`}>
                        {sc.actual_decision}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {sc.passed ? (
                        <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          PASS
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-rose-400 font-semibold text-[11px]">
                          <XCircle className="w-3.5 h-3.5" />
                          FAIL
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono text-gray-400 text-[11px]">
                      {sc.latency_ms} ms
                    </td>
                    <td className="py-3 px-3 text-gray-400 max-w-sm truncate" title={sc.details}>
                      {sc.details}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
