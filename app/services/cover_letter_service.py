from typing import Dict, Any
from app.services.llm_client import llm_client

def generate_cover_letter(
    resume_text: str,
    resume_profile: Dict[str, Any],
    structured_jd: Dict[str, Any]
) -> str:
    """
    Generates a personalized, professional cover letter matching actual resume facts to the target role.
    """
    candidate_name = resume_profile.get("contact_info", {}).get("name") or "Applicant"
    job_title = structured_jd.get("title", "Software Engineer")
    company = structured_jd.get("company", "the Hiring Team")
    skills = ", ".join(structured_jd.get("required_skills", [])[:5]) or "modern software engineering"

    if llm_client.is_configured():
        system_prompt = (
            "You are a professional career advisor crafting a compelling, concise cover letter.\n"
            "STRICT RULES: Use ONLY facts, companies, and skills present in the candidate's resume. "
            "Never invent qualifications. Keep to 3 paragraphs (Opening hook, relevant experience, closing)."
        )
        prompt = f"""Candidate Name: {candidate_name}
Target Role: {job_title}
Target Company: {company}
Key Required Technologies: {skills}

Candidate Resume:
{resume_text[:2000]}

Write a polished, professional cover letter from {candidate_name} applying for the {job_title} role at {company}."""

        try:
            return llm_client.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=1000)
        except Exception:
            pass

    # Structured professional template fallback based on real candidate data
    exp_items = resume_profile.get("experience", [])
    recent_role = exp_items[0].get("title", "Software Engineer") if exp_items else "Software Engineer"
    recent_company = exp_items[0].get("company", "previous roles") if exp_items else "industry"
    top_skills = ", ".join(resume_profile.get("skills", [])[:4]) or skills

    letter = f"""Dear Hiring Team at {company},

I am writing to express my strong interest in the {job_title} position. With my background in {recent_role} at {recent_company} and hands-on expertise in {top_skills}, I am excited about the opportunity to contribute to your engineering initiatives.

Throughout my experience, I have focused on building scalable, reliable backend solutions and collaborating within high-performance teams. Your requirements for {skills} align closely with my technical foundation and daily development practices.

I would welcome the opportunity to discuss how my experience and problem-solving skills can support your goals at {company}. Thank you for your time and consideration.

Sincerely,
{candidate_name}"""

    return letter
