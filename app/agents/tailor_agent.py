from app.vector_store.chroma_client import chroma_client
from app.services.tailor_service import tailor_resume_content

def tailor_resume(state: dict) -> dict:
    """
    Tailor Agent Node in the LangGraph pipeline.
    Queries ChromaDB for semantically relevant resume chunks and performs factual tailoring.
    """
    resume_text = state.get("resume_text", "")
    resume_profile = state.get("resume_profile", {})
    structured_jd = state.get("structured_jd", {})
    resume_id = state.get("resume_id")
    before_feedback = state.get("ats_feedback", {})
    
    # Semantic retrieval from ChromaDB
    req_skills = structured_jd.get("required_skills", [])
    query = " ".join(req_skills[:6]) if req_skills else structured_jd.get("title", "Software Engineer")
    relevant_chunks = chroma_client.search_similar_resume_sections(
        query=query,
        resume_id=resume_id,
        n_results=4
    )
    
    tailor_result = tailor_resume_content(
        resume_text=resume_text,
        resume_profile=resume_profile,
        structured_jd=structured_jd,
        relevant_chunks=relevant_chunks,
        before_feedback=before_feedback,
        resume_id=resume_id
    )
    
    return {
        "tailored_resume": tailor_result["tailored_text"],
        "tailored_diff": {
            "mode": tailor_result["mode"],
            "changes_summary": tailor_result["changes_summary"],
            "before_score": tailor_result["before_score"],
            "after_score": tailor_result["after_score"],
            "missing_requirements": tailor_result["missing_requirements"]
        },
        "status": "tailoring_complete"
    }
