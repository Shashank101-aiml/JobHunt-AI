from typing import TypedDict, Optional, Dict, Any, List

class AgentState(TypedDict):
    application_id: int
    job_id: Optional[int]
    job_url: str
    job_text: Optional[str]
    resume_id: int
    
    # Ingested data
    raw_jd: str
    structured_jd: Dict[str, Any]
    resume_text: str
    resume_profile: Dict[str, Any]
    
    # Analysis & Tailoring
    relevant_chunks: List[Dict[str, Any]]
    ats_score: float
    ats_feedback: Dict[str, Any]
    tailored_resume: str
    tailored_diff: Dict[str, Any]
    cover_letter: str
    
    # Review & Submission
    status: str  # draft, ready_for_review, requires_manual_action, submitted, failed
    user_approved: bool
    submission_type: str
    submission_result: Optional[Dict[str, Any]]
    
    error: Optional[str]
