import React, { useEffect, useState, useRef } from 'react';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Eye,
  Check,
  User,
  Mail,
  Phone,
  Layers,
} from 'lucide-react';
import { resumeApi } from '../services/resumeApi';
import { Resume } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { Modal } from '../components/ui/Modal';
import { extractErrorMessage } from '../lib/api';

export const ResumesPage: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadResumes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await resumeApi.listResumes();
      setResumes(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const handleFileUpload = async (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const validExtensions = ['.pdf', '.docx', '.txt', '.md'];

    if (!validExtensions.includes(ext)) {
      setError(`Unsupported file format '${ext}'. Please upload a PDF, DOCX, or TXT file.`);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10MB limit.');
      return;
    }

    if (file.size === 0) {
      setError('Selected file is empty.');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccessMsg(null);
      const newResume = await resumeApi.uploadResume(file, true);
      setSuccessMsg(`Successfully uploaded and parsed resume: ${newResume.filename}`);
      await loadResumes();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleActivate = async (id: number) => {
    try {
      setError(null);
      await resumeApi.activateResume(id);
      setSuccessMsg('Active candidate resume updated successfully.');
      await loadResumes();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleDelete = async (id: number, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete '${filename}'?`)) return;
    try {
      setError(null);
      await resumeApi.deleteResume(id);
      setSuccessMsg(`Deleted resume: ${filename}`);
      await loadResumes();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Resume Ingestion & Profile Manager</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload authentic candidate resumes (PDF, DOCX, TXT). Text is extracted deterministically, skills categorized,
          and semantic chunks indexed in ChromaDB.
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Upload or Parsing Error</p>
            <p className="text-rose-600 mt-0.5">{error}</p>
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

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-50/50 scale-[1.01]'
            : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50/50 bg-white'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />
        <div className="flex flex-col items-center max-w-md mx-auto">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 shadow-sm">
            <Upload className="w-7 h-7" />
          </div>
          <h3 className="text-base font-semibold text-slate-800">
            {uploading ? 'Parsing and indexing resume...' : 'Drop your resume here, or browse files'}
          </h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            Supports PDF, DOCX, and TXT files up to 10MB.
          </p>
          {uploading ? (
            <LoadingSpinner message="Extracting text and categorizing skills..." size="sm" className="p-2" />
          ) : (
            <span className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors">
              Choose File
            </span>
          )}
        </div>
      </div>

      {/* Uploaded Resumes List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Stored Candidate Resumes</h2>
            <p className="text-xs text-slate-500">Select the active resume to be matched against incoming jobs</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg">
            {resumes.length} {resumes.length === 1 ? 'Resume' : 'Resumes'}
          </span>
        </div>

        {loading ? (
          <LoadingSpinner message="Loading candidate profiles..." size="md" />
        ) : resumes.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No Resumes Uploaded"
            description="Upload a PDF, DOCX, or TXT resume above to begin matching and tailoring jobs."
            actionText="Upload Resume"
            onAction={() => fileInputRef.current?.click()}
          />
        ) : (
          <div className="divide-y divide-slate-100">
            {resumes.map((resume) => {
              const profile = resume.structured_profile;
              const contact = profile?.contact_info;
              const skillsList = resume.parsed_skills ? resume.parsed_skills.split(', ') : [];

              return (
                <div
                  key={resume.id}
                  className={`p-6 transition-colors ${
                    resume.is_active ? 'bg-indigo-50/30' : 'hover:bg-slate-50/60'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div
                        className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                          resume.is_active ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        <FileText className="w-6 h-6" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-base font-semibold text-slate-900 truncate">
                            {resume.filename}
                          </h3>
                          {resume.is_active && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                              <Check className="w-3 h-3" />
                              Active Resume
                            </span>
                          )}
                          <span className="text-xs text-slate-400 uppercase font-mono">
                            .{resume.file_type}
                          </span>
                        </div>

                        {/* Extracted Contact Info */}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-600 mt-2">
                          {contact?.name && (
                            <span className="flex items-center gap-1 font-medium text-slate-800">
                              <User className="w-3.5 h-3.5 text-slate-400" />
                              {contact.name}
                            </span>
                          )}
                          {contact?.email && (
                            <span className="flex items-center gap-1">
                              <Mail className="w-3.5 h-3.5 text-slate-400" />
                              {contact.email}
                            </span>
                          )}
                          {contact?.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="w-3.5 h-3.5 text-slate-400" />
                              {contact.phone}
                            </span>
                          )}
                        </div>

                        {/* Skills Preview */}
                        {skillsList.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-3">
                            {skillsList.slice(0, 7).map((skill, i) => (
                              <span
                                key={i}
                                className="inline-block px-2 py-0.5 text-xs bg-white border border-slate-200 text-slate-700 rounded-md shadow-2xs"
                              >
                                {skill}
                              </span>
                            ))}
                            {skillsList.length > 7 && (
                              <span className="inline-block px-2 py-0.5 text-xs text-slate-400">
                                +{skillsList.length - 7} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <button
                        type="button"
                        onClick={() => setSelectedResume(resume)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 shadow-2xs transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect Profile</span>
                      </button>

                      {!resume.is_active && (
                        <button
                          type="button"
                          onClick={() => handleActivate(resume.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Make Active</span>
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleDelete(resume.id, resume.filename)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Delete resume"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Inspect Profile Modal */}
      <Modal
        isOpen={selectedResume !== null}
        onClose={() => setSelectedResume(null)}
        title={`Extracted Profile: ${selectedResume?.filename || ''}`}
        maxWidth="2xl"
      >
        {selectedResume && (
          <div className="space-y-6 text-sm text-slate-700">
            {/* Contact Information */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <h4 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                <User className="w-4 h-4 text-indigo-600" />
                Contact Details
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400 block">Candidate Name:</span>
                  <span className="font-medium text-slate-900">
                    {selectedResume.structured_profile?.contact_info?.name || 'Not detected'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Email Address:</span>
                  <span className="font-medium text-slate-900">
                    {selectedResume.structured_profile?.contact_info?.email || 'Not detected'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Phone:</span>
                  <span className="font-medium text-slate-900">
                    {selectedResume.structured_profile?.contact_info?.phone || 'Not detected'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">LinkedIn / GitHub:</span>
                  <span className="font-medium text-slate-900">
                    {selectedResume.structured_profile?.contact_info?.linkedin ||
                      selectedResume.structured_profile?.contact_info?.github ||
                      'Not specified'}
                  </span>
                </div>
              </div>
            </div>

            {/* Categorized Skills */}
            <div>
              <h4 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Extracted Skills Taxonomy
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {selectedResume.parsed_skills ? (
                  selectedResume.parsed_skills.split(', ').map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 rounded-md border border-indigo-100"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 text-xs">No skills detected.</span>
                )}
              </div>
            </div>

            {/* Raw Extracted Text Viewer */}
            <div>
              <h4 className="font-semibold text-slate-900 mb-2">Original Extracted Text</h4>
              <div className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs max-h-60 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {selectedResume.raw_text}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
