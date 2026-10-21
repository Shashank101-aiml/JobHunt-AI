export interface ContactInfo {
  name?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  github?: string;
}

export interface StructuredResumeProfile {
  contact_info?: ContactInfo;
  summary?: string;
  skills?: Record<string, string[]>;
  experience?: Array<{
    title?: string;
    company?: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    description?: string;
  }>;
  education?: Array<{
    degree?: string;
    institution?: string;
    year?: string;
    details?: string;
  }>;
  certifications?: string[];
  projects?: Array<{
    name?: string;
    description?: string;
    technologies?: string[];
  }>;
}

export interface Resume {
  id: number;
  filename: string;
  filepath: string;
  file_type: string;
  file_size_bytes?: number;
  parsed_skills?: string;
  raw_text?: string;
  structured_profile?: StructuredResumeProfile;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface StructuredJobDescription {
  title?: string;
  company?: string;
  location?: string;
  employment_type?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  min_years_experience?: number;
  responsibilities?: string[];
  qualifications?: string[];
  salary_range?: string;
  keywords?: string[];
}

export interface Job {
  id: number;
  title: string;
  company?: string;
  location?: string;
  employment_type?: string;
  source: string;
  source_url?: string;
  raw_description: string;
  structured_jd?: StructuredJobDescription;
  status: string;
  created_at: string;
}

export interface PaginatedJobs {
  total: number;
  items: Job[];
}

export interface SubscoreBreakdown {
  required_skills_match: number;
  preferred_skills_match: number;
  experience_match: number;
  keyword_density: number;
  section_completeness: number;
}

export interface ATSFeedback {
  score: number;
  subscores: SubscoreBreakdown;
  matched_skills: string[];
  missing_skills: string[];
  evidence?: Record<string, any>;
  suggestions?: string[];
  disclaimer?: string;
}

export interface TailoredDiff {
  mode?: string;
  changes?: string[];
  added_keywords?: string[];
  before_score?: number;
  after_score?: number;
}

export interface Application {
  id: number;
  job_id?: number;
  job_url: string;
  job_title?: string;
  company?: string;
  status: string;
  ats_score?: number;
  ats_feedback?: ATSFeedback;
  tailored_resume_id?: number;
  tailored_resume_text?: string;
  tailored_resume_diff?: TailoredDiff;
  cover_letter?: string;
  submission_type: string;
  submission_response?: Record<string, any>;
  notes?: string;
  submitted_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface PaginatedApplications {
  total: number;
  items: Application[];
}

export interface ApplicationEvent {
  id: number;
  application_id: number;
  event_type: string;
  message: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface MatchEvaluationResponse {
  job_title: string;
  company?: string;
  ats_score: number;
  feedback: ATSFeedback;
  required_skills: string[];
  preferred_skills: string[];
  min_years_experience?: number;
}

export interface DashboardStats {
  total_jobs: number;
  total_applications: number;
  awaiting_review: number;
  submitted: number;
  interviewing: number;
  average_match_score?: number;
  status_distribution: Record<string, number>;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database: string;
  vector_store: string;
  llm_provider: {
    provider: string;
    model: string;
    is_configured: boolean;
  };
  email_service: {
    enabled: boolean;
    smtp_host: string;
  };
}
