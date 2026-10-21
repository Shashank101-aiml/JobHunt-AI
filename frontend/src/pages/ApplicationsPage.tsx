import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList,
  Search,
  Filter,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  ArrowRight,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { applicationsApi } from '../services/applicationsApi';
import { Application } from '../types';
import { StatusBadge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { extractErrorMessage } from '../lib/api';

export const ApplicationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<Application[]>([]);
  const [totalApps, setTotalApps] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [page, setPage] = useState(0);
  const limit = 10;

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await applicationsApi.listApplications({
        search: search.trim() || undefined,
        status: selectedStatus || undefined,
        skip: page * limit,
        limit,
      });
      setApplications(data.items);
      setTotalApps(data.total);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [page, selectedStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchApplications();
  };

  const handleStatusChange = async (appId: number, newStatus: string) => {
    try {
      await applicationsApi.updateApplicationStatus(appId, newStatus);
      await fetchApplications();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const totalPages = Math.ceil(totalApps / limit);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Application Tracker</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track and manage your applications across verified operational statuses with full event audit logs.
          </p>
        </div>

        <button
          onClick={() => navigate('/tailor')}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4 text-amber-300" />
          <span>New Application / Tailor</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Application Tracker Error</p>
            <p className="text-rose-600 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search job title or company name..."
            className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          />
        </form>

        <div className="relative w-full sm:w-60">
          <Filter className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setPage(0);
            }}
            className="w-full pl-10 pr-8 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white font-medium"
          >
            <option value="">All Statuses ({totalApps})</option>
            <option value="draft">Draft</option>
            <option value="ready_for_review">Ready for Review</option>
            <option value="requires_manual_action">Requires Manual Action</option>
            <option value="submitted">Submitted</option>
            <option value="interviewing">Interviewing</option>
            <option value="rejected">Rejected</option>
            <option value="offer">Offer Received</option>
          </select>
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner message="Loading applications..." size="md" />
        ) : applications.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No Applications Tracked"
            description="You have not tracked any applications matching this filter yet."
            actionText="Start New Application"
            onAction={() => navigate('/tailor')}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Target Role & Company</th>
                  <th className="px-6 py-3.5">ATS Match</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Submitted / Created</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 text-sm">{app.job_title || 'Software Engineer'}</div>
                      <div className="text-slate-500 text-xs mt-0.5">
                        {app.company || 'Not specified'}
                        {app.job_url && !app.job_url.startsWith('manual-') && (
                          <a
                            href={app.job_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-0.5 ml-2 text-indigo-600 hover:underline"
                          >
                            <span>Link</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                      {app.notes && (
                        <p className="text-[11px] text-slate-400 italic mt-1 truncate max-w-xs">{app.notes}</p>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      {app.ats_score ? (
                        <span className="font-bold text-slate-800 text-sm">{app.ats_score}%</span>
                      ) : (
                        <span className="text-slate-400">Pending</span>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={app.status} />
                        <select
                          value={app.status}
                          onChange={(e) => handleStatusChange(app.id, e.target.value)}
                          className="text-[11px] border border-slate-200 rounded px-1.5 py-0.5 bg-white text-slate-600 focus:outline-none"
                        >
                          <option value="draft">draft</option>
                          <option value="ready_for_review">ready_for_review</option>
                          <option value="requires_manual_action">requires_manual_action</option>
                          <option value="submitted">submitted</option>
                          <option value="interviewing">interviewing</option>
                          <option value="rejected">rejected</option>
                          <option value="offer">offer</option>
                        </select>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-slate-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{new Date(app.created_at).toLocaleDateString()}</span>
                      </div>
                      {app.submitted_at && (
                        <div className="text-[11px] text-emerald-600 font-medium mt-0.5">
                          Submitted: {new Date(app.submitted_at).toLocaleDateString()}
                        </div>
                      )}
                    </td>

                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {app.tailored_resume_text && (
                          <button
                            type="button"
                            onClick={() => applicationsApi.downloadTailoredDocx(app.id)}
                            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600"
                            title="Download DOCX"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => navigate(`/applications/${app.id}/review`)}
                          className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs flex items-center gap-1"
                        >
                          <span>Review & Submit</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {page * limit + 1} to {Math.min((page + 1) * limit, totalApps)} of {totalApps} applications
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(p - 1, 0))}
                className="p-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span>
                Page {page + 1} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
                className="p-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
