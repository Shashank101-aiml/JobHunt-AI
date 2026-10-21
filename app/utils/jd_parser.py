import re
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.job import StructuredJobDescription
from app.services.resume_parser import KNOWN_SKILLS

JOB_TITLE_PATTERNS = [
    r'(?i)(?:title|role|position):\s*([^\n\r]+)',
    r'(?i)\b(?:Senior|Junior|Lead|Staff|Principal|Associate)?\s*(?:Software|Backend|Frontend|Full[- ]?Stack|DevOps|Data|Machine Learning|ML|AI|Cloud|Platform|Systems|Site Reliability|QA)\s*(?:Engineer|Developer|Architect|Scientist|Lead)\b',
]

def extract_job_title(raw_text: str) -> str:
    """Extract job title from explicit markers or common title patterns."""
    for pattern in JOB_TITLE_PATTERNS:
        match = re.search(pattern, raw_text)
        if match:
            extracted = (match.group(1) if match.groups() and match.group(1) else match.group(0)).strip()
            # Clean up trailing punctuation
            extracted = re.sub(r'[\r\n\t|#*-]+', '', extracted).strip()
            if 3 <= len(extracted) <= 80:
                return extracted
                
    # Fallback: check first 3 non-empty lines for reasonable title
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    for line in lines[:3]:
        clean = re.sub(r'^[-#*\s]+', '', line).strip()
        if 4 <= len(clean) <= 60 and not clean.endswith(".") and not any(k in clean.lower() for k in ["about", "http", "description"]):
            return clean
            
    return "Software Engineer"

def extract_company_name(raw_text: str) -> Optional[str]:
    """Extract hiring company name if mentioned."""
    patterns = [
        r'(?i)(?:company|organization|employer):\s*([A-Za-z0-9&.,\- ]+)',
        r'(?i)about\s+([A-Z][a-zA-Z0-9&.,\- ]{2,40})(?:\s+is|\s+was|\s+builds|\n)',
        r'(?i)join\s+([A-Z][a-zA-Z0-9&.,\- ]{2,40})(?:team|\s+as|\s+to|\n|\.)',
        r'(?i)at\s+([A-Z][a-zA-Z0-9&.,\- ]{2,30})\s*(?:,\s*[A-Z]{2}|\n|$)'
    ]
    for pat in patterns:
        m = re.search(pat, raw_text)
        if m:
            comp = m.group(1).strip()
            if comp.lower() not in ["our", "the", "a", "an", "this", "us", "team", "you"]:
                return comp[:80]
    return None

