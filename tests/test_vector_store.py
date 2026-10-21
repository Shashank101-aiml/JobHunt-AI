import pytest
import numpy as np

from app.vector_store.embedder import get_embedding, get_embeddings
from app.vector_store.chroma_client import chroma_client

def test_embedder_dimensionality_and_non_constant():
    vec1 = get_embedding("Senior Python Backend Developer with FastAPI and Docker")
    vec2 = get_embedding("Financial Accountant specializing in Corporate Tax Law")
    
    # Must have 384 dimensions (all-MiniLM-L6-v2)
    assert len(vec1) == 384
    assert len(vec2) == 384
    
    # Must not be constant dummy vectors
    assert not all(x == 0.1 for x in vec1)
    assert vec1 != vec2
    
    # Cosine similarity between related query and vec1 should be higher than vec2
    query_vec = get_embedding("Python API engineering")
    dot1 = np.dot(query_vec, vec1) / (np.linalg.norm(query_vec) * np.linalg.norm(vec1))
    dot2 = np.dot(query_vec, vec2) / (np.linalg.norm(query_vec) * np.linalg.norm(vec2))
    assert dot1 > dot2

def test_chroma_client_chunk_indexing_and_search():
    test_id = 8888
    resume_text = "Architected high-throughput services with FastAPI, SQLAlchemy, and Redis."
    profile = {
        "summary": "Distributed systems engineer with cloud focus",
        "skills": ["Python", "FastAPI", "Redis", "SQLAlchemy"],
        "experience": [
            {
                "title": "Lead Backend Engineer",
                "company": "ScaleAI",
                "highlights": ["Built distributed data pipelines handling 10M records daily."]
            }
        ]
    }

    chroma_client.add_resume(test_id, resume_text, profile)

    try:
        # Search for FastAPI should match the skills or full text chunk
        matches = chroma_client.search_similar_resume_sections("FastAPI backend services", resume_id=test_id, n_results=3)
        assert len(matches) > 0
        assert any("FastAPI" in m["text"] for m in matches)
        assert matches[0]["similarity"] > 0.3
    finally:
        chroma_client.delete_resume(test_id)
