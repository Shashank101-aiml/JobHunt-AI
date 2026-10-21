import os
import re
from typing import List, Dict, Any, Tuple
import pypdf
import docx

from app.schemas.resume import (
    StructuredResumeProfile,
    ContactInfo,
    EducationItem,
    ExperienceItem,
)

# Standard skills taxonomy for exact keyword boundary extraction
KNOWN_SKILLS = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Go", "Golang", "Java", "C++", "C#", "Ruby", "Rust",
    "PHP", "SQL", "HTML", "CSS", "Bash", "Shell", "R", "Scala", "Kotlin", "Swift",
    # Frameworks & Libraries
    "FastAPI", "Django", "Flask", "React", "React.js", "Vue", "Vue.js", "Angular", "Next.js",
    "Node.js", "Express", "Spring Boot", "PyTorch", "TensorFlow", "Scikit-Learn", "Pandas",
    "NumPy", "LangChain", "LangGraph", "LlamaIndex", "Celery", "SQLAlchemy", "Alembic", "TailwindCSS",
    # Databases & Storage
    "PostgreSQL", "Postgres", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
    "Cassandra", "DynamoDB", "ChromaDB", "Pinecone", "Milvus", "Qdrant",
    # Cloud & DevOps
    "Docker", "Kubernetes", "AWS", "GCP", "Google Cloud", "Azure", "Terraform", "CI/CD",
    "GitHub Actions", "GitLab CI", "Linux", "Git", "Nginx", "Prometheus", "Grafana",
    # Concepts & Architecture
    "REST", "RESTful APIs", "GraphQL", "Microservices", "Event-Driven", "WebSockets",
    "RAG", "LLM", "Prompt Engineering", "NLP", "Machine Learning", "Deep Learning",
    "Vector Search", "Unit Testing", "TDD", "Agile", "Scrum", "Playwright", "Selenium"
]

def extract_text_from_pdf(filepath: str) -> str:
    """Extract raw text from PDF file with validation."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    text_parts = []
    try:
        reader = pypdf.PdfReader(filepath)
        if len(reader.pages) == 0:
            raise ValueError("PDF file contains no pages.")
        for page_idx, page in enumerate(reader.pages):
            content = page.extract_text()
            if content:
                text_parts.append(content.strip())
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Corrupted or unreadable PDF: {str(e)}")

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("Could not extract readable text from PDF (file may be empty or scanned image).")
    return full_text

def extract_text_from_docx(filepath: str) -> str:
    """Extract raw text from DOCX file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    try:
        doc = docx.Document(filepath)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
    except Exception as e:
        raise ValueError(f"Corrupted or unreadable DOCX: {str(e)}")
        
    full_text = "\n".join(paragraphs).strip()
    if not full_text:
        raise ValueError("DOCX document is empty or contains no readable text.")
    return full_text

