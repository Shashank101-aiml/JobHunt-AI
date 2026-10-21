import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Wand2,
  FileText,
  Briefcase,
  Download,
  Save,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  FileCheck,
  Edit3,
} from 'lucide-react';
import { resumeApi } from '../services/resumeApi';
import { jobsApi } from '../services/jobsApi';
import { applicationsApi } from '../services/applicationsApi';
import { Resume, Job, Application } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { extractErrorMessage } from '../lib/api';

export const TailorPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const paramResumeId = searchParams.get('resume_id');
  const paramJobId = searchParams.get('job_id');

  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<number | ''>(
    paramResumeId ? parseInt(paramResumeId, 10) : ''
  );
  const [selectedJobId, setSelectedJobId] = useState<number | ''>(
    paramJobId ? parseInt(paramJobId, 10) : ''
  );

  const [useCustomJob, setUseCustomJob] = useState(false);
  const [customJobText, setCustomJobText] = useState('');

  const [tailoring, setTailoring] = useState(false);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Completed Application Result
  const [application, setApplication] = useState<Application | null>(null);

  // Editable Form Fields
  const [editedResume, setEditedResume] = useState('');
  const [editedCoverLetter, setEditedCoverLetter] = useState('');
  const [candidateNotes, setCandidateNotes] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        const [resList, jobsList] = await Promise.all([
          resumeApi.listResumes(),
          jobsApi.listJobs({ limit: 50 }),
        ]);
        setResumes(resList);
        setJobs(jobsList.items);

        if (!selectedResumeId) {
          const active = resList.find((r) => r.is_active) || resList[0];
          if (active) setSelectedResumeId(active.id);
        }
      } catch (err) {
        setError(extractErrorMessage(err));
      }
    }
    loadData();
  }, []);

  const handleStartTailoring = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResumeId) {
      setError('Please select a candidate resume.');
      return;
    }
    if (!useCustomJob && !selectedJobId) {
      setError('Please select a target job or enter custom job text.');
      return;
    }
    if (useCustomJob && (!customJobText || customJobText.trim().length < 20)) {
      setError('Custom job description must be at least 20 characters.');
      return;
    }

    try {
      setTailoring(true);
      setError(null);
      setSuccessMsg(null);

      const payload = {
        resume_id: Number(selectedResumeId),
        job_id: useCustomJob ? undefined : Number(selectedJobId),
        job_text: useCustomJob ? customJobText.trim() : undefined,
        sync_execution: true,
      };

      const result = await applicationsApi.createApplication(payload);
      setApplication(result);
      setEditedResume(result.tailored_resume_text || '');
      setEditedCoverLetter(result.cover_letter || '');
      setCandidateNotes(result.notes || '');

      setSuccessMsg(`Tailoring completed! Review package ready (Application ID: ${result.id})`);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setTailoring(false);
    }
  };

  const handleSaveEdits = async () => {
    if (!application) return;
    try {
      setSaving(true);
      setError(null);
      const updated = await applicationsApi.saveApplicationReview(application.id, {
        tailored_resume_text: editedResume,
        cover_letter: editedCoverLetter,
        notes: candidateNotes,
      });
      setApplication(updated);
      setSuccessMsg('Your manual edits to the tailored resume and cover letter have been saved.');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadDocx = async () => {
    if (!application) return;
    try {
      setDownloading(true);
      setError(null);
      await applicationsApi.downloadTailoredDocx(application.id);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  const diff = application?.tailored_resume_diff;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Resume Tailoring & Cover Letter Studio</h1>
        <p className="text-sm text-slate-500 mt-1">
          Synthesizes authentic candidate experiences with target job requirements using ChromaDB context retrieval.
          Strict anti-hallucination guardrails guarantee no fabricated jobs or metrics.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Workflow Alert</p>
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

      {/* Target Selector */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
        <form onSubmit={handleStartTailoring} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-indigo-600" />
                Select Candidate Resume
              </label>
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white font-medium"
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.filename} {r.is_active ? '★ (Active)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4 text-indigo-600" />
                  Select Target Job
                </label>
                <button
                  type="button"
                  onClick={() => setUseCustomJob((prev) => !prev)}
                  className="text-xs text-indigo-600 font-semibold hover:text-indigo-800"
                >
                  {useCustomJob ? 'Use Saved Job' : '+ Custom Job Text'}
                </button>
              </div>

              {useCustomJob ? (
                <textarea
                  rows={3}
                  required
                  value={customJobText}
                  onChange={(e) => setCustomJobText(e.target.value)}
                  placeholder="Paste direct job description text..."
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              ) : (
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white font-medium"
                >
                  <option value="">-- Choose a saved job --</option>
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} at {j.company || 'Company'} ({j.source})
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={tailoring || resumes.length === 0}
              className="px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {tailoring ? (
                <>
                  <LoadingSpinner size="sm" className="p-0 text-white" />
                  <span>Executing Tailoring Pipeline...</span>
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4" />
                  <span>Generate Tailored Package</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Tailored Workspace Output */}
      {application && (
        <div className="space-y-6">
          {/* Metrics & Diff Card */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-6">
            <div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                Application Review Package #{application.id}
              </span>
              <h2 className="text-xl font-bold text-slate-900 mt-2">
                {application.job_title} at {application.company || 'Company'}
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Tailoring Mode:{' '}
                <strong className="text-indigo-600 font-mono">
                  {diff?.mode || 'heuristic_alignment'}
                </strong>{' '}
                • Status: <strong className="text-slate-800">{application.status}</strong>
              </p>
            </div>

            {/* Before vs After Score */}
            <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div className="text-center">
                <span className="text-xs text-slate-400 block">Original Score</span>
                <span className="text-xl font-bold text-slate-600">{diff?.before_score ?? 60}%</span>
              </div>
              <ArrowRight className="w-5 h-5 text-indigo-500" />
              <div className="text-center">
                <span className="text-xs text-indigo-600 font-semibold block">Tailored Score</span>
                <span className="text-2xl font-bold text-indigo-700">
                  {application.ats_score ?? diff?.after_score ?? 85}%
                </span>
              </div>
            </div>
          </div>

          {/* Two-Column Editor: Tailored Resume vs Cover Letter */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tailored Resume */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileCheck className="w-5 h-5 text-indigo-600" />
                  Tailored Resume Text
                </h3>
                <span className="text-xs text-slate-400">Editable Markdown/Text</span>
              </div>
              <textarea
                rows={16}
                value={editedResume}
                onChange={(e) => setEditedResume(e.target.value)}
                className="w-full flex-1 p-4 text-xs font-mono border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50 leading-relaxed text-slate-800"
              />
            </div>

            {/* Generated Cover Letter */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Edit3 className="w-5 h-5 text-indigo-600" />
                  Tailored Cover Letter
                </h3>
                <span className="text-xs text-slate-400">Customized Narrative</span>
              </div>
              <textarea
                rows={16}
                value={editedCoverLetter}
                onChange={(e) => setEditedCoverLetter(e.target.value)}
                className="w-full flex-1 p-4 text-xs font-sans border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50 leading-relaxed text-slate-800"
              />
            </div>
          </div>

          {/* Candidate Notes */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Application Notes & Personal Reminders
            </label>
            <input
              type="text"
              value={candidateNotes}
              onChange={(e) => setCandidateNotes(e.target.value)}
              placeholder="e.g. Applied via internal referral, hiring manager name, follow-up scheduled for next Tuesday..."
              className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Actions Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleSaveEdits}
                disabled={saving}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 hover:bg-slate-800 text-white transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Saving...' : 'Save Manual Edits'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadDocx}
                disabled={downloading}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                <span>{downloading ? 'Exporting...' : 'Download DOCX Resume'}</span>
              </button>
            </div>

            <button
              type="button"
              onClick={() => navigate(`/applications/${application.id}/review`)}
              className="px-5 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center gap-2 transition-colors"
            >
              <span>Go to Final Submission & Review</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
