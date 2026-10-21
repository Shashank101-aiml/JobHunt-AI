import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SyncSessionLocal, Base, sync_engine
from app.models.resume import Resume
from app.services.resume_parser import parse_resume_document
from app.vector_store.chroma_client import chroma_client

def main():
    parser = argparse.ArgumentParser(description="Seed resume file into DB and ChromaDB vector index")
    parser.add_argument("--file", default="data/resumes/sample_resume.txt", help="Path to resume file (PDF, DOCX, TXT)")
    args = parser.parse_args()

    filepath = os.path.abspath(args.file)
    if not os.path.exists(filepath):
        print(f"Error: Specified resume file '{filepath}' does not exist.")
        sys.exit(1)

    filename = os.path.basename(filepath)
    print(f"Reading and parsing resume: {filename} ({filepath})...")

    try:
        raw_text, profile, skills = parse_resume_document(filepath, filename)
    except Exception as e:
        print(f"Error parsing resume file: {e}")
        sys.exit(1)

    # Ensure tables exist
    Base.metadata.create_all(bind=sync_engine)

    db = SyncSessionLocal()
    try:
        # Mark other resumes as inactive
        db.query(Resume).update({"is_active": False})
        
        file_size = os.path.getsize(filepath)
        ext = os.path.splitext(filename)[1].lstrip(".")
        
        resume = Resume(
            filename=filename,
            filepath=filepath,
            file_type=ext,
            file_size_bytes=file_size,
            raw_text=raw_text,
            parsed_skills=", ".join(skills),
            structured_profile=profile.model_dump(),
            is_active=True
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        # Add to ChromaDB vector store
        chroma_client.add_resume(resume.id, raw_text, profile=profile.model_dump())
        
        print(f"\nSuccessfully seeded Resume ID: {resume.id}")
        print(f"- Candidate Name: {profile.contact_info.name or 'Not specified'}")
        print(f"- Email: {profile.contact_info.email or 'Not specified'}")
        print(f"- Extracted Skills ({len(skills)}): {', '.join(skills[:8])}{'...' if len(skills) > 8 else ''}")
        print(f"- Text Length: {len(raw_text)} chars")
        print(f"- Vector Store Status: Indexed in ChromaDB")
    finally:
        db.close()

if __name__ == "__main__":
    main()
