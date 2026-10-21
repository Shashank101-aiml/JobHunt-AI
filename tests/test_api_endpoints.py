import pytest
import io

def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "job-hunt-api"
    assert "vector_store" in data
    assert "llm_provider" in data

def test_resume_upload_and_listing(client):
    resume_content = (
        "Alex Rivera\n"
        "alex.rivera@example.com | (555) 234-5678\n"
        "linkedin.com/in/alexrivera\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Senior Backend Engineer with 5 years experience in Python and FastAPI.\n\n"
        "TECHNICAL SKILLS\n"
        "Python, FastAPI, Docker, PostgreSQL, Redis\n\n"
        "WORK EXPERIENCE\n"
        "Senior Engineer | TechVentures | 2021 - Present\n"
        "- Built high-throughput microservices using FastAPI and PostgreSQL.\n"
    )

    file_obj = io.BytesIO(resume_content.encode("utf-8"))
    response = client.post(
        "/api/v1/resumes",
        files={"file": ("test_resume.txt", file_obj, "text/plain")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["filename"] == "test_resume.txt"
    assert "Python" in res_data["parsed_skills"]
    assert res_data["is_active"] is True
    resume_id = res_data["id"]

    # Verify listing
    list_resp = client.get("/api/v1/resumes")
    assert list_resp.status_code == 200
    resumes = list_resp.json()
    assert any(r["id"] == resume_id for r in resumes)

def test_manual_job_creation_and_listing(client):
    job_payload = {
        "title": "Senior Python Backend Engineer",
        "company": "Apex Cloud Systems",
        "location": "Remote",
        "employment_type": "Full-Time",
        "description_text": (
            "Title: Senior Python Backend Engineer\n"
            "Company: Apex Cloud Systems\n"
            "Requirements:\n"
            "- 4+ years of experience with Python, FastAPI, and Docker\n"
            "- Strong database skills with PostgreSQL\n"
            "Nice to have:\n"
            "- Experience with Redis, Kubernetes\n"
            "Salary: USD 140,000 - 175,000 / yr"
        ),
        "source_url": "https://apexcloud.example.com/careers/backend-101"
    }

    create_resp = client.post("/api/v1/jobs/manual", json=job_payload)
    assert create_resp.status_code == 200
    job_data = create_resp.json()
    assert job_data["title"] == "Senior Python Backend Engineer"
    assert job_data["company"] == "Apex Cloud Systems"
    job_id = job_data["id"]

    # Listing
    list_resp = client.get("/api/v1/jobs")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

def test_full_application_lifecycle_api(client):
    # 1. Create a job first
    job_payload = {
        "title": "Staff Platform Engineer",
        "company": "NovaCore",
        "location": "San Francisco, CA",
        "description_text": (
            "Title: Staff Platform Engineer\n"
            "Requirements:\n"
            "- Python, FastAPI, PostgreSQL, Docker\n"
            "Experience: 5+ years"
        )
    }
    job_resp = client.post("/api/v1/jobs/manual", json=job_payload)
    job_id = job_resp.json()["id"]

    # 2. Trigger Application
    apply_resp = client.post(
        "/api/v1/apply?sync_execution=true",
        json={"job_id": job_id}
    )
    assert apply_resp.status_code == 200
    app_data = apply_resp.json()
    app_id = app_data["id"]
    
    # Must be in ready_for_review status
    assert app_data["status"] == "ready_for_review"
    assert app_data["ats_score"] is not None
    assert app_data["ats_score"] > 50.0
    assert len(app_data["tailored_resume_text"]) > 20
    assert len(app_data["cover_letter"]) > 20

    # 3. Candidate Reviews and Edits Application Content
    review_resp = client.post(
        f"/api/v1/applications/{app_id}/review",
        json={
            "cover_letter": "Dear NovaCore Team,\n\nI am thrilled to apply for the Staff Platform Engineer role.",
            "notes": "Reviewed tailored resume; highlighting distributed systems."
        }
    )
    assert review_resp.status_code == 200
    assert "NovaCore" in review_resp.json()["cover_letter"]

    # 4. Candidate Confirms Submission
    submit_resp = client.post(
        f"/api/v1/applications/{app_id}/submit",
        json={"submission_type": "manual", "candidate_confirmed": True}
    )
    assert submit_resp.status_code == 200
    submitted_data = submit_resp.json()
    assert submitted_data["status"] == "submitted"
    assert submitted_data["submitted_at"] is not None

    # 5. Check Audit Trail Events
    events_resp = client.get(f"/api/v1/applications/{app_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 3
    event_types = [e["event_type"] for e in events]
    assert "created" in event_types
    assert "submission_attempt" in event_types
