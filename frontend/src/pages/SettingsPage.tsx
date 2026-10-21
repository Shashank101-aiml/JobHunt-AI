import React, { useEffect, useState } from 'react';
import {
  Database,
  Layers,
  Cpu,
  Mail,
  Shield,
  RefreshCw,
  ExternalLink,
  AlertTriangle,
} from 'lucide-react';
import { healthApi } from '../services/healthApi';
import { HealthStatus } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { StatusBadge } from '../components/ui/Badge';
import { extractErrorMessage } from '../lib/api';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setRefreshing(true);
      setError(null);
      const data = await healthApi.getHealth();
      setHealth(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Health & Settings</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time diagnostics for Database, ChromaDB Vector Store, LLM Provider, and Subsystem Integrations.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchHealth}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold shadow-2xs transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Diagnostics</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Diagnostic Connection Error</p>
            <p className="text-rose-600 mt-0.5 whitespace-pre-wrap">{error}</p>
          </div>
        </div>
      )}

      {loading ? (
        <LoadingSpinner message="Checking backend diagnostics..." size="lg" className="min-h-[40vh]" />
      ) : (
        <div className="space-y-6">
          {/* Main Health Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Database Health */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Database Layer</span>
                  <Database className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-base font-bold text-slate-900 capitalize">
                  {health?.database.startsWith('ok') ? 'Connected' : 'Degraded'}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {health?.database.startsWith('ok')
                    ? 'PostgreSQL / Local SQLite Resilient Engine'
                    : health?.database}
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">ORM / Migrations</span>
                <StatusBadge status={health?.database.startsWith('ok') ? 'ok' : 'unhealthy'} />
              </div>
            </div>

            {/* Vector Store Health */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Vector Store</span>
                  <Layers className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-base font-bold text-slate-900">ChromaDB</div>
                <p className="text-xs text-slate-500 mt-1">
                  Local ONNX 384d Dense Embeddings (<code>all-MiniLM-L6-v2</code>)
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">{health?.vector_store || 'Offline'}</span>
                <StatusBadge status={health?.vector_store.startsWith('ok') ? 'ok' : 'unhealthy'} />
              </div>
            </div>

            {/* LLM Provider Status */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase">LLM Provider</span>
                  <Cpu className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-base font-bold text-slate-900 capitalize">
                  {health?.llm_provider.provider || 'Anthropic'}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Model: <code className="text-slate-800">{health?.llm_provider.model || 'Default'}</code>
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  {health?.llm_provider.is_configured ? 'API Key Active' : 'Heuristic Mode'}
                </span>
                <StatusBadge status={health?.llm_provider.is_configured ? 'active' : 'draft'} />
              </div>
            </div>

            {/* SMTP Email Service */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Email Service</span>
                  <Mail className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-base font-bold text-slate-900">
                  {health?.email_service.enabled ? 'Enabled' : 'Disabled'}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Host: <code className="text-slate-800">{health?.email_service.smtp_host || 'None'}</code>
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">Direct SMTP</span>
                <StatusBadge status={health?.email_service.enabled ? 'active' : 'draft'} />
              </div>
            </div>
          </div>

          {/* Job Source Architecture & Policies Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Supported Job Sources & Boundaries</h2>
              <p className="text-xs text-slate-500">
                Official integrations, authorized APIs, and ethical scraping policies enforced by the backend.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3">Source Name</th>
                    <th className="px-6 py-3">Integration Method</th>
                    <th className="px-6 py-3">Access Policy</th>
                    <th className="px-6 py-3">Operational Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="px-6 py-3.5 font-bold text-slate-900">Greenhouse Job Boards</td>
                    <td className="px-6 py-3.5 text-slate-600">Official REST API (<code>boards-api.greenhouse.io</code>)</td>
                    <td className="px-6 py-3.5 text-emerald-700 font-medium">Permitted Public API</td>
                    <td className="px-6 py-3.5"><StatusBadge status="active" /></td>
                  </tr>
                  <tr>
                    <td className="px-6 py-3.5 font-bold text-slate-900">Lever Postings</td>
                    <td className="px-6 py-3.5 text-slate-600">Official REST API (<code>api.lever.co/v0/postings</code>)</td>
                    <td className="px-6 py-3.5 text-emerald-700 font-medium">Permitted Public API</td>
                    <td className="px-6 py-3.5"><StatusBadge status="active" /></td>
                  </tr>
                  <tr>
                    <td className="px-6 py-3.5 font-bold text-slate-900">Direct URL Scraping</td>
                    <td className="px-6 py-3.5 text-slate-600">HTTPX + BeautifulSoup4 parser</td>
                    <td className="px-6 py-3.5 text-slate-600">Permitted HTML Web Pages</td>
                    <td className="px-6 py-3.5"><StatusBadge status="active" /></td>
                  </tr>
                  <tr>
                    <td className="px-6 py-3.5 font-bold text-slate-900">Manual Job Description</td>
                    <td className="px-6 py-3.5 text-slate-600">Direct Text Input & NLP Normalization</td>
                    <td className="px-6 py-3.5 text-emerald-700 font-medium">Universal (Offline / Portal)</td>
                    <td className="px-6 py-3.5"><StatusBadge status="active" /></td>
                  </tr>
                  <tr className="bg-rose-50/20">
                    <td className="px-6 py-3.5 font-bold text-rose-900">LinkedIn / Indeed / Restricted</td>
                    <td className="px-6 py-3.5 text-slate-600">Blocked by design (<code>RestrictedJobSourceError</code>)</td>
                    <td className="px-6 py-3.5 text-rose-700 font-medium">Requires Manual Input Form</td>
                    <td className="px-6 py-3.5"><StatusBadge status="rejected" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Configuration Instructions Box */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">Backend Configuration Guide</h2>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Environment variables configure external AI providers and SMTP delivery without exposing secrets to the browser.
              Modify <code>.env</code> in the project root to update credentials:
            </p>

            <div className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs overflow-x-auto leading-relaxed">
              <p className="text-slate-400"># LLM Provider Configuration</p>
              <p>LLM_PROVIDER=anthropic</p>
              <p>ANTHROPIC_API_KEY=sk-ant-api03-...</p>
              <p>ANTHROPIC_MODEL=claude-3-5-sonnet-20241022</p>
              <br />
              <p className="text-slate-400"># Optional SMTP Email Configuration</p>
              <p>EMAIL_ENABLED=true</p>
              <p>SMTP_HOST=smtp.gmail.com</p>
              <p>SMTP_PORT=587</p>
              <p>SMTP_USERNAME=your-email@gmail.com</p>
              <p>SMTP_PASSWORD=your-app-password</p>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500">
                Frontend running at <code>http://localhost:5173</code> connecting to <code>http://localhost:8000</code>.
              </span>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="text-xs text-indigo-600 font-semibold hover:underline flex items-center gap-1"
              >
                <span>Interactive Swagger Docs</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
