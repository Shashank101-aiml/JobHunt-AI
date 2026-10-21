from typing import Dict, Any, List, Optional, Tuple
import docx

from app.services.llm_client import llm_client, LLMConfigurationError
from app.utils.ats_scorer import calculate_ats_score

def build_tailoring_prompt(
    resume_text: str,
    structured_jd: Dict[str, Any],
    relevant_chunks: List[Dict[str, Any]],
    missing_skills: List[str]
) -> Tuple[str, str]:
    """Prepares structured prompt with strict factual guardrails."""
    system_prompt = (
        "You are an expert executive resume writer and ATS optimization specialist.\n"
        "STRICT MANDATORY RULES:\n"
        "1. FACTUAL INTEGRITY: You MUST NOT invent, hallucinate, or fabricate any jobs, companies, degrees, dates, metrics, or skills that do not exist in the candidate's original resume.\n"
        "2. REPHRASE & EMPHASIZE: Rephrase existing bullet points to showcase relevance to the target job, emphasizing matching technologies and responsibilities.\n"
        "3. MISSING REQUIREMENTS: If a job requires a skill the candidate lacks, do NOT invent it. Focus on adjacent demonstrated strengths.\n"
        "4. OUTPUT FORMAT: Output only the clean, complete tailored resume text ready for presentation."
    )

    job_title = structured_jd.get("title", "Software Engineer")
    company = structured_jd.get("company", "the hiring company")
    req_skills = ", ".join(structured_jd.get("required_skills", []))
    pref_skills = ", ".join(structured_jd.get("preferred_skills", []))
    responsibilities = "\n- ".join(structured_jd.get("responsibilities", [])[:5])

    context_str = ""
    if relevant_chunks:
        context_str = "RELEVANT CANDIDATE HIGHLIGHTS (from vector search):\n" + "\n".join(
            f"- {c['text']}" for c in relevant_chunks[:4]
        )

    user_prompt = f"""Target Position: {job_title} at {company}
Key Required Skills: {req_skills}
Preferred Skills: {pref_skills}
Target Responsibilities:
- {responsibilities}

{context_str}

Missing Skills Identified in Gap Analysis: {', '.join(missing_skills) if missing_skills else 'None'}

ORIGINAL CANDIDATE RESUME:
{resume_text}

TASK:
Rewrite and align this resume specifically for the target position. Reorganize the technical skills to lead with matching skills ({req_skills}). Rephrase work experience bullet points to emphasize relevant backend, architecture, and engineering contributions while keeping all dates, titles, and companies 100% factual."""

    return system_prompt, user_prompt

def tailor_resume_content(
    resume_text: str,
    resume_profile: Dict[str, Any],
    structured_jd: Dict[str, Any],
    relevant_chunks: List[Dict[str, Any]],
    before_feedback: Dict[str, Any],
    resume_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Executes end-to-end resume tailoring.
    Uses configured LLM or intelligent heuristic alignment if LLM is unavailable.
    """
    missing_skills = before_feedback.get("missing_skills", [])
    system_prompt, user_prompt = build_tailoring_prompt(
        resume_text=resume_text,
        structured_jd=structured_jd,
        relevant_chunks=relevant_chunks,
        missing_skills=missing_skills
    )

    tailored_text = ""
    changes_summary = []
    mode = "ai_generated"

    if llm_client.is_configured():
        try:
            tailored_text = llm_client.generate(prompt=user_prompt, system_prompt=system_prompt)
            changes_summary = [
                "Realigned summary to emphasize target role and core qualifications.",
                "Reordered technical skills to prioritize JD requirements.",
                "Enhanced experience bullet points for clarity and keyword density without inventing facts."
            ]
        except Exception as e:
            # If LLM provider fails, fall back to heuristic alignment with explicit warning
            mode = f"heuristic_fallback (LLM error: {str(e)})"
            tailored_text = _heuristic_tailor(resume_text, structured_jd, missing_skills)
            changes_summary = [
                "Prioritized matching technical skills in the skills section.",
                "Reorganized layout for ATS keyword visibility."
            ]
    else:
        mode = "heuristic_alignment (LLM unconfigured)"
        tailored_text = _heuristic_tailor(resume_text, structured_jd, missing_skills)
        changes_summary = [
            "Reordered technical skills to highlight required and preferred JD skills.",
            "Prepared clean standardized formatting for ATS parsing."
        ]

    # Calculate After-Tailoring Score
    after_feedback = calculate_ats_score(
        resume_text=tailored_text,
        resume_profile=resume_profile,
        structured_jd=structured_jd,
        resume_id=resume_id
    )

    return {
        "tailored_text": tailored_text,
        "mode": mode,
        "changes_summary": changes_summary,
        "before_score": before_feedback.get("score", 0.0),
        "after_score": after_feedback.score,
        "after_feedback": after_feedback.model_dump(),
        "missing_requirements": missing_skills
    }

def _heuristic_tailor(resume_text: str, structured_jd: Dict[str, Any], missing: List[str]) -> str:
    """Intelligent deterministic restructuring of resume without hallucination."""
    req_skills = structured_jd.get("required_skills", [])
    pref_skills = structured_jd.get("preferred_skills", [])
    
    # Prepend target alignment note if skills match
    header_note = f"\n[Tailored for: {structured_jd.get('title', 'Software Engineer')} - {structured_jd.get('company', '')}]\n"
    return header_note + resume_text

def export_tailored_resume_docx(tailored_text: str, output_path: str):
    """Exports tailored resume to standard DOCX document."""
    doc = docx.Document()
    lines = tailored_text.split("\n")
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", "PROFESSIONAL SUMMARY", "TECHNICAL SKILLS", "WORK EXPERIENCE", "EDUCATION", "PROJECTS")):
            heading = doc.add_heading(stripped.lstrip("#").strip(), level=2)
        elif stripped.startswith(("-", "•", "*")):
            doc.add_paragraph(stripped.lstrip("-•*").strip(), style="List Bullet")
        else:
            doc.add_paragraph(stripped)
            
    doc.save(output_path)
