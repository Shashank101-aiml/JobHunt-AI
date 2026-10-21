from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None

class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

class StructuredResumeProfile(BaseModel):
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size_bytes: Optional[int] = None
    parsed_skills: Optional[str] = None
    structured_profile: Optional[StructuredResumeProfile] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ResumeActivateRequest(BaseModel):
    is_active: bool = True
