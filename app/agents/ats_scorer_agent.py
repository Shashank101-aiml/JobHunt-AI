from app.utils.ats_scorer import calculate_ats_score

def score_ats(state: dict) -> dict:
    """
    ATS Scorer Node in the LangGraph pipeline.
    Calculates transparent, evidence-based match score between resume and structured JD.
    """
    resume_text = state.get("tailored_resume") or state.get("resume_text", "")
    resume_profile = state.get("resume_profile", {})
    structured_jd = state.get("structured_jd", {})
    resume_id = state.get("resume_id")
    
    feedback = calculate_ats_score(
        resume_text=resume_text,
        resume_profile=resume_profile,
        structured_jd=structured_jd,
        resume_id=resume_id
    )
    
    return {
        "ats_score": feedback.score,
        "ats_feedback": feedback.model_dump(),
        "status": "scoring_complete"
    }
