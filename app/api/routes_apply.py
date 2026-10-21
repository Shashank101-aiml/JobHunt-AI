from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_async_db
from app.models.application import Application, ApplicationEvent
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusResponse,
    MatchEvaluationRequest,
    MatchEvaluationResponse,
    ATSFeedback
)
from app.schemas.job import StructuredJobDescription
from app.utils.jd_parser import normalize_jd
from app.utils.ats_scorer import calculate_ats_score
from app.services.job_scrapers import scraper_registry, ScraperError, RestrictedJobSourceError
from app.orchestrator.runner import trigger_pipeline_async, run_pipeline_sync

router = APIRouter()

@router.post("/apply", response_model=ApplicationResponse)
async def apply_for_job(
    req: ApplicationCreate,
    sync_execution: bool = Query(True, description="Run synchronously so result is ready immediately"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Initiates job processing and application pipeline.
    Accepts job_url, pre-saved job_id, or direct job_text.
    Deduplicates active applications and loads the active resume if resume_id is not specified.
    """
    # 1. Resolve Resume
    resume_id = req.resume_id
    if not resume_id:
        res_active = await db.execute(select(Resume).where(Resume.is_active == True).order_by(Resume.created_at.desc()))
        active_resume = res_active.scalar_one_or_none()
        if not active_resume:
            res_latest = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
            active_resume = res_latest.scalar_one_or_none()
        if not active_resume:
            raise HTTPException(status_code=400, detail="No resume available. Please upload a resume before starting an application.")
        resume_id = active_resume.id
    else:
        res_chk = await db.execute(select(Resume).where(Resume.id == resume_id))
        if not res_chk.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Resume ID {resume_id} not found.")

    # 2. Resolve Job source & metadata
    job_url = req.job_url or ""
    job_title = None
    company = None
    job_id = req.job_id
    
    if job_id:
        j_res = await db.execute(select(Job).where(Job.id == job_id))
        job_obj = j_res.scalar_one_or_none()
        if not job_obj:
            raise HTTPException(status_code=404, detail=f"Job ID {job_id} not found.")
        job_url = job_obj.source_url or job_url or f"urn:job:{job_id}"
        job_title = job_obj.title
        company = job_obj.company
    elif not job_url and req.job_text:
        job_url = f"manual-entry-{len(req.job_text)}"
    elif not job_url and not req.job_text:
        raise HTTPException(status_code=400, detail="Must provide job_url, job_id, or job_text.")

    # 3. Duplicate Prevention
    dup_query = select(Application).where(
        Application.resume_id == resume_id,
        Application.job_url == job_url,
        Application.status.notin_(["rejected", "failed"])
    )
    dup_res = await db.execute(dup_query)
    existing_app = dup_res.scalar_one_or_none()
    if existing_app:
        return existing_app

    # 4. Create Application in 'draft' state
    app_db = Application(
        job_id=job_id,
        job_url=job_url,
        job_title=job_title,
        company=company,
        resume_id=resume_id,
        status="draft"
    )
    db.add(app_db)
    await db.commit()
    await db.refresh(app_db)

    # Initial Audit Event
    event = ApplicationEvent(
        application_id=app_db.id,
        event_type="created",
        message="Application record created in draft status.",
        details={"job_url": job_url, "resume_id": resume_id}
    )
    db.add(event)
    await db.commit()

    # 5. Trigger Pipeline
    if sync_execution:
        run_pipeline_sync(
            app_id=app_db.id,
            job_url=req.job_url,
            resume_id=resume_id,
            job_text=req.job_text,
            job_id=job_id
        )
        await db.refresh(app_db)
    else:
        trigger_pipeline_async(
            app_id=app_db.id,
            job_url=req.job_url,
            resume_id=resume_id,
            job_text=req.job_text,
            job_id=job_id
        )

    return app_db

@router.get("/status/{app_id}", response_model=ApplicationStatusResponse)
async def get_application_status(app_id: int, db: AsyncSession = Depends(get_async_db)):
    """Retrieve lightweight status and score for a specific application."""
    res = await db.execute(select(Application).where(Application.id == app_id))
    app_db = res.scalar_one_or_none()
    if not app_db:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_db

@router.post("/match/evaluate", response_model=MatchEvaluationResponse)
async def evaluate_job_match(
    req: MatchEvaluationRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Evaluates candidate resume against target job description without creating an application.
    Calculates transparent ATS score, subscores, matched skills, and recommendations.
    """
    # 1. Resolve Resume
    resume_id = req.resume_id
    if not resume_id:
        res_active = await db.execute(select(Resume).where(Resume.is_active == True).order_by(Resume.created_at.desc()))
        resume = res_active.scalar_one_or_none()
        if not resume:
            res_latest = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
            resume = res_latest.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=400, detail="No resume available. Please upload a resume first.")
    else:
        res_chk = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = res_chk.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume ID {resume_id} not found.")

    # 2. Resolve Job Description
    structured: StructuredJobDescription = None
    if req.job_id:
        j_res = await db.execute(select(Job).where(Job.id == req.job_id))
        job_obj = j_res.scalar_one_or_none()
        if not job_obj:
            raise HTTPException(status_code=404, detail=f"Job ID {req.job_id} not found.")
        if job_obj.structured_jd:
            structured = StructuredJobDescription(**job_obj.structured_jd)
        else:
            structured = normalize_jd(job_obj.raw_description, source_url=job_obj.source_url)
    elif req.job_text:
        structured = normalize_jd(req.job_text, source_url=req.job_url)
    elif req.job_url:
        try:
            scraped = await scraper_registry.scrape_job(req.job_url)
            structured = normalize_jd(scraped.raw_description, source_url=req.job_url)
        except RestrictedJobSourceError as rje:
            raise HTTPException(status_code=403, detail=str(rje))
        except ScraperError as se:
            raise HTTPException(status_code=422, detail=str(se))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape job URL: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Must provide job_id, job_text, or job_url.")

    # 3. Calculate transparent ATS score
    feedback = calculate_ats_score(
        resume_text=resume.raw_text,
        resume_profile=resume.structured_profile or {},
        structured_jd=structured.model_dump(),
        resume_id=resume.id
    )

    return MatchEvaluationResponse(
        job_title=structured.title or "Software Engineer",
        company=structured.company,
        ats_score=feedback.score,
        feedback=feedback,
        required_skills=structured.required_skills,
        preferred_skills=structured.preferred_skills,
        min_years_experience=structured.min_years_experience
    )

