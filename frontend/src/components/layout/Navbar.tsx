import React, { useEffect, useState } from 'react';
import { Menu, ExternalLink } from 'lucide-react';
import { healthApi } from '../../services/healthApi';
import { HealthStatus } from '../../types';

interface NavbarProps {
  onToggleMobile: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobile }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isDegraded, setIsDegraded] = useState(false);

  useEffect(() => {
    healthApi
      .getHealth()
      .then((data) => {
        setHealth(data);
        setIsDegraded(data.status !== 'ok');
      })
      .catch(() => {
        setIsDegraded(true);
      });
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleMobile}
          className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="hidden sm:flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
            Localhost Studio
          </span>
          <span className="text-xs text-slate-400">FastAPI + LangGraph + ChromaDB</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend Connectivity Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              health && !isDegraded ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
            }`}
          />
          <span className="font-medium text-slate-700">
            {health && !isDegraded ? 'API Online' : 'API Offline / Error'}
          </span>
          {health?.llm_provider && (
            <span className="text-slate-400 border-l border-slate-200 pl-2 hidden md:inline">
              LLM: {health.llm_provider.is_configured ? health.llm_provider.provider : 'Heuristic Mode'}
            </span>
          )}
        </div>

        {/* API Docs Link */}
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-600 hover:text-indigo-600 flex items-center gap-1 font-medium transition-colors"
        >
          <span>Swagger Docs</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </header>
  );
};