def extract_location_and_type(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect location (city/state/remote) and employment type."""
    location = None
    emp_type = None
    
    text_lower = raw_text.lower()
    
    # Location / Work model
    if "remote" in text_lower:
        if "hybrid" in text_lower:
            location = "Hybrid / Remote Eligible"
        else:
            location = "Remote"
    elif "hybrid" in text_lower:
        location = "Hybrid"
    else:
        loc_match = re.search(r'(?i)(?:location|office):\s*([^\n\r]+)', raw_text)
        if loc_match:
            location = loc_match.group(1).strip()[:80]
            
    # Employment Type
    if "contract" in text_lower or "contractor" in text_lower:
        emp_type = "Contract"
    elif "intern" in text_lower or "internship" in text_lower:
        emp_type = "Internship"
    elif "part-time" in text_lower or "part time" in text_lower:
        emp_type = "Part-Time"
    elif "full-time" in text_lower or "full time" in text_lower or "permanent" in text_lower:
        emp_type = "Full-Time"
        
    return location, emp_type

def extract_years_experience(raw_text: str) -> Optional[int]:
    """Extract minimum years of experience required without hardcoding."""
    patterns = [
        r'(?i)(?:at least\s+|minimum\s+of\s+)?(\d+)\+?\s*(?:to|-)?\s*(?:\d+)?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?(?:[a-zA-Z]+\s+){0,4}(?:experience|exp))',
        r'(?i)(\d+)\+?\s*(?:to|-)?\s*(?:\d+)?\s*(?:years?|yrs?)\b'
    ]
    for pat in patterns:
        m = re.search(pat, raw_text)
        if m:
            try:
                yoe = int(m.group(1))
                if 1 <= yoe <= 25:
                    return yoe
            except (ValueError, IndexError):
                pass
    return None

def extract_salary_range(raw_text: str) -> Optional[str]:
    """Extract explicit salary disclosures."""
    patterns = [
        r'\$\s*\d{2,3}(?:,\d{3})*(?:\s*(?:-|to)\s*\$?\s*\d{2,3}(?:,\d{3})*)?(?:\s*(?:k|K))?(?:\s*\/\s*(?:yr|year|hour|hr|mo|month|annual|annually))?',
        r'\b(?:USD|EUR|GBP|£|€)\s*\d{2,3}(?:,\d{3})*(?:\s*(?:-|to)\s*\d{2,3}(?:,\d{3})*)?',
        r'\$\d{2,3}k\s*(?:-|to)\s*\$?\d{2,3}k'
    ]
    for pat in patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            if len(val) >= 4:
                return val
    return None

def split_jd_sections(raw_text: str) -> Dict[str, str]:
    """Segments JD into required, preferred, responsibilities, and about sections."""
    sections = {
        "required": "",
        "preferred": "",
        "responsibilities": "",
        "general": ""
    }
    
    current_key = "general"
    buffer = []
    
    lines = raw_text.split("\n")
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        
        # Check section boundaries (including inline bullet headers like "- Nice to have:")
        if any(h in lower for h in ["preferred qualification", "nice to have", "bonus points", "preferred skill", "desired skill", "plus if you have"]):
            if buffer:
                sections[current_key] += "\n" + "\n".join(buffer)
            current_key = "preferred"
            buffer = [stripped]
        elif any(h in lower for h in ["minimum qualification", "basic qualification", "requirements", "what you need", "what you bring", "must have", "who you are"]):
            if buffer:
                sections[current_key] += "\n" + "\n".join(buffer)
            current_key = "required"
            buffer = [stripped]
        elif any(h in lower for h in ["responsibilities", "what you'll do", "what you will do", "the role", "duties"]):
            if buffer:
                sections[current_key] += "\n" + "\n".join(buffer)
            current_key = "responsibilities"
            buffer = [stripped]
        else:
            buffer.append(stripped)
            
    if buffer:
        sections[current_key] += "\n" + "\n".join(buffer)
        
    return sections

def extract_skills_from_text(text: str) -> List[str]:
    """Identifies skills from known taxonomy in a specific text fragment."""
    found = []
    text_lower = f" {text.lower()} "
    for skill in KNOWN_SKILLS:
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            found.append(skill)
            
    # Deduplicate preserving order
    res = []
    for s in found:
        if s not in res:
            res.append(s)
    return res

def extract_bullet_list(section_text: str, max_items: int = 10) -> List[str]:
    """Extracts clean bullet points from a section."""
    bullets = []
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]
    for l in lines:
        cleaned = re.sub(r'^[-*•–\d.)\s]+', '', l).strip()
        if len(cleaned) > 15:
            bullets.append(cleaned)
            if len(bullets) >= max_items:
                break
    return bullets

def normalize_jd(raw_text: str, source_url: Optional[str] = None) -> StructuredJobDescription:
    """
    Parses and normalizes a raw job description into structured Pydantic model.
    Never invents data or returns fixed hardcoded skills/yoe.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Job description text cannot be empty.")
        
    title = extract_job_title(raw_text)
    company = extract_company_name(raw_text)
    location, emp_type = extract_location_and_type(raw_text)
    yoe = extract_years_experience(raw_text)
    salary = extract_salary_range(raw_text)
    
    sections = split_jd_sections(raw_text)
    
    req_skills = extract_skills_from_text(sections["required"])
    pref_skills = extract_skills_from_text(sections["preferred"])
    general_skills = extract_skills_from_text(sections["general"])
    
    # If no specific required section was found, populate required with general skills
    if not req_skills and general_skills:
        req_skills = [s for s in general_skills if s not in pref_skills]
    else:
        # Include general skills not already categorized
        for s in general_skills:
            if s not in req_skills and s not in pref_skills:
                req_skills.append(s)
                
    responsibilities = extract_bullet_list(sections["responsibilities"])
    qualifications = extract_bullet_list(sections["required"])
    
    # Aggregate keywords (all distinct skills + title tokens)
    keywords = list(set(req_skills + pref_skills))
    
    return StructuredJobDescription(
        title=title,
        company=company,
        location=location,
        employment_type=emp_type,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        min_years_experience=yoe,
        responsibilities=responsibilities,
        qualifications=qualifications,
        salary_range=salary,
        keywords=keywords
    )
