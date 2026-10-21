import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  Download,
  ExternalLink,
  Save,
  History,
  ShieldCheck,
  ArrowLeft,
  Check,
} from 'lucide-react';
import { applicationsApi } from '../services/applicationsApi';
import { Application, ApplicationEvent } from '../types';
import { StatusBadge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { extractErrorMessage } from '../lib/api';

export const ApplicationReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const appId = parseInt(id || '0', 10);

  const [application, setApplication] = useState<Application | null>(null);
  const [events, setEvents] = useState<ApplicationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Editable Content
  const [tailoredResume, setTailoredResume] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [notes, setNotes] = useState('');

  // Human-in-the-loop Verification Checklist
  const [checkContact, setCheckContact] = useState(false);
  const [checkTruth, setCheckTruth] = useState(false);
  const [checkRequirements, setCheckRequirements] = useState(false);

  // Submission Settings
  const [submissionType, setSubmissionType] = useState<'manual' | 'email'>('manual');

  const loadApplication = async () => {
    if (!appId) return;
    try {
      setLoading(true);
      setError(null);
      const [appData, eventList] = await Promise.all([
        applicationsApi.getApplication(appId),
        applicationsApi.getApplicationEvents(appId),
      ]);
      setApplication(appData);
      setTailoredResume(appData.tailored_resume_text || '');
      setCoverLetter(appData.cover_letter || '');
      setNotes(appData.notes || '');
      setEvents(eventList);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplication();
  }, [appId]);

  const handleSaveEdits = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);
      const updated = await applicationsApi.saveApplicationReview(appId, {
        tailored_resume_text: tailoredResume,
        cover_letter: coverLetter,
        notes,
      });
      setApplication(updated);
      setSuccessMsg('Candidate edits successfully saved to database.');
      const eventList = await applicationsApi.getApplicationEvents(appId);
      setEvents(eventList);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadDocx = async () => {
    try {
      setDownloading(true);
      setError(null);
      await applicationsApi.downloadTailoredDocx(appId);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  const handleSubmitAction = async (confirmed: boolean) => {
    const allChecked = checkContact && checkTruth && checkRequirements;
    if (!allChecked) {
      setError('Please complete the verification checklist before triggering or confirming submission.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);
      const updated = await applicationsApi.submitApplication(appId, {
        submission_type: submissionType,
        candidate_confirmed: confirmed,
        notes,
      });
      setApplication(updated);
      if (updated.status === 'submitted') {
        setSuccessMsg('Application successfully marked as submitted with verified confirmation!');
      } else if (updated.status === 'requires_manual_action') {
        setSuccessMsg('Package prepared! Manual portal submission required. Complete the steps on the employer portal and confirm.');
      } else {
        setSuccessMsg(`Status updated: ${updated.status}`);
      }
      const eventList = await applicationsApi.getApplicationEvents(appId);
      setEvents(eventList);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading application package and audit trail..." size="lg" className="min-h-[50vh]" />;
  }

  if (!application) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-600">Application not found.</p>
        <button onClick={() => navigate('/applications')} className="mt-4 text-indigo-600 font-semibold underline">
          Return to Applications
        </button>
      </div>
    );
  }

  const allChecked = checkContact && checkTruth && checkRequirements;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Navigation & Header */}
      <div>
        <button
          type="button"
          onClick={() => navigate('/applications')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Applications</span>
        </button>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                {application.job_title || 'Software Engineer'}
              </h1>
              <StatusBadge status={application.status} />
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {application.company || 'Company Not Specified'} • Application #{application.id}
            </p>
          </div>

          <button
            type="button"
            onClick={handleDownloadDocx}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold shadow-2xs transition-colors self-start sm:self-auto"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>{downloading ? 'Downloading...' : 'Export DOCX'}</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Action Alert</p>
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

      {/* Human-in-the-Loop Verification Checklist Card */}
      <div className="bg-indigo-900 text-white p-6 sm:p-8 rounded-2xl shadow-md space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-indigo-300" />
          <h2 className="text-lg font-bold">Mandatory Human Review Checklist</h2>
        </div>
        <p className="text-xs text-indigo-200 leading-relaxed max-w-2xl">
          To maintain strict ethical boundaries and factual accuracy, Job Hunt requires explicit candidate confirmation
          before any application is considered submitted or delivered externally.
        </p>

        <div className="space-y-2 pt-2">
          <label className="flex items-center gap-3 text-xs cursor-pointer select-none">
            <input
              type="checkbox"
              checked={checkContact}
              onChange={(e) => setCheckContact(e.target.checked)}
              className="w-4 h-4 text-indigo-500 rounded focus:ring-indigo-400"
            />
            <span>I have verified that my contact details (Email, Phone, LinkedIn) are current and accurate.</span>
          </label>

          <label className="flex items-center gap-3 text-xs cursor-pointer select-none">
            <input
              type="checkbox"
              checked={checkTruth}
              onChange={(e) => setCheckTruth(e.target.checked)}
              className="w-4 h-4 text-indigo-500 rounded focus:ring-indigo-400"
            />
            <span>I have reviewed the tailored resume bullet points and verified that no qualifications were fabricated.</span>
          </label>

          <label className="flex items-center gap-3 text-xs cursor-pointer select-none">
            <input
              type="checkbox"
              checked={checkRequirements}
              onChange={(e) => setCheckRequirements(e.target.checked)}
              className="w-4 h-4 text-indigo-500 rounded focus:ring-indigo-400"
            />
            <span>I have inspected the target company job description and confirmed eligibility.</span>
          </label>
        </div>
      </div>

      {/* Two-Column Editor: Tailored Resume & Cover Letter */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tailored Resume */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-indigo-600" />
              Tailored Resume Content
            </h3>
            <span className="text-xs text-slate-400 font-mono">Editable</span>
          </div>
          <textarea
            rows={14}
            value={tailoredResume}
            onChange={(e) => setTailoredResume(e.target.value)}
            className="w-full flex-1 p-3.5 text-xs font-mono border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50 leading-relaxed text-slate-800"
          />
        </div>

        {/* Cover Letter */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-indigo-600" />
              Personalized Cover Letter
            </h3>
            <span className="text-xs text-slate-400 font-mono">Editable</span>
          </div>
          <textarea
            rows={14}
            value={coverLetter}
            onChange={(e) => setCoverLetter(e.target.value)}
            className="w-full flex-1 p-3.5 text-xs font-sans border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50 leading-relaxed text-slate-800"
          />
        </div>
      </div>

      {/* Notes & Save Row */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center gap-4">
        <div className="flex-1 w-full">
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Application Notes & Interview Reminders
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add personal notes or interview scheduling details..."
            className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          type="button"
          onClick={handleSaveEdits}
          disabled={saving}
          className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center gap-2 self-end sm:self-auto disabled:opacity-50 transition-colors"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving...' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Submission Actions Box */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Application Submission Execution</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Choose how to execute the submission. External submissions are handled via authorized adapters or manual portal link.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            onClick={() => setSubmissionType('manual')}
            className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
              submissionType === 'manual'
                ? 'border-indigo-600 bg-indigo-50/30'
                : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-sm text-slate-900">Manual Portal Submission</span>
              {submissionType === 'manual' && <Check className="w-4 h-4 text-indigo-600" />}
            </div>
            <p className="text-xs text-slate-500">
              For company career portals. Prepares the package, opens the employer link, and records status upon your confirmation.
            </p>
          </div>

          <div
            onClick={() => setSubmissionType('email')}
            className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
              submissionType === 'email'
                ? 'border-indigo-600 bg-indigo-50/30'
                : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-sm text-slate-900">SMTP Email Delivery</span>
              {submissionType === 'email' && <Check className="w-4 h-4 text-indigo-600" />}
            </div>
            <p className="text-xs text-slate-500">
              Dispatches directly to hiring manager email using authenticated SMTP (requires configured SMTP in .env).
            </p>
          </div>
        </div>

        {/* Portal URL link if manual */}
        {submissionType === 'manual' && application.job_url && !application.job_url.startsWith('manual-') && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-500 block">Employer Career Portal URL:</span>
              <a
                href={application.job_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-indigo-600 hover:underline flex items-center gap-1 mt-0.5"
              >
                <span className="truncate max-w-md">{application.job_url}</span>
                <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
              </a>
            </div>
            <a
              href={application.job_url}
              target="_blank"
              rel="noreferrer"
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
            >
              Open Portal
            </a>
          </div>
        )}

        {/* Confirm Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Current Lifecycle Status:</span>
            <StatusBadge status={application.status} />
          </div>

          <div className="flex items-center gap-3">
            {application.status !== 'submitted' ? (
              <>
                <button
                  type="button"
                  onClick={() => handleSubmitAction(false)}
                  disabled={submitting || !allChecked}
                  className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50 transition-colors"
                >
                  Prepare Submission Package
                </button>
                <button
                  type="button"
                  onClick={() => handleSubmitAction(true)}
                  disabled={submitting || !allChecked}
                  className="px-5 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm flex items-center gap-1.5 disabled:opacity-50 transition-colors"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm I Have Submitted</span>
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2 text-emerald-700 text-xs font-semibold">
                <CheckCircle2 className="w-5 h-5" />
                <span>Application is confirmed and tracked as submitted.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chronological Event History Timeline */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-600" />
          Audit Trail & Activity History ({events.length})
        </h3>

        {events.length === 0 ? (
          <p className="text-xs text-slate-400">No activity logged yet.</p>
        ) : (
          <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {events.map((ev) => (
              <div key={ev.id} className="relative">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-indigo-600 border-2 border-white" />
                <div className="text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800 capitalize">
                      {ev.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-slate-400 text-[10px]">
                      {new Date(ev.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-600 mt-0.5">{ev.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
