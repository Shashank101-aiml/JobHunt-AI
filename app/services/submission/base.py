from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class SubmissionPackage(BaseModel):
    application_id: int
    job_title: str
    company: str
    job_url: str
    candidate_name: str
    candidate_email: Optional[str] = None
    tailored_resume_text: str
    cover_letter: Optional[str] = None
    resume_attachment_path: Optional[str] = None

class SubmissionResult(BaseModel):
    status: str  # "submitted", "ready_for_review", "requires_manual_action", "failed"
    is_submitted: bool
    receipt_id: Optional[str] = None
    message: str
    requires_user_action: bool = False
    action_instructions: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class BaseSubmissionAdapter(ABC):
    @abstractmethod
    def can_handle(self, submission_type: str) -> bool:
        pass

    @abstractmethod
    async def submit(self, package: SubmissionPackage, user_confirmed: bool) -> SubmissionResult:
        pass
