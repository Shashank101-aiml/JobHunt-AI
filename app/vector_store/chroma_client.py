import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.vector_store.embedder import get_embedding_function

class ChromaClient:
    """
    Manages persistent ChromaDB vector storage, document chunking,
    and semantic similarity retrieval.
    """

    def __init__(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.embedding_fn = get_embedding_function()
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.resume_collection = self.client.get_or_create_collection(
            name="resume_chunks",
            embedding_function=self.embedding_fn
        )
        self.job_collection = self.client.get_or_create_collection(
            name="job_postings",
            embedding_function=self.embedding_fn
        )

    def add_resume(self, resume_id: int, raw_text: str, profile: Optional[Dict[str, Any]] = None):
        """
        Chunks and indexes a resume document for granular semantic retrieval.
        Creates vectors for summary, skills, and each experience bullet.
        """
        # First remove any stale chunks for this resume_id
        self.delete_resume(resume_id)

        documents = []
        metadatas = []
        ids = []

        # 1. Full document snapshot
        full_doc = raw_text[:2000]
        documents.append(full_doc)
        metadatas.append({"resume_id": resume_id, "section": "full_text", "index": 0})
        ids.append(f"res_{resume_id}_full")

        # 2. Structured profile chunks if available
        if profile:
            summary = profile.get("summary")
            if summary:
                documents.append(summary)
                metadatas.append({"resume_id": resume_id, "section": "summary", "index": 0})
                ids.append(f"res_{resume_id}_summary")

            skills = profile.get("skills", [])
            if skills:
                skills_doc = f"Technical Skills: {', '.join(skills)}"
                documents.append(skills_doc)
                metadatas.append({"resume_id": resume_id, "section": "skills", "index": 0})
                ids.append(f"res_{resume_id}_skills")

            experience_items = profile.get("experience", [])
            for idx, exp in enumerate(experience_items):
                title = exp.get("title", "")
                company = exp.get("company", "")
                highlights = exp.get("highlights", [])
                exp_text = f"Role: {title} at {company or 'Company'}. Highlights: " + " ".join(highlights)
                if len(exp_text.strip()) > 20:
                    documents.append(exp_text)
                    metadatas.append({"resume_id": resume_id, "section": "experience", "index": idx})
                    ids.append(f"res_{resume_id}_exp_{idx}")

        self.resume_collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_similar_resume_sections(
        self,
        query: str,
        resume_id: Optional[int] = None,
        n_results: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most semantically relevant resume chunks matching a job requirement or skill query.
        Optionally filters by specific resume_id.
        """
        count = self.resume_collection.count()
        if count == 0 or not query.strip():
            return []

        where_filter = {"resume_id": resume_id} if resume_id is not None else None
        
        limit = min(n_results, count)
        try:
            results = self.resume_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []

        matched_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            dists = results["distances"][0] if "distances" in results else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, dists):
                matched_chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": float(dist),
                    "similarity": round(max(0.0, 1.0 - (float(dist) / 2.0)), 4)
                })

        return matched_chunks

    def add_job(self, job_id: int, raw_description: str, structured: Optional[Dict[str, Any]] = None):
        """Indexes job description and required qualifications for semantic matching."""
        self.delete_job(job_id)

        docs = [raw_description[:2500]]
        metas = [{"job_id": job_id, "type": "full_description"}]
        ids = [f"job_{job_id}_full"]

        if structured:
            req_skills = structured.get("required_skills", [])
            responsibilities = structured.get("responsibilities", [])
            req_text = f"Job Requirements: {', '.join(req_skills)}. Responsibilities: " + " ".join(responsibilities[:5])
            if len(req_text) > 30:
                docs.append(req_text)
                metas.append({"job_id": job_id, "type": "requirements"})
                ids.append(f"job_{job_id}_reqs")

        self.job_collection.upsert(
            documents=docs,
            metadatas=metas,
            ids=ids
        )

    def delete_resume(self, resume_id: int):
        """Removes all chunks associated with a resume_id."""
        try:
            self.resume_collection.delete(where={"resume_id": resume_id})
        except Exception:
            pass

    def delete_job(self, job_id: int):
        """Removes all chunks associated with a job_id."""
        try:
            self.job_collection.delete(where={"job_id": job_id})
        except Exception:
            pass

chroma_client = ChromaClient()
