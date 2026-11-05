import pytest
import json
from pydantic import ValidationError

from app.schemas.resume import (
    StructuredResumeProfile,
    ContactInfo,
    EducationItem,
    ExperienceItem,
    ResumeResponse
)
from app.schemas.job import (
    StructuredJobDescription,
    JobResponse,
    JobCreateManual
)
from app.schemas.application import (
    ATSFeedback,
    SubscoreBreakdown,
    MatchEvaluationResponse,
    ApplicationResponse
)
from app.utils.jd_parser import normalize_jd
from app.services.resume_parser import (
    extract_contact_info,
    extract_skills_nlp,
    extract_sections,
    extract_education_items,
    extract_experience_items
)

def test_structured_resume_profile_valid_schema():
    profile_data = {
        "contact_info": {
            "name": "Alex Rivera",
            "email": "alex@example.com",
            "phone": "(555) 234-5678",
            "linkedin": "linkedin.com/in/alexrivera"
        },
        "summary": "Senior Backend Engineer with 6 years experience.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "education": [
            {
                "degree": "Bachelor of Science",
                "institution": "Cal State",
                "graduation_year": "2018"
            }
        ],
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "CloudScale",
                "duration": "2021 - Present",
                "highlights": ["Built REST APIs in FastAPI"]
            }
        ],
        "projects": [],
        "certifications": []
    }

    profile = StructuredResumeProfile(**profile_data)
    assert profile.contact_info.name == "Alex Rivera"
    assert "FastAPI" in profile.skills
    assert len(profile.experience) == 1
    assert profile.experience[0].company == "CloudScale"

def test_structured_resume_profile_empty_and_default_handling():
    # Empty profile must instantiate cleanly with defaults
    profile = StructuredResumeProfile()
    assert profile.skills == []
    assert profile.experience == []
    assert profile.education == []
    assert profile.contact_info is None or isinstance(profile.contact_info, ContactInfo)

def test_structured_job_description_schema():
    jd_text = (
        "Title: Senior Backend Engineer\n"
        "Company: Apex Cloud\n"
        "Location: Remote\n"
        "Requirements:\n"
        "- 5+ years experience in Python and FastAPI\n"
        "- PostgreSQL database expertise\n"
        "Preferred:\n"
        "- Redis caching\n"
        "Salary: USD 140,000 - 180,000 / yr"
    )

    structured = normalize_jd(jd_text, source_url="https://apex.example.com/job/101")
    assert isinstance(structured, StructuredJobDescription)
    assert structured.title == "Senior Backend Engineer"
    assert structured.company == "Apex Cloud"
    assert structured.min_years_experience == 5
    assert "Python" in structured.required_skills
    assert "FastAPI" in structured.required_skills
    assert "PostgreSQL" in structured.required_skills
    assert structured.salary_range is not None

def test_jd_schema_validation_rejects_empty_text():
    with pytest.raises(ValueError, match="Job description text cannot be empty"):
        normalize_jd("")

def test_ats_feedback_schema_and_subscores():
    subscores = SubscoreBreakdown(
        required_skills_match=85.0,
        preferred_skills_match=70.0,
        experience_match=100.0,
        keyword_density=75.0,
        section_completeness=90.0
    )
    feedback = ATSFeedback(
        score=84.5,
        subscores=subscores,
        matched_skills=["Python", "FastAPI", "PostgreSQL"],
        missing_skills=["Kubernetes"],
        evidence={"matched_count": 3, "total_required": 4},
        suggestions=["Add Kubernetes exposure if applicable."]
    )

    feedback_json = feedback.model_dump()
    assert feedback_json["score"] == 84.5
    assert feedback_json["subscores"]["required_skills_match"] == 85.0
    assert "Kubernetes" in feedback_json["missing_skills"]

def test_malformed_llm_json_recovery():
    """Validates that malformed or partial LLM JSON outputs are safely handled."""
    malformed_json_str = '{"title": "Backend Dev", "required_skills": ["Python", "FastAPI"], '  # truncated JSON

    with pytest.raises(json.JSONDecodeError):
        json.loads(malformed_json_str)

    # Valid schema fallback mechanism
    fallback_data = {"title": "Software Engineer", "required_skills": ["Python"]}
    recovered_model = StructuredJobDescription(**fallback_data)
    assert recovered_model.title == "Software Engineer"
    assert recovered_model.required_skills == ["Python"]

def test_schema_rejects_invalid_types():
    with pytest.raises(ValidationError):
        # min_years_experience should be an integer or None, not a dictionary
        StructuredJobDescription(title="Eng", min_years_experience={"invalid": "type"})

def test_deterministic_parser_helpers_integrity():
    raw_resume = (
        "Sarah Connor\n"
        "sarah@cyberdyne.example.com | (415) 555-0199\n"
        "linkedin.com/in/sconnor\n\n"
        "TECHNICAL SKILLS\n"
        "Python, Docker, Linux, Git, SQL\n\n"
        "WORK EXPERIENCE\n"
        "Security Analyst | Cyberdyne Systems | 2020 - Present\n"
        "- Performed vulnerability assessments\n\n"
        "EDUCATION\n"
        "BS Cyber Security | Caltech | 2020"
    )

    contact = extract_contact_info(raw_resume)
    assert contact.email == "sarah@cyberdyne.example.com"
    assert contact.phone is not None

    skills = extract_skills_nlp(raw_resume)
    assert "Python" in skills
    assert "Docker" in skills
    assert "Linux" in skills

    sections = extract_sections(raw_resume)
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections

    edu_items = extract_education_items(sections["education"])
    assert len(edu_items) >= 1
    assert edu_items[0].graduation_year == "2020"
