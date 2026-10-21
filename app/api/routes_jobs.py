from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func

from app.database import get_async_db
from app.models.job import Job
from app.schemas.job import (
    JobCreateManual,
    JobScrapeRequest,
    JobResponse,
    PaginatedJobsResponse
)
from app.services.job_scrapers import scraper_registry, ScraperError, RestrictedJobSourceError
from app.services.job_scrapers.base import normalize_url
from app.utils.jd_parser import normalize_jd
from app.vector_store.chroma_client import chroma_client

router = APIRouter()

@router.post("/jobs/scrape", response_model=JobResponse)
async def scrape_job_posting(req: JobScrapeRequest, db: AsyncSession = Depends(get_async_db)):
    """
    Scrapes a job posting from a public URL using the modular scraper registry.
    Deduplicates by canonical URL and persists normalized job details.
    """
    canonical = normalize_url(req.url)
    
    # Check if already scraped
    existing = await db.execute(select(Job).where(Job.source_url == canonical))
    existing_job = existing.scalar_one_or_none()
    if existing_job:
        return existing_job

    try:
        scraped = await scraper_registry.scrape_job(req.url)
    except RestrictedJobSourceError as rje:
        raise HTTPException(status_code=403, detail=str(rje))
    except ScraperError as se:
        raise HTTPException(status_code=422, detail=str(se))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error while scraping job: {str(e)}")

    structured = normalize_jd(scraped.raw_description, source_url=req.url)
    
    job_db = Job(
        title=structured.title or scraped.title,
        company=structured.company or scraped.company,
        location=structured.location or scraped.location,
        employment_type=structured.employment_type or scraped.employment_type,
        source=scraped.source,
        source_url=canonical,
        raw_description=scraped.raw_description,
        structured_jd=structured.model_dump(),
        status="active"
    )
    db.add(job_db)
    await db.commit()
    await db.refresh(job_db)

    # Index in ChromaDB for semantic matching
    try:
        chroma_client.add_job(job_db.id, job_db.raw_description, structured=structured.model_dump())
    except Exception as e:
        print(f"Warning: Failed to index job in vector store: {e}")

    return job_db

@router.post("/jobs/manual", response_model=JobResponse)
async def create_manual_job(req: JobCreateManual, db: AsyncSession = Depends(get_async_db)):
    """
    Manually add a job description (for sites with login barriers, CAPTCHAs, or offline descriptions).
    """
    if not req.description_text or len(req.description_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description text is too short or empty.")
        
    canonical = normalize_url(req.source_url) if req.source_url else None
    if canonical:
        existing = await db.execute(select(Job).where(Job.source_url == canonical))
        existing_job = existing.scalar_one_or_none()
        if existing_job:
            return existing_job

    structured = normalize_jd(req.description_text, source_url=req.source_url)
    
    job_db = Job(
        title=req.title or structured.title,
        company=req.company or structured.company,
        location=req.location or structured.location,
        employment_type=req.employment_type or structured.employment_type,
        source="manual_entry",
        source_url=canonical,
        raw_description=req.description_text,
        structured_jd=structured.model_dump(),
        status="active"
    )
    db.add(job_db)
    await db.commit()
    await db.refresh(job_db)

    try:
        chroma_client.add_job(job_db.id, job_db.raw_description, structured=structured.model_dump())
    except Exception as e:
        print(f"Warning: Failed to index job in vector store: {e}")

    return job_db

@router.get("/jobs", response_model=PaginatedJobsResponse)
async def list_jobs(
    search: Optional[str] = Query(None, description="Search keyword in title or company"),
    location: Optional[str] = Query(None, description="Filter by location or remote"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List jobs with pagination and optional search filters."""
    query = select(Job)
    count_query = select(func.count(Job.id))

    if search:
        search_filter = or_(
            Job.title.ilike(f"%{search}%"),
            Job.company.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if location:
        loc_filter = Job.location.ilike(f"%{location}%")
        query = query.where(loc_filter)
        count_query = count_query.where(loc_filter)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    items = res.scalars().all()

    return PaginatedJobsResponse(total=total, items=items)

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_async_db)):
    """Retrieve full details of a specific job by ID."""
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
