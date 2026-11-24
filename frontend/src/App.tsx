import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { PlaygroundView } from './components/PlaygroundView';
import { AgentsView } from './components/AgentsView';
import { PoliciesView } from './components/PoliciesView';
import { AuditLogsView } from './components/AuditLogsView';
import { BenchmarkView } from './components/BenchmarkView';
import { NLIPView } from './components/NLIPView';
import { api } from './services/api';
import { Shield, ExternalLink } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [systemHealthy, setSystemHealthy] = useState<boolean>(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        setSystemHealthy(res.status === 'healthy');
      } catch (err) {
        setSystemHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0b0f17] text-[#e6edf3] flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealthy={systemHealthy}
      />

      {/* Main Content View */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'playground' && <PlaygroundView />}
        {activeTab === 'agents' && <AgentsView />}
        {activeTab === 'policies' && <PoliciesView />}
        {activeTab === 'audit' && <AuditLogsView />}
        {activeTab === 'benchmarks' && <BenchmarkView />}
        {activeTab === 'nlip' && <NLIPView />}
      </main>

      {/* Enterprise Cyber Security Footer */}
      <footer className="border-t border-[#21262d] bg-[#0d1117] py-6 text-xs text-gray-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <Shield className="w-4 h-4 text-blue-500 flex-shrink-0" />
            <span className="font-bold text-white">ControlPoint-AI</span>
            <span className="text-gray-600">—</span>
            <span className="font-semibold text-white">IndustrySphere AI</span>
            <span className="text-gray-500">•</span>
            <span className="italic text-gray-300">Control What Your AI Agents Can Do.</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-gray-500 font-mono text-[11px]">
            <span>Type-3 Security Extension</span>
            <span>•</span>
            <span>Apache-2.0 License</span>
            <span>•</span>
            <a 
              href="/docs" 
              target="_blank" 
              rel="noreferrer"
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              OpenAPI Docs <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
