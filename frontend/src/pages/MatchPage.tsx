import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Sparkles,
  FileText,
  Briefcase,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  Gauge,
  Check,
} from 'lucide-react';
import { resumeApi } from '../services/resumeApi';
import { jobsApi } from '../services/jobsApi';
import { matchingApi } from '../services/matchingApi';
import { Resume, Job, MatchEvaluationResponse } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { extractErrorMessage } from '../lib/api';

export const MatchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedJobId = searchParams.get('job_id');

  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<number | ''>('');
  const [selectedJobId, setSelectedJobId] = useState<number | ''>(
    preselectedJobId ? parseInt(preselectedJobId, 10) : ''
  );

  const [useCustomJob, setUseCustomJob] = useState(false);
  const [customJobText, setCustomJobText] = useState('');

  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchResult, setMatchResult] = useState<MatchEvaluationResponse | null>(null);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [resList, jobsList] = await Promise.all([
          resumeApi.listResumes(),
          jobsApi.listJobs({ limit: 50 }),
        ]);
        setResumes(resList);
        setJobs(jobsList.items);

        // Pre-select active resume
        const active = resList.find((r) => r.is_active) || resList[0];
        if (active) setSelectedResumeId(active.id);

        if (preselectedJobId) {
          const id = parseInt(preselectedJobId, 10);
          if (jobsList.items.some((j) => j.id === id)) {
            setSelectedJobId(id);
          }
        }
      } catch (err) {
        setError(extractErrorMessage(err));
      }
    }
    loadOptions();
  }, [preselectedJobId]);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResumeId) {
      setError('Please select a candidate resume.');
      return;
    }

    if (!useCustomJob && !selectedJobId) {
      setError('Please select a saved job or switch to custom job text.');
      return;
    }

    if (useCustomJob && (!customJobText || customJobText.trim().length < 20)) {
      setError('Please provide at least 20 characters of job description text.');
      return;
    }

    try {
      setEvaluating(true);
      setError(null);
      setMatchResult(null);

      const payload = {
        resume_id: Number(selectedResumeId),
        job_id: useCustomJob ? undefined : Number(selectedJobId),
        job_text: useCustomJob ? customJobText.trim() : undefined,
      };

      const result = await matchingApi.evaluateMatch(payload);
      setMatchResult(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setEvaluating(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-600 border-emerald-500 bg-emerald-50';
    if (score >= 60) return 'text-indigo-600 border-indigo-500 bg-indigo-50';
    if (score >= 40) return 'text-amber-600 border-amber-500 bg-amber-50';
    return 'text-rose-600 border-rose-500 bg-rose-50';
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">ATS Match & Semantic Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Evaluate an authentic resume against target job requirements. The engine inspects keyword density,
          categorized skill coverage, years of experience, and section completeness with zero fabricated scores.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Evaluation Error</p>
            <p className="text-rose-600 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Input Form Card */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
        <form onSubmit={handleEvaluate} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Resume Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-indigo-600" />
                Select Candidate Resume
              </label>
              {resumes.length === 0 ? (
                <div className="text-xs text-amber-600 bg-amber-50 p-3 rounded-xl border border-amber-200">
                  No resumes found. Please upload a resume in Resume Manager first.
                </div>
              ) : (
                <select
                  value={selectedResumeId}
                  onChange={(e) => setSelectedResumeId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white font-medium"
                >
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.filename} {r.is_active ? '★ (Active)' : ''} —{' '}
                      {r.structured_profile?.contact_info?.name || 'Parsed Profile'}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Job Source Selector */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4 text-indigo-600" />
                  Target Job Description
                </label>
                <button
                  type="button"
                  onClick={() => setUseCustomJob((prev) => !prev)}
                  className="text-xs text-indigo-600 font-semibold hover:text-indigo-800"
                >
                  {useCustomJob ? 'Select from Saved Jobs' : '+ Paste Custom JD'}
                </button>
              </div>

              {useCustomJob ? (
                <textarea
                  rows={4}
                  required
                  value={customJobText}
                  onChange={(e) => setCustomJobText(e.target.value)}
                  placeholder="Paste direct job description text (requirements, responsibilities, skills)..."
                  className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              ) : jobs.length === 0 ? (
                <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  No saved jobs available.{' '}
                  <button
                    type="button"
                    onClick={() => setUseCustomJob(true)}
                    className="text-indigo-600 font-semibold hover:underline"
                  >
                    Paste custom job text instead.
                  </button>
                </div>
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
              disabled={evaluating || resumes.length === 0}
              className="px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {evaluating ? (
                <>
                  <LoadingSpinner size="sm" className="p-0 text-white" />
                  <span>Computing ATS Compatibility...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>Calculate ATS Match Score</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Results View */}
      {matchResult && (
        <div className="space-y-6">
          {/* Main Score Header Card */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex-1">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                Evaluation Target
              </span>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-2">{matchResult.job_title}</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                {matchResult.company ? `Company: ${matchResult.company} • ` : ''}
                {matchResult.min_years_experience
                  ? `Required Experience: ${matchResult.min_years_experience}+ Years`
                  : 'Experience Not Specified'}
              </p>
              <p className="text-xs text-slate-400 mt-3 italic">{matchResult.feedback.disclaimer}</p>
            </div>

            {/* Score Ring Display */}
            <div className="flex flex-col items-center">
              <div
                className={`w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center font-bold shadow-sm ${getScoreColor(
                  matchResult.ats_score
                )}`}
              >
                <span className="text-3xl leading-none">{matchResult.ats_score}</span>
                <span className="text-[11px] font-medium uppercase tracking-wider mt-1 text-slate-500">out of 100</span>
              </div>
            </div>
          </div>

          {/* Subscores Breakdown Grid */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Gauge className="w-5 h-5 text-indigo-600" />
              Transparent Subscore Breakdown & Weights
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 text-xs">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-500 block">Required Skills (40%):</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">
                  {matchResult.feedback.subscores.required_skills_match}%
                </span>
                <span className="text-[10px] text-slate-400">Strict taxonomy matching</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-500 block">Preferred Skills (15%):</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">
                  {matchResult.feedback.subscores.preferred_skills_match}%
                </span>
                <span className="text-[10px] text-slate-400">Bonus points & nice-to-haves</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-500 block">Experience YoE (20%):</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">
                  {matchResult.feedback.subscores.experience_match}%
                </span>
                <span className="text-[10px] text-slate-400">Seniority alignment</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-500 block">Keyword Density (15%):</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">
                  {matchResult.feedback.subscores.keyword_density}%
                </span>
                <span className="text-[10px] text-slate-400">Term frequency in text</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-500 block">Completeness (10%):</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">
                  {matchResult.feedback.subscores.section_completeness}%
                </span>
                <span className="text-[10px] text-slate-400">Contact, Work, Education</span>
              </div>
            </div>
          </div>

          {/* Matched vs Missing Skills Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Matched Skills */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Matched Skills & Requirements ({matchResult.feedback.matched_skills.length})
              </h3>
              {matchResult.feedback.matched_skills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.feedback.matched_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200 flex items-center gap-1"
                    >
                      <Check className="w-3 h-3 text-emerald-600" />
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No matching skills detected in resume text.</p>
              )}
            </div>

            {/* Missing Skills */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                <XCircle className="w-4 h-4 text-rose-600" />
                Missing or Weakly Evidenced Requirements ({matchResult.feedback.missing_skills.length})
              </h3>
              {matchResult.feedback.missing_skills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.feedback.missing_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 text-xs font-semibold bg-rose-50 text-rose-800 rounded-lg border border-rose-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-emerald-700 font-medium">
                  Outstanding! All identified requirements are represented in the resume.
                </p>
              )}
            </div>
          </div>

          {/* Actionable Recommendations */}
          {matchResult.feedback.suggestions && matchResult.feedback.suggestions.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                Actionable ATS Improvement Recommendations
              </h3>
              <ul className="space-y-2 text-xs text-slate-700">
                {matchResult.feedback.suggestions.map((sugg, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="w-4 h-4 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{sugg}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Proceed to Tailor Action */}
          <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-6 rounded-2xl border border-indigo-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-indigo-950">Ready to Tailor Your Resume?</h3>
              <p className="text-xs text-indigo-800 mt-0.5">
                Execute the tailoring pipeline to align bullet points, generate a personalized cover letter, and
                export a DOCX document.
              </p>
            </div>
            <button
              onClick={() => {
                navigate(
                  `/tailor?resume_id=${selectedResumeId}${
                    selectedJobId ? `&job_id=${selectedJobId}` : ''
                  }`
                );
              }}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold text-xs shadow-sm flex items-center gap-2 flex-shrink-0"
            >
              <span>Proceed to Tailoring Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
