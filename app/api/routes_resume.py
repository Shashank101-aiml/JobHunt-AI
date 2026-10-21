import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.database import get_async_db
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse, ResumeActivateRequest
from app.services.resume_parser import parse_resume_document
from app.vector_store.chroma_client import chroma_client

router = APIRouter()
RESUME_DIR = "./data/resumes"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

@router.post("/upload-resume", response_model=ResumeResponse)
@router.post("/resumes", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    set_active: bool = Query(True, description="Mark as the active candidate resume"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Accepts PDF, DOCX, or TXT resume files.
    Performs real text extraction and NLP entity extraction without hardcoding.
    """
    filename = file.filename or "uploaded_resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
        
    os.makedirs(RESUME_DIR, exist_ok=True)
    filepath = os.path.join(RESUME_DIR, filename)
    
    # Read file content safely
    content = await file.read()
    file_size = len(content)
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 10MB limit.")
        
    with open(filepath, "wb") as buffer:
        buffer.write(content)
        
    try:
        raw_text, profile, skills = parse_resume_document(filepath, filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

    # If setting active, deactivate existing resumes
    if set_active:
        await db.execute(update(Resume).values(is_active=False))

    resume_db = Resume(
        filename=filename,
        filepath=filepath,
        file_type=ext.lstrip("."),
        file_size_bytes=file_size,
        raw_text=raw_text,
        parsed_skills=", ".join(skills),
        structured_profile=profile.model_dump(),
        is_active=set_active
    )
    db.add(resume_db)
    await db.commit()
    await db.refresh(resume_db)
    
    # Index in ChromaDB for semantic retrieval
    try:
        chroma_client.add_resume(resume_db.id, raw_text, profile=profile.model_dump())
    except Exception as e:
        # Non-fatal to DB commit, but log warning
        print(f"Warning: Failed to index resume in vector store: {e}")
        
    return resume_db

@router.get("/resumes", response_model=List[ResumeResponse])
async def list_resumes(db: AsyncSession = Depends(get_async_db)):
    """List all candidate resumes stored in the database."""
    res = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    return res.scalars().all()

@router.get("/resumes/active", response_model=ResumeResponse)
async def get_active_resume(db: AsyncSession = Depends(get_async_db)):
    """Get the currently active candidate resume."""
    res = await db.execute(select(Resume).where(Resume.is_active == True).order_by(Resume.created_at.desc()))
    active_resume = res.scalar_one_or_none()
    if not active_resume:
        # Fall back to latest resume
        res_latest = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
        active_resume = res_latest.scalar_one_or_none()
    if not active_resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload a resume first.")
    return active_resume

@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get details of a specific resume."""
    res = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = res.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume

@router.post("/resumes/{resume_id}/activate", response_model=ResumeResponse)
async def activate_resume(resume_id: int, db: AsyncSession = Depends(get_async_db)):
    """Mark a specific resume as active for future job matches and applications."""
    res = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = res.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    await db.execute(update(Resume).values(is_active=False))
    resume.is_active = True
    await db.commit()
    await db.refresh(resume)
    return resume

@router.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_async_db)):
    """Delete a resume and its vector store entries."""
    res = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = res.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    await db.delete(resume)
    await db.commit()
    
    try:
        chroma_client.delete_resume(resume_id)
    except Exception:
        pass
        
    return {"status": "deleted", "id": resume_id}
