import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Terminal, 
  Bot, 
  Lock, 
  FileText, 
  Activity, 
  Layers,
  Menu,
  X
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, systemHealthy }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const navItems = [
    { id: 'dashboard', label: 'Security Dashboard', icon: Activity },
    { id: 'playground', label: 'Security Playground', icon: Terminal },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'policies', label: 'Policies', icon: Lock },
    { id: 'audit', label: 'Audit Logs', icon: FileText },
    { id: 'benchmarks', label: 'Evaluation & Benchmarks', icon: ShieldCheck },
    { id: 'nlip', label: 'NLIP Protocol', icon: Layers },
  ];

  const handleTabClick = (id: string) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="border-b border-[#21262d] bg-[#0d1117] sticky top-0 z-50">
      {/* Primary Brand & Status Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Brand Identity */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 flex-shrink-0 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white whitespace-nowrap">
                  ControlPoint-AI
                </span>
                <span className="hidden sm:inline-flex text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700/50">
                  Type-3 Security
                </span>
              </div>
              <p className="text-xs text-gray-300 truncate">
                <span className="font-semibold text-white">IndustrySphere AI</span>
                <span className="mx-1.5 text-gray-500">•</span>
                <span className="italic text-gray-300">Control What Your AI Agents Can Do.</span>
              </p>
            </div>
          </div>

          {/* Right Controls: Health Status & Mobile Toggle */}
          <div className="flex items-center gap-3 flex-shrink-0">
            {/* Health indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#161b22] border border-[#30363d] text-xs shadow-inner">
              <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-gray-300 font-mono text-[11px] hidden sm:inline">
                {systemHealthy ? 'Policy Engine Online' : 'Engine Offline'}
              </span>
            </div>

            {/* Mobile Menu Toggle Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-white hover:bg-[#161b22] border border-[#30363d] focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Desktop Secondary Navigation Bar */}
      <nav className="hidden lg:block border-t border-[#21262d] bg-[#0b0f17]/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-1 py-1.5 overflow-x-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all whitespace-nowrap focus:outline-none focus:ring-1 focus:ring-blue-500 ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/40 shadow-sm'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-[#161b22] border border-transparent'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-[#21262d] bg-[#0d1117] px-4 py-3 space-y-1.5 shadow-xl animate-fadeIn">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-md text-sm font-medium transition-colors text-left ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40'
                    : 'text-gray-300 hover:bg-[#161b22] hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
