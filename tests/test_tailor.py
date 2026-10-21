import pytest
import os
import tempfile
from app.services.tailor_service import tailor_resume_content, export_tailored_resume_docx, build_tailoring_prompt
from app.agents.tailor_agent import tailor_resume

def test_tailor_prompt_guardrails():
    system_prompt, user_prompt = build_tailoring_prompt(
        resume_text="Senior Python dev at AlphaCorp (2020-2024)",
        structured_jd={"title": "Lead Backend Dev", "required_skills": ["Python", "Docker"]},
        relevant_chunks=[{"text": "Built Python microservices"}],
        missing_skills=["Kubernetes"]
    )
    assert "FACTUAL INTEGRITY" in system_prompt
    assert "MUST NOT invent" in system_prompt
    assert "AlphaCorp" in user_prompt
    assert "Python" in user_prompt

def test_tailor_resume_workflow():
    state = {
        "resume_text": "Experienced developer skilled in Python and FastAPI. 4 years at DataCo.",
        "resume_profile": {"skills": ["Python", "FastAPI"], "experience": [{"title": "Dev"}]},
        "structured_jd": {"title": "FastAPI Architect", "required_skills": ["Python", "FastAPI", "Docker"]},
        "resume_id": 1,
        "ats_feedback": {"score": 60.0, "missing_skills": ["Docker"]}
    }
    res = tailor_resume(state)
    assert "tailored_resume" in res
    assert res["status"] == "tailoring_complete"
    assert "tailored_diff" in res
    assert len(res["tailored_diff"]["changes_summary"]) > 0

def test_export_tailored_resume_docx():
    with tempfile.NamedTemporaryFile("wb", suffix=".docx", delete=False) as f:
        temp_docx = f.name

    try:
        sample_tailored = "Alex Rivera\nSenior Engineer\n\nPROFESSIONAL SUMMARY\nExperienced backend engineer.\n\nTECHNICAL SKILLS\n- Python\n- FastAPI"
        export_tailored_resume_docx(sample_tailored, temp_docx)
        assert os.path.exists(temp_docx)
        assert os.path.getsize(temp_docx) > 500  # Valid docx file
    finally:
        if os.path.exists(temp_docx):
            os.remove(temp_docx)
