from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class StructuredJobDescription(BaseModel):
    title: str = "Software Engineer"
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years_experience: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

class JobCreateManual(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    description_text: str
    source_url: Optional[str] = None

class JobScrapeRequest(BaseModel):
    url: str

class JobResponse(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    raw_description: str
    structured_jd: Optional[StructuredJobDescription] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class PaginatedJobsResponse(BaseModel):
    total: int
    items: List[JobResponse]
