import re
from typing import Dict, Any, List, Tuple
from app.schemas.job import StructuredJobDescription
from app.schemas.resume import StructuredResumeProfile
from app.schemas.application import ATSFeedback, SubscoreBreakdown
from app.vector_store.chroma_client import chroma_client

def calculate_ats_score(
    resume_text: str,
    resume_profile: Dict[str, Any],
    structured_jd: Dict[str, Any],
    resume_id: int = None
) -> ATSFeedback:
    """
    Evidence-based ATS scoring engine comparing an actual resume against an actual job description.
    
    Formula Weights:
      - Required Skills Match: 40%
      - Preferred Skills Match: 15%
      - Experience / YoE Alignment: 20%
      - Keyword & Term Density: 15%
      - Section & Profile Completeness: 10%
    """
    resume_lower = resume_text.lower()
    
    # 1. Required Skills Match (Weight 40%)
    req_skills = structured_jd.get("required_skills", [])
    matched_req = []
    missing_req = []
    semantic_matches = []
    
    for skill in req_skills:
        skill_pat = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(skill_pat, resume_lower):
            matched_req.append(skill)
        else:
            # Check for semantic match in ChromaDB if available
            sem_found = False
            if resume_id:
                similar_chunks = chroma_client.search_similar_resume_sections(skill, resume_id=resume_id, n_results=1)
                if similar_chunks and similar_chunks[0]["similarity"] > 0.45:
                    semantic_matches.append(f"{skill} (semantic match in: {similar_chunks[0]['text'][:40]}...)")
                    sem_found = True
            if not sem_found:
                missing_req.append(skill)

    if req_skills:
        req_score = ((len(matched_req) * 1.0 + len(semantic_matches) * 0.7) / len(req_skills)) * 100.0
    else:
        req_score = 100.0  # Not penalized if no required skills are stated in JD

    # 2. Preferred Skills Match (Weight 15%)
    pref_skills = structured_jd.get("preferred_skills", [])
    matched_pref = []
    missing_pref = []
    
    for skill in pref_skills:
        skill_pat = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(skill_pat, resume_lower):
            matched_pref.append(skill)
        else:
            missing_pref.append(skill)

    if pref_skills:
        pref_score = (len(matched_pref) / len(pref_skills)) * 100.0
    else:
        pref_score = 100.0  # Full marks if no preferred skills specified

    # 3. Experience Match (Weight 20%)
    jd_min_yoe = structured_jd.get("min_years_experience")
    # Estimate candidate YoE from experience items or text
    exp_items = resume_profile.get("experience", [])
    candidate_yoe = len(exp_items) * 2  # Heuristic 2 years per listed position if dates ambiguous
    
    # Try finding explicit years in resume
    yoe_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)', resume_lower)
    if yoe_match:
        try:
            candidate_yoe = max(candidate_yoe, int(yoe_match.group(1)))
        except ValueError:
            pass

    if jd_min_yoe and jd_min_yoe > 0:
        if candidate_yoe >= jd_min_yoe:
            exp_score = 100.0
        else:
            exp_score = min(100.0, (candidate_yoe / jd_min_yoe) * 100.0)
    else:
        exp_score = 100.0

    # 4. Keyword & Term Density (Weight 15%)
    jd_keywords = structured_jd.get("keywords", [])
    if jd_keywords:
        kw_matches = sum(1 for kw in jd_keywords if re.search(r'(?<![a-zA-Z0-9])' + re.escape(kw.lower()) + r'(?![a-zA-Z0-9])', resume_lower))
        kw_score = (kw_matches / len(jd_keywords)) * 100.0
    else:
        kw_score = 80.0

    # 5. Section & Profile Completeness (Weight 10%)
    comp_points = 0.0
    contact = resume_profile.get("contact_info", {})
    if contact.get("email"):
        comp_points += 25.0
    if contact.get("phone") or contact.get("linkedin"):
        comp_points += 25.0
    if exp_items:
        comp_points += 25.0
    if resume_profile.get("skills"):
        comp_points += 25.0
    completeness_score = comp_points

    # Final Weighted Score Calculation
    total_score = (
        (req_score * 0.40) +
        (pref_score * 0.15) +
        (exp_score * 0.20) +
        (kw_score * 0.15) +
        (completeness_score * 0.10)
    )
    final_score = round(min(100.0, max(0.0, total_score)), 2)

    subscores = SubscoreBreakdown(
        required_skills_match=round(req_score, 2),
        preferred_skills_match=round(pref_score, 2),
        experience_match=round(exp_score, 2),
        keyword_density=round(kw_score, 2),
        section_completeness=round(completeness_score, 2)
    )

    # Actionable Suggestions
    suggestions = []
    if missing_req:
        suggestions.append(f"Add experience or projects highlighting missing required skills: {', '.join(missing_req[:4])}.")
    if missing_pref:
        suggestions.append(f"Consider adding preferred skills if you have relevant exposure: {', '.join(missing_pref[:3])}.")
    if jd_min_yoe and candidate_yoe < jd_min_yoe:
        suggestions.append(f"Job requires {jd_min_yoe}+ years of experience; emphasize cumulative project depth and scope.")
    if not contact.get("linkedin"):
        suggestions.append("Add a LinkedIn profile URL to your contact section.")
    if not resume_profile.get("summary"):
        suggestions.append("Include a 2-3 sentence executive summary tailored to this target role.")
    if not suggestions:
        suggestions.append("Strong candidate alignment! Ensure key achievements include measurable metrics.")

    evidence = {
        "candidate_estimated_yoe": candidate_yoe,
        "jd_required_yoe": jd_min_yoe,
        "matched_required_count": len(matched_req),
        "total_required_count": len(req_skills),
        "matched_preferred_count": len(matched_pref),
        "total_preferred_count": len(pref_skills),
        "semantic_matches": semantic_matches
    }

    all_matched = matched_req + [f"{s} (Preferred)" for s in matched_pref] + semantic_matches

    return ATSFeedback(
        score=final_score,
        subscores=subscores,
        matched_skills=all_matched,
        missing_skills=missing_req,
        evidence=evidence,
        suggestions=suggestions
    )
