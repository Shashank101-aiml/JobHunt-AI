import pytest
from app.utils.jd_parser import (
    normalize_jd,
    extract_job_title,
    extract_company_name,
    extract_years_experience,
    extract_salary_range
)

SAMPLE_JD_TEXT = """Role: Senior Backend Engineer
Company: CloudNexus Technologies
Location: Remote (US)
Employment Type: Full-Time

About CloudNexus:
We are building next-generation distributed databases.

Responsibilities:
- Design and scale distributed microservices in Go and Python.
- Optimize high-throughput APIs handling millions of requests per minute.
- Collaborate with cloud infrastructure engineers on AWS and Kubernetes.

Requirements:
- 5+ years of software development experience with Python, Go, and PostgreSQL.
- Experience with Docker, Redis, and message queues.
- Strong knowledge of RESTful API design and system architecture.

Preferred Qualifications:
- Experience with Terraform, CI/CD, and Kubernetes.
- Familiarity with Vector Search and ChromaDB.

Compensation:
USD 150,000 - 190,000 / yr plus equity.
"""

def test_extract_job_title():
    title = extract_job_title(SAMPLE_JD_TEXT)
    assert "Senior Backend Engineer" in title

def test_extract_company():
    company = extract_company_name(SAMPLE_JD_TEXT)
    assert company == "CloudNexus Technologies"

def test_extract_yoe():
    yoe = extract_years_experience(SAMPLE_JD_TEXT)
    assert yoe == 5

def test_extract_salary():
    salary = extract_salary_range(SAMPLE_JD_TEXT)
    assert salary is not None
    assert "150,000" in salary

def test_normalize_jd_full():
    jd = normalize_jd(SAMPLE_JD_TEXT)
    assert jd.title == "Senior Backend Engineer"
    assert jd.company == "CloudNexus Technologies"
    assert jd.location == "Remote"
    assert jd.employment_type == "Full-Time"
    assert jd.min_years_experience == 5
    
    # Required skills
    assert "Python" in jd.required_skills
    assert "Go" in jd.required_skills
    assert "PostgreSQL" in jd.required_skills
    assert "Docker" in jd.required_skills

    # Preferred skills
    assert "Terraform" in jd.preferred_skills
    assert "Kubernetes" in jd.preferred_skills
    assert "ChromaDB" in jd.preferred_skills

    # Responsibilities & qualifications extracted
    assert len(jd.responsibilities) >= 2
    assert len(jd.qualifications) >= 2

def test_jd_without_salary_does_not_invent():
    text_no_salary = """Position: Python Developer
Requirements:
- Python, FastAPI
"""
    jd = normalize_jd(text_no_salary)
    assert jd.salary_range is None
    assert jd.min_years_experience is None
    assert "Python" in jd.required_skills
