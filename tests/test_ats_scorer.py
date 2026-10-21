import pytest
from app.utils.ats_scorer import calculate_ats_score

JOB_PYTHON_FASTAPI = {
    "title": "Senior Python Backend Engineer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "preferred_skills": ["Redis", "Kubernetes"],
    "min_years_experience": 4,
    "keywords": ["Python", "FastAPI", "PostgreSQL", "Docker", "API"]
}

HIGH_MATCH_RESUME_TEXT = """John Smith
john.smith@example.com | San Francisco, CA
Senior Software Engineer with 6 years of experience.
Expert in Python, FastAPI, Docker, and PostgreSQL. Experienced with Redis caching and AWS.
Built microservices handling 10M requests daily.
"""

HIGH_MATCH_PROFILE = {
    "contact_info": {"email": "john.smith@example.com", "name": "John Smith"},
    "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "Redis"],
    "experience": [{"title": "Senior Engineer", "duration": "2018 - Present"}]
}

LOW_MATCH_RESUME_TEXT = """Arthur Dent
arthur@dent.com | London, UK
Accountant and Financial Planner with 3 years of experience in Tax Compliance, Excel, and SAP.
"""

LOW_MATCH_PROFILE = {
    "contact_info": {"email": "arthur@dent.com", "name": "Arthur Dent"},
    "skills": ["Accounting", "Excel", "Tax Law"],
    "experience": [{"title": "Accountant", "duration": "2021 - Present"}]
}

def test_ats_score_high_match_vs_low_match():
    high_feedback = calculate_ats_score(
        resume_text=HIGH_MATCH_RESUME_TEXT,
        resume_profile=HIGH_MATCH_PROFILE,
        structured_jd=JOB_PYTHON_FASTAPI
    )
    
    low_feedback = calculate_ats_score(
        resume_text=LOW_MATCH_RESUME_TEXT,
        resume_profile=LOW_MATCH_PROFILE,
        structured_jd=JOB_PYTHON_FASTAPI
    )

    # High match must score significantly higher than low match
    assert high_feedback.score > 75.0
    assert low_feedback.score < 40.0
    assert high_feedback.score != 85.0  # Must not be hardcoded 85

    # Check subscores structure
    assert high_feedback.subscores.required_skills_match == 100.0
    assert low_feedback.subscores.required_skills_match == 0.0

    # Low match must identify missing required skills
    assert "Python" in low_feedback.missing_skills
    assert "FastAPI" in low_feedback.missing_skills

    # Actionable suggestions generated
    assert len(low_feedback.suggestions) >= 1
    assert any("Python" in s or "FastAPI" in s for s in low_feedback.suggestions)
