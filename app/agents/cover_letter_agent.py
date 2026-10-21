from app.services.cover_letter_service import generate_cover_letter as generate_letter

def generate_cover_letter(state: dict) -> dict:
    """
    Cover Letter Agent Node in the LangGraph pipeline.
    Produces personalized letter from candidate profile and structured JD.
    """
    resume_text = state.get("tailored_resume") or state.get("resume_text", "")
    resume_profile = state.get("resume_profile", {})
    structured_jd = state.get("structured_jd", {})
    
    letter = generate_letter(
        resume_text=resume_text,
        resume_profile=resume_profile,
        structured_jd=structured_jd
    )
    
    return {
        "cover_letter": letter,
        "status": "cover_letter_complete"
    }
