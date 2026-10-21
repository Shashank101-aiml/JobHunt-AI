import pytest
from app.orchestrator.graph import pipeline_graph

def test_pipeline_graph_execution_to_ready_for_review():
    initial_state = {
        "application_id": 1,
        "job_id": None,
        "job_url": "",
        "job_text": "Title: Senior Backend Developer\nRequirements:\n- Python, FastAPI, Docker, PostgreSQL\nNice to have:\n- Redis, Kubernetes\nExperience: 4+ years",
        "resume_id": 1,
        "raw_jd": "",
        "structured_jd": {},
        "resume_text": "Alex Rivera\nSenior Python Engineer with 6 years experience in Python, FastAPI, Docker, PostgreSQL.",
        "resume_profile": {
            "contact_info": {"name": "Alex Rivera", "email": "alex@rivera.dev"},
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "experience": [{"title": "Senior Engineer", "duration": "2019 - Present"}]
        },
        "relevant_chunks": [],
        "tailored_resume": "",
        "tailored_diff": {},
        "cover_letter": "",
        "ats_score": 0.0,
        "ats_feedback": {},
        "status": "pending",
        "user_approved": False,
        "submission_type": "manual",
        "submission_result": None,
        "error": None
    }
    
    final_state = pipeline_graph.invoke(initial_state)
    
    # Must reach ready_for_review (not blindly marked as submitted or applied)
    assert final_state["status"] == "ready_for_review"
    assert final_state["ats_score"] > 50.0
    assert len(final_state["tailored_resume"]) > 20
    assert len(final_state["cover_letter"]) > 30
    assert "changes_summary" in final_state["tailored_diff"]

def test_pipeline_graph_stops_early_on_scraping_error():
    initial_state = {
        "application_id": 2,
        "job_id": None,
        "job_url": "https://www.linkedin.com/jobs/view/restricted-123",
        "job_text": None,
        "resume_id": 1,
        "raw_jd": "",
        "structured_jd": {},
        "resume_text": "Python Engineer",
        "resume_profile": {},
        "relevant_chunks": [],
        "tailored_resume": "",
        "tailored_diff": {},
        "cover_letter": "",
        "ats_score": 0.0,
        "ats_feedback": {},
        "status": "pending",
        "user_approved": False,
        "submission_type": "manual",
        "submission_result": None,
        "error": None
    }
    
    final_state = pipeline_graph.invoke(initial_state)
    assert final_state["status"] == "failed"
    assert "restricted" in final_state["error"].lower()
