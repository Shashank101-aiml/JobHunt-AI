import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  ClipboardList,
  Clock,
  CheckCircle,
  TrendingUp,
  FileText,
  Sparkles,
  ArrowRight,
  AlertTriangle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { applicationsApi } from '../services/applicationsApi';
import { jobsApi } from '../services/jobsApi';
import { Application, Job, DashboardStats } from '../types';
import { StatusBadge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { extractErrorMessage } from '../lib/api';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentApps, setRecentApps] = useState<Application[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      setError(null);
      try {
        const [statsData, appsData, jobsData] = await Promise.all([
          applicationsApi.getDashboardStats(),
          applicationsApi.listApplications({ limit: 5 }),
          jobsApi.listJobs({ limit: 5 }),
        ]);
        setStats(statsData);
        setRecentApps(appsData.items);
        setRecentJobs(jobsData.items);
      } catch (err) {
        setError(extractErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading live dashboard analytics..." size="lg" className="min-h-[50vh]" />;
  }

  const chartData = stats?.status_distribution
    ? Object.entries(stats.status_distribution).map(([status, count]) => ({
        name: status.replace(/_/g, ' '),
        count,
      }))
    : [];

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6'];

  return (
    <div className="space-y-8">
      {/* Welcome Banner & Quick Actions */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-indigo-950 rounded-2xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
            Real-World AI Agentic Pipeline
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold mt-3 mb-2 tracking-tight">
            AI Job Search & Application Command Center
          </h1>
          <p className="text-indigo-200 text-sm leading-relaxed mb-6">
            Ingest candidate resumes, retrieve dense vector matches via ChromaDB, evaluate authentic ATS compatibility,
            and manage verified application submissions with human-in-the-loop oversight.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate('/resumes')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white text-indigo-900 rounded-xl font-semibold text-sm hover:bg-indigo-50 transition-colors shadow-sm"
            >
              <FileText className="w-4 h-4 text-indigo-600" />
              <span>Upload Resume</span>
            </button>
            <button
              onClick={() => navigate('/jobs')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-700/80 text-white rounded-xl font-medium text-sm hover:bg-indigo-700 border border-indigo-500/50 transition-colors"
            >
              <Briefcase className="w-4 h-4 text-indigo-300" />
              <span>Discover Jobs</span>
            </button>
            <button
              onClick={() => navigate('/match')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl font-medium text-sm hover:bg-indigo-500 transition-colors shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Evaluate Match & ATS</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div>
            <p className="font-semibold">Failed to fetch dashboard metrics</p>
            <p className="text-rose-600 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Primary KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Jobs Ingested</span>
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900">{stats?.total_jobs ?? 0}</span>
            <p className="text-[11px] text-slate-400 mt-0.5">Stored in PostgreSQL / SQLite</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Tracked</span>
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <ClipboardList className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900">{stats?.total_applications ?? 0}</span>
            <p className="text-[11px] text-slate-400 mt-0.5">Applications lifecycle history</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Awaiting Review</span>
            <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-amber-600">{stats?.awaiting_review ?? 0}</span>
            <p className="text-[11px] text-slate-400 mt-0.5">Requires candidate review / action</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Submitted</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-600">{stats?.submitted ?? 0}</span>
            <p className="text-[11px] text-slate-400 mt-0.5">Verified portal / email delivery</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Avg ATS Score</span>
            <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-purple-600">
              {stats?.average_match_score ? `${stats.average_match_score}%` : 'N/A'}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">Heuristic & semantic weights</p>
          </div>
        </div>
      </div>

      {/* Charts & Status Breakdown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Application Pipeline Status Distribution</h2>
              <p className="text-xs text-slate-500">Live counts across workflow stages</p>
            </div>
          </div>
          {chartData.length > 0 ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-sm">
              <ClipboardList className="w-8 h-8 mb-2 opacity-50" />
              <span>No application statuses to display yet.</span>
            </div>
          )}
        </div>

        {/* Operational Guardrails Card */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-2">Operational Integrity Rules</h2>
            <p className="text-xs text-slate-500 mb-4">
              Our backend enforces honest data flows without simulated statuses or phantom submissions.
            </p>
            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>No Phantom Submissions:</strong> Portal applications require explicit candidate verification
                  before moving to <code>submitted</code>.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Anti-Hallucination Guardrails:</strong> Resume tailoring preserves genuine candidate
                  history without fabricating employment or credentials.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Respects Site Limits:</strong> Public job APIs (Greenhouse/Lever) are supported; restricted
                  sites (LinkedIn) guide users to manual entry.
                </span>
              </li>
            </ul>
          </div>
          <div className="pt-4 border-t border-slate-100 mt-4">
            <button
              onClick={() => navigate('/settings')}
              className="text-xs text-indigo-600 font-semibold hover:text-indigo-800 flex items-center gap-1"
            >
              <span>View System & Vector Store Health</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Recent Applications & Recent Jobs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Applications */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">Recent Applications</h2>
            <button
              onClick={() => navigate('/applications')}
              className="text-xs text-indigo-600 font-medium hover:text-indigo-800 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {recentApps.length > 0 ? (
              recentApps.map((app) => (
                <div
                  key={app.id}
                  onClick={() => navigate(`/applications/${app.id}/review`)}
                  className="p-4 hover:bg-slate-50 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <div className="min-w-0 pr-4">
                    <p className="text-sm font-semibold text-slate-900 truncate">
                      {app.job_title || 'Software Engineer'}
                    </p>
                    <p className="text-xs text-slate-500 truncate mt-0.5">
                      {app.company || 'Not specified'} • Match:{' '}
                      <strong className="text-slate-700">{app.ats_score ? `${app.ats_score}%` : 'Pending'}</strong>
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={app.status} />
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                No applications tracked yet. Start by matching a resume to a job!
              </div>
            )}
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">Recent Ingested Jobs</h2>
            <button
              onClick={() => navigate('/jobs')}
              className="text-xs text-indigo-600 font-medium hover:text-indigo-800 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {recentJobs.length > 0 ? (
              recentJobs.map((job) => (
                <div
                  key={job.id}
                  onClick={() => navigate(`/match?job_id=${job.id}`)}
                  className="p-4 hover:bg-slate-50 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <div className="min-w-0 pr-4">
                    <p className="text-sm font-semibold text-slate-900 truncate">{job.title}</p>
                    <p className="text-xs text-slate-500 truncate mt-0.5">
                      {job.company || 'Unknown Company'} • {job.location || 'Remote / Unspecified'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                      {job.source}
                    </span>
                    <button
                      type="button"
                      className="p-1 rounded text-indigo-600 hover:bg-indigo-50"
                      title="Match against active resume"
                    >
                      <Sparkles className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                No jobs stored yet. Use the Job Discovery tool to add jobs!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
