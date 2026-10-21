import re

def extract_keywords(text: str) -> list:
    words = re.findall(r'\b[A-Z][a-zA-Z0-9+#]+\b', text)
    return list(set(words))

def calculate_match_score(jd_keywords: list, resume_text: str) -> float:
    if not jd_keywords:
        return 85.0
    matched = sum(1 for kw in jd_keywords if kw.lower() in resume_text.lower())
    score = (matched / len(jd_keywords)) * 100
    return round(min(100.0, max(10.0, score)), 2)
