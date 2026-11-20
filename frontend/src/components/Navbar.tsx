import React from 'react';
import { 
  ShieldCheck, 
  Terminal, 
  Bot, 
  Lock, 
  FileText, 
  Activity, 
  Layers
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, systemHealthy }) => {
  const navItems = [
    { id: 'dashboard', label: 'Security Dashboard', icon: Activity },
    { id: 'playground', label: 'Security Playground', icon: Terminal },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'policies', label: 'Policies', icon: Lock },
    { id: 'audit', label: 'Audit Logs', icon: FileText },
    { id: 'benchmarks', label: 'Evaluation & Benchmarks', icon: ShieldCheck },
    { id: 'nlip', label: 'NLIP Protocol', icon: Layers },
  ];

  return (
    <header className="border-b border-[#21262d] bg-[#0d1117] sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Identity */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white">ControlPoint-AI</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700/50">
                  Type-3 Security
                </span>
              </div>
              <p className="text-xs text-gray-400">IndustrySphere AI • <span className="text-gray-300 italic">Control What Your AI Agents Can Do.</span></p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-[#161b22]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Health indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#161b22] border border-[#30363d] text-xs">
            <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-gray-300 font-mono">Policy Engine Online</span>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      <div className="md:hidden border-t border-[#21262d] px-2 py-2 flex overflow-x-auto gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs whitespace-nowrap ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 bg-[#161b22]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