def extract_text_from_txt(filepath: str) -> str:
    """Extract raw text from plain text file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read().strip()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            text = f.read().strip()
    except Exception as e:
        raise ValueError(f"Error reading text file: {str(e)}")
        
    if not text:
        raise ValueError("Text file is empty.")
    return text

def extract_text_by_type(filepath: str, file_ext: str) -> str:
    """Dispatches text extraction according to normalized extension."""
    ext = file_ext.lower().lstrip(".")
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(filepath)
    elif ext in ("txt", "text", "md"):
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Supported formats: PDF, DOCX, TXT")

def extract_contact_info(raw_text: str) -> ContactInfo:
    """Extracts contact info using deterministic regex without hallucination."""
    info = ContactInfo()
    
    # Email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', raw_text)
    if email_match:
        info.email = email_match.group(0)

    # Phone
    phone_match = re.search(r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?', raw_text)
    if phone_match and phone_match.group(0).strip():
        matched_str = phone_match.group(0).strip()
        if len(re.sub(r'\D', '', matched_str)) >= 10:
            info.phone = matched_str

    # LinkedIn
    linkedin_match = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)', raw_text, re.IGNORECASE)
    if linkedin_match:
        info.linkedin = linkedin_match.group(0)

    # GitHub
    github_match = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)', raw_text, re.IGNORECASE)
    if github_match:
        info.github = github_match.group(0)

    # Candidate Name (heuristic: first non-empty line with 2-4 words that isn't a header or email)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    for line in lines[:5]:
        if any(keyword in line.lower() for keyword in ["resume", "curriculum vitae", "cv", "page", "email", "@", "http"]):
            continue
        words = line.split()
        if 1 <= len(words) <= 4 and all(w[0].isupper() or w[0].isalpha() for w in words if w):
            info.name = line
            break

    return info

def extract_skills_nlp(raw_text: str) -> List[str]:
    """Extracts confirmed industry skills based on strict boundary token matching."""
    found_skills = []
    text_lower = f" {raw_text.lower()} "
    
    for skill in KNOWN_SKILLS:
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
            
    # Remove duplicates preserving order
    unique_skills = []
    for s in found_skills:
        if s not in unique_skills:
            unique_skills.append(s)
            
    return unique_skills

def extract_sections(raw_text: str) -> Dict[str, str]:
    """Splits resume text into standardized section chunks."""
    section_patterns = {
        "summary": r'\b(?:summary|professional summary|profile|about me|objective)\b',
        "skills": r'\b(?:skills|technical skills|technologies|core competencies|competencies)\b',
        "experience": r'\b(?:work experience|experience|professional experience|employment history|employment)\b',
        "education": r'\b(?:education|academic background|qualifications)\b',
        "projects": r'\b(?:projects|personal projects|key projects)\b',
        "certifications": r'\b(?:certifications|certificates|licenses)\b'
    }
    
    sections = {}
    lines = raw_text.split("\n")
    current_section = "header"
    buffer = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        matched_section = None
        # Check if line looks like a header (short, title-like)
        if len(stripped.split()) <= 4 and len(stripped) < 40:
            for s_name, pat in section_patterns.items():
                if re.fullmatch(pat, stripped.lower()):
                    matched_section = s_name
                    break
                    
        if matched_section:
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = matched_section
            buffer = []
        else:
            buffer.append(stripped)
            
    if buffer:
        sections[current_section] = "\n".join(buffer).strip()
        
    return sections

def extract_education_items(edu_text: str) -> List[EducationItem]:
    """Parses education lines into structured items."""
    items = []
    if not edu_text:
        return items
        
    lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
    for line in lines:
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', line)
        degree_match = re.search(r'\b(bachelor|master|phd|b\.?s\.?|m\.?s\.?|b\.?tech|m\.?tech|associate)\b', line, re.IGNORECASE)
        
        if degree_match or year_match or any(k in line.lower() for k in ["university", "college", "institute", "school"]):
            items.append(EducationItem(
                degree=degree_match.group(0).title() if degree_match else None,
                institution=line[:100],
                graduation_year=year_match.group(0) if year_match else None
            ))
    return items

def extract_experience_items(exp_text: str) -> List[ExperienceItem]:
    """Parses work experience blocks into structured items."""
    items = []
    if not exp_text:
        return items
        
    lines = [l.strip() for l in exp_text.split("\n") if l.strip()]
    current_item: Dict[str, Any] = None
    
    for line in lines:
        # Check if line looks like a job header: contains year / date or common role
        date_match = re.search(r'\b(?:19\d{2}|20\d{2})\s*(?:-|–|to)\s*(?:19\d{2}|20\d{2}|present|current)\b', line, re.IGNORECASE)
        is_bullet = line.startswith(("-", "•", "*", "–")) or (current_item and len(line) > 50)
        
        if date_match or (not is_bullet and any(role in line.lower() for role in ["engineer", "developer", "lead", "architect", "manager", "intern", "analyst"])):
            if current_item:
                items.append(ExperienceItem(**current_item))
            current_item = {
                "title": line[:100],
                "company": None,
                "duration": date_match.group(0) if date_match else None,
                "highlights": []
            }
        elif current_item:
            bullet_clean = re.sub(r'^[-•*–\s]+', '', line).strip()
            if bullet_clean:
                current_item["highlights"].append(bullet_clean)
                
    if current_item:
        items.append(ExperienceItem(**current_item))
        
    return items

def parse_resume_document(filepath: str, filename: str) -> Tuple[str, StructuredResumeProfile, List[str]]:
    """Complete resume extraction and parsing pipeline."""
    ext = os.path.splitext(filename)[1]
    raw_text = extract_text_by_type(filepath, ext)
    
    contact_info = extract_contact_info(raw_text)
    skills = extract_skills_nlp(raw_text)
    sections = extract_sections(raw_text)
    
    education = extract_education_items(sections.get("education", ""))
    experience = extract_experience_items(sections.get("experience", ""))
    summary = sections.get("summary", "")[:500] if "summary" in sections else None
    
    profile = StructuredResumeProfile(
        contact_info=contact_info,
        summary=summary,
        skills=skills,
        education=education,
        experience=experience,
        projects=[],
        certifications=[]
    )
    
    return raw_text, profile, skills
