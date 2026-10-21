import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Search,
  PlusCircle,
  Globe,
  Sparkles,
  MapPin,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Eye,
  Info,
} from 'lucide-react';
import { jobsApi } from '../services/jobsApi';
import { Job } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { Modal } from '../components/ui/Modal';
import { extractErrorMessage } from '../lib/api';

export const JobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Search & Pagination
  const [search, setSearch] = useState('');
  const [location, setLocation] = useState('');
  const [page, setPage] = useState(0);
  const limit = 10;

  // Active Tab: 'browse' | 'manual' | 'scrape'
  const [activeTab, setActiveTab] = useState<'browse' | 'manual' | 'scrape'>('browse');

  // Manual Form
  const [manualTitle, setManualTitle] = useState('');
  const [manualCompany, setManualCompany] = useState('');
  const [manualLocation, setManualLocation] = useState('');
  const [manualEmpType, setManualEmpType] = useState('Full-Time');
  const [manualText, setManualText] = useState('');
  const [manualUrl, setManualUrl] = useState('');

  // Scrape Form
  const [scrapeUrl, setScrapeUrl] = useState('');

  // Selected Job for Detail Modal
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await jobsApi.listJobs({
        search: search.trim() || undefined,
        location: location.trim() || undefined,
        skip: page * limit,
        limit,
      });
      setJobs(data.items);
      setTotalJobs(data.total);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchJobs();
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualText || manualText.trim().length < 20) {
      setError('Job description text must be at least 20 characters long.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);
      const newJob = await jobsApi.createManualJob({
        title: manualTitle.trim() || undefined,
        company: manualCompany.trim() || undefined,
        location: manualLocation.trim() || undefined,
        employment_type: manualEmpType,
        description_text: manualText.trim(),
        source_url: manualUrl.trim() || undefined,
      });
      setSuccessMsg(`Successfully saved and normalized job: ${newJob.title}`);
      setManualTitle('');
      setManualCompany('');
      setManualLocation('');
      setManualText('');
      setManualUrl('');
      setActiveTab('browse');
      await fetchJobs();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleScrapeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scrapeUrl || !scrapeUrl.trim().startsWith('http')) {
      setError('Please provide a valid HTTP or HTTPS job posting URL.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);
      const scrapedJob = await jobsApi.scrapeJob(scrapeUrl.trim());
      setSuccessMsg(`Successfully scraped and parsed job: ${scrapedJob.title} at ${scrapedJob.company || 'Company'}`);
      setScrapeUrl('');
      setActiveTab('browse');
      await fetchJobs();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const totalPages = Math.ceil(totalJobs / limit);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Job Discovery & Ingestion</h1>
          <p className="text-sm text-slate-500 mt-1">
            Ingest jobs from official Greenhouse/Lever APIs, direct permitted URLs, or manual input.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl">
          <button
            type="button"
            onClick={() => setActiveTab('browse')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'browse' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Browse Jobs ({totalJobs})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('manual')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'manual' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Manual Input</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('scrape')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'scrape' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Scrape URL</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Job Ingestion Error</p>
            <p className="text-rose-600 mt-0.5 whitespace-pre-wrap">{error}</p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3 text-emerald-800 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">{successMsg}</p>
          </div>
        </div>
      )}

      {/* Tab: Manual Job Entry Form */}
      {activeTab === 'manual' && (
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm max-w-3xl">
          <div className="flex items-center gap-2 mb-4">
            <PlusCircle className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-bold text-slate-900">Manually Add Job Description</h2>
          </div>
          <p className="text-xs text-slate-500 mb-6">
            Use manual entry when targeting job boards with CAPTCHAs, login walls (e.g. LinkedIn), or internal company postings.
          </p>

          <form onSubmit={handleManualSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Job Title</label>
                <input
                  type="text"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  placeholder="e.g. Senior Backend Engineer (or leave blank to auto-detect)"
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Company Name</label>
                <input
                  type="text"
                  value={manualCompany}
                  onChange={(e) => setManualCompany(e.target.value)}
                  placeholder="e.g. Stripe, Acme Corp"
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Location / Work Model</label>
                <input
                  type="text"
                  value={manualLocation}
                  onChange={(e) => setManualLocation(e.target.value)}
                  placeholder="e.g. Remote, San Francisco, Hybrid"
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Employment Type</label>
                <select
                  value={manualEmpType}
                  onChange={(e) => setManualEmpType(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  <option value="Full-Time">Full-Time</option>
                  <option value="Part-Time">Part-Time</option>
                  <option value="Contract">Contract</option>
                  <option value="Internship">Internship</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Source URL (Optional)</label>
              <input
                type="url"
                value={manualUrl}
                onChange={(e) => setManualUrl(e.target.value)}
                placeholder="https://jobs.example.com/posting/123"
                className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Job Description Text <span className="text-rose-500">*</span>
              </label>
              <textarea
                rows={8}
                required
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                placeholder="Paste the full job posting requirements, responsibilities, qualifications, and company details..."
                className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-sans"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setActiveTab('browse')}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {submitting ? 'Normalizing JD...' : 'Save & Normalize Job'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab: URL Scraper Form */}
      {activeTab === 'scrape' && (
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm max-w-2xl">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-bold text-slate-900">Scrape Job from Permitted URL</h2>
          </div>

          <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100 mb-6 text-xs text-indigo-900 space-y-1.5">
            <p className="font-semibold flex items-center gap-1.5">
              <Info className="w-4 h-4 text-indigo-600" />
              Supported Official Integrations:
            </p>
            <ul className="list-disc list-inside text-indigo-800 space-y-0.5 pl-1">
              <li>Greenhouse Job Boards (e.g. <code>boards.greenhouse.io/company/jobs/123</code>)</li>
              <li>Lever Job Postings (e.g. <code>jobs.lever.co/company/abc-123</code>)</li>
              <li>Direct public job descriptions permitting automated access.</li>
            </ul>
            <p className="text-slate-500 pt-1">
              <em>Note: LinkedIn, Indeed, and login-protected portals are intentionally blocked to respect terms of service. Use Manual Input for those sites.</em>
            </p>
          </div>

          <form onSubmit={handleScrapeSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Job Posting URL <span className="text-rose-500">*</span>
              </label>
              <input
                type="url"
                required
                value={scrapeUrl}
                onChange={(e) => setScrapeUrl(e.target.value)}
                placeholder="https://boards.greenhouse.io/airbnb/jobs/12345"
                className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-xs"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setActiveTab('browse')}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {submitting ? 'Retrieving & Parsing...' : 'Retrieve Job Posting'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab: Browse Jobs */}
      {activeTab === 'browse' && (
        <div className="space-y-4">
          {/* Search & Filter Bar */}
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search job title or company name..."
                className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>
            <div className="relative w-full sm:w-64">
              <MapPin className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Filter location or remote..."
                className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-semibold hover:bg-slate-800 transition-colors"
            >
              Filter
            </button>
          </form>

          {/* Job Listings Grid */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {loading ? (
              <LoadingSpinner message="Searching jobs..." size="md" />
            ) : jobs.length === 0 ? (
              <EmptyState
                icon={Briefcase}
                title="No Jobs Found"
                description="No matching jobs found in the database. Add a job manually or scrape a public posting URL."
                actionText="Add Job Manually"
                onAction={() => setActiveTab('manual')}
              />
            ) : (
              <div className="divide-y divide-slate-100">
                {jobs.map((job) => {
                  const structured = job.structured_jd;
                  const reqSkills = structured?.required_skills || [];

                  return (
                    <div key={job.id} className="p-6 hover:bg-slate-50/60 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-base font-bold text-slate-900">{job.title}</h3>
                            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700">
                              {job.company || 'Company Not Specified'}
                            </span>
                            <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                              {job.source}
                            </span>
                          </div>

                          {/* Metadata row */}
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-2">
                            {job.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                                {job.location}
                              </span>
                            )}
                            {job.employment_type && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3.5 h-3.5 text-slate-400" />
                                {job.employment_type}
                              </span>
                            )}
                            {structured?.min_years_experience && (
                              <span>Min {structured.min_years_experience}+ yrs exp</span>
                            )}
                            {structured?.salary_range && (
                              <span className="flex items-center gap-1 text-emerald-700 font-medium">
                                <DollarSign className="w-3.5 h-3.5" />
                                {structured.salary_range}
                              </span>
                            )}
                          </div>

                          {/* Required Skills Badges */}
                          {reqSkills.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              <span className="text-[11px] font-semibold text-slate-400 mr-1 self-center">
                                Required:
                              </span>
                              {reqSkills.slice(0, 6).map((skill, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 text-xs bg-slate-100 text-slate-700 rounded-md font-medium"
                                >
                                  {skill}
                                </span>
                              ))}
                              {reqSkills.length > 6 && (
                                <span className="text-xs text-slate-400 self-center">
                                  +{reqSkills.length - 6} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2 self-end sm:self-start flex-shrink-0">
                          <button
                            type="button"
                            onClick={() => setSelectedJob(job)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 shadow-2xs transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Details</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => navigate(`/match?job_id=${job.id}`)}
                            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition-colors"
                          >
                            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                            <span>Evaluate ATS</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="px-6 py-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>
                  Showing {page * limit + 1} to {Math.min((page + 1) * limit, totalJobs)} of {totalJobs} jobs
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
      )}

      {/* Job Details Modal */}
      <Modal
        isOpen={selectedJob !== null}
        onClose={() => setSelectedJob(null)}
        title={selectedJob ? `${selectedJob.title} — ${selectedJob.company || 'Company'}` : 'Job Details'}
        maxWidth="2xl"
      >
        {selectedJob && (
          <div className="space-y-6 text-sm text-slate-700">
            {/* Metadata Pills */}
            <div className="flex flex-wrap gap-2 text-xs">
              {selectedJob.location && (
                <span className="px-2.5 py-1 bg-slate-100 rounded-lg text-slate-700 font-medium">
                  {selectedJob.location}
                </span>
              )}
              {selectedJob.employment_type && (
                <span className="px-2.5 py-1 bg-slate-100 rounded-lg text-slate-700 font-medium">
                  {selectedJob.employment_type}
                </span>
              )}
              {selectedJob.structured_jd?.min_years_experience && (
                <span className="px-2.5 py-1 bg-slate-100 rounded-lg text-slate-700 font-medium">
                  {selectedJob.structured_jd.min_years_experience}+ Years Experience
                </span>
              )}
              {selectedJob.structured_jd?.salary_range && (
                <span className="px-2.5 py-1 bg-emerald-50 text-emerald-800 rounded-lg font-semibold">
                  Salary: {selectedJob.structured_jd.salary_range}
                </span>
              )}
            </div>

            {/* Extracted Skills */}
            <div className="space-y-2">
              <h4 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">Required Skills:</h4>
              <div className="flex flex-wrap gap-1.5">
                {selectedJob.structured_jd?.required_skills?.map((s, idx) => (
                  <span key={idx} className="px-2.5 py-1 text-xs bg-indigo-50 text-indigo-700 rounded-md font-medium">
                    {s}
                  </span>
                )) || <span className="text-slate-400 text-xs">None explicitly extracted.</span>}
              </div>
            </div>

            {/* Raw Description Viewer */}
            <div className="space-y-2">
              <h4 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">Full Job Description:</h4>
              <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl max-h-72 overflow-y-auto whitespace-pre-wrap text-xs leading-relaxed font-sans text-slate-800">
                {selectedJob.raw_description}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedJob(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  const id = selectedJob.id;
                  setSelectedJob(null);
                  navigate(`/match?job_id=${id}`);
                }}
                className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Match With Resume</span>
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
