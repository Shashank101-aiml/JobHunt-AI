from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SubscoreBreakdown(BaseModel):
    required_skills_match: float
    preferred_skills_match: float
    experience_match: float
    keyword_density: float
    section_completeness: float

class ATSFeedback(BaseModel):
    score: float
    subscores: SubscoreBreakdown
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    disclaimer: str = "Simulated ATS heuristic analysis based on keyword overlap, experience, and completeness."

class ApplicationCreate(BaseModel):
    job_url: Optional[str] = None
    job_id: Optional[int] = None
    job_text: Optional[str] = None  # Optional direct JD text
    resume_id: Optional[int] = None

class ApplicationReviewUpdate(BaseModel):
    tailored_resume_text: Optional[str] = None
    cover_letter: Optional[str] = None
    notes: Optional[str] = None

class ApplicationSubmitRequest(BaseModel):
    submission_type: str = "manual"  # "manual", "greenhouse_api", "email"
    candidate_confirmed: bool = True
    notes: Optional[str] = None

class ApplicationEventResponse(BaseModel):
    id: int
    event_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class ApplicationResponse(BaseModel):
    id: int
    job_id: Optional[int] = None
    job_url: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: str
    ats_score: Optional[float] = None
    ats_feedback: Optional[Dict[str, Any]] = None
    tailored_resume_id: Optional[int] = None
    tailored_resume_text: Optional[str] = None
    tailored_resume_diff: Optional[Dict[str, Any]] = None
    cover_letter: Optional[str] = None
    submission_type: str
    submission_response: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ApplicationStatusResponse(BaseModel):
    id: int
    job_url: str
    status: str
    ats_score: Optional[float] = None
    updated_at: datetime

    model_config = {"from_attributes": True}

class PaginatedApplicationsResponse(BaseModel):
    total: int
    items: List[ApplicationResponse]

class MatchEvaluationRequest(BaseModel):
    resume_id: Optional[int] = None
    job_id: Optional[int] = None
    job_url: Optional[str] = None
    job_text: Optional[str] = None

class MatchEvaluationResponse(BaseModel):
    job_title: str
    company: Optional[str] = None
    ats_score: float
    feedback: ATSFeedback
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years_experience: Optional[int] = None

class DashboardStatsResponse(BaseModel):
    total_jobs: int
    total_applications: int
    awaiting_review: int
    submitted: int
    interviewing: int
    average_match_score: Optional[float] = None
    status_distribution: Dict[str, int]
