import os
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func

from app.database import get_async_db
from app.models.application import Application, ApplicationEvent
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.application import (
    ApplicationResponse,
    ApplicationReviewUpdate,
    ApplicationSubmitRequest,
    ApplicationEventResponse,
    PaginatedApplicationsResponse,
    DashboardStatsResponse
)
from app.services.submission import get_submission_adapter, SubmissionPackage
from app.services.tailor_service import export_tailored_resume_docx

router = APIRouter()

VALID_STATUSES = {
    "draft",
    "ready_for_review",
    "submission_in_progress",
    "submitted",
    "interviewing",
    "rejected",
    "offer",
    "requires_manual_action",
    "failed"
}

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_async_db)):
    """Retrieve real aggregated stats for the dashboard."""
    # 1. Total jobs
    total_jobs_res = await db.execute(select(func.count(Job.id)))
    total_jobs = total_jobs_res.scalar() or 0

    # 2. Total applications
    total_apps_res = await db.execute(select(func.count(Application.id)))
    total_apps = total_apps_res.scalar() or 0

    # 3. Awaiting review / action
    awaiting_res = await db.execute(
        select(func.count(Application.id)).where(
            Application.status.in_(["ready_for_review", "requires_manual_action", "draft"])
        )
    )
    awaiting_review = awaiting_res.scalar() or 0

    # 4. Submitted
    submitted_res = await db.execute(
        select(func.count(Application.id)).where(Application.status == "submitted")
    )
    submitted = submitted_res.scalar() or 0

    # 5. Interviewing
    interview_res = await db.execute(
        select(func.count(Application.id)).where(Application.status == "interviewing")
    )
    interviewing = interview_res.scalar() or 0

    # 6. Average match score
    avg_score_res = await db.execute(
        select(func.avg(Application.ats_score)).where(Application.ats_score.isnot(None))
    )
    avg_score_val = avg_score_res.scalar()
    avg_score = round(float(avg_score_val), 1) if avg_score_val is not None else None

    # 7. Status distribution
    dist_res = await db.execute(
        select(Application.status, func.count(Application.id)).group_by(Application.status)
    )
    status_distribution = {row[0]: row[1] for row in dist_res.all()}

    return DashboardStatsResponse(
        total_jobs=total_jobs,
        total_applications=total_apps,
        awaiting_review=awaiting_review,
        submitted=submitted,
        interviewing=interviewing,
        average_match_score=avg_score,
        status_distribution=status_distribution
    )

@router.get("/applications", response_model=PaginatedApplicationsResponse)
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status (e.g., ready_for_review, submitted)"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    search: Optional[str] = Query(None, description="Search query in job title or company"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """List applications with pagination and filters."""
    query = select(Application)
    count_query = select(func.count(Application.id))

    if status:
        query = query.where(Application.status == status)
        count_query = count_query.where(Application.status == status)

    if company:
        query = query.where(Application.company.ilike(f"%{company}%"))
        count_query = count_query.where(Application.company.ilike(f"%{company}%"))

    if search:
        search_filter = or_(
            Application.job_title.ilike(f"%{search}%"),
            Application.company.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Application.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    items = res.scalars().all()

    return PaginatedApplicationsResponse(total=total, items=items)

@router.get("/applications/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: int, db: AsyncSession = Depends(get_async_db)):
    """Retrieve full details of an application including tailored resume, diff, and score."""
    res = await db.execute(select(Application).where(Application.id == app_id))
    app_db = res.scalar_one_or_none()
    if not app_db:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_db

@router.patch("/applications/{app_id}", response_model=ApplicationResponse)
async def update_application_status(
    app_id: int,
    status: Optional[str] = Query(None, description="New valid status"),
    notes: Optional[str] = Query(None, description="Application notes"),
    db: AsyncSession = Depends(get_async_db)
):
    """Update status or notes with validation and audit logging."""
    res = await db.execute(select(Application).where(Application.id == app_id))
    app_db = res.scalar_one_or_none()
    if not app_db:
        raise HTTPException(status_code=404, detail="Application not found")

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid statuses: {', '.join(sorted(VALID_STATUSES))}"
            )
        old_status = app_db.status
        app_db.status = status
        
        event = ApplicationEvent(
            application_id=app_id,
            event_type="status_changed",
            message=f"Status changed from '{old_status}' to '{status}'",
            details={"old_status": old_status, "new_status": status}
        )
        db.add(event)

    if notes is not None:
        app_db.notes = notes

    await db.commit()
    await db.refresh(app_db)
    return app_db

@router.post("/applications/{app_id}/review", response_model=ApplicationResponse)
async def review_and_edit_application(
    app_id: int,
    req: ApplicationReviewUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Save candidate edits to tailored resume text and cover letter."""
    res = await db.execute(select(Application).where(Application.id == app_id))
    app_db = res.scalar_one_or_none()
    if not app_db:
        raise HTTPException(status_code=404, detail="Application not found")

    if req.tailored_resume_text is not None:
        app_db.tailored_resume_text = req.tailored_resume_text
    if req.cover_letter is not None:
        app_db.cover_letter = req.cover_letter
    if req.notes is not None:
        app_db.notes = req.notes

    event = ApplicationEvent(
        application_id=app_id,
        event_type="review_updated",
        message="Candidate edited and saved tailored application content.",
        details={"has_resume_edits": bool(req.tailored_resume_text), "has_letter_edits": bool(req.cover_letter)}
    )
    db.add(event)
    await db.commit()
    await db.refresh(app_db)
    return app_db

@router.post("/applications/{app_id}/submit", response_model=ApplicationResponse)
async def submit_application(
    app_id: int,
    req: ApplicationSubmitRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submits application using authorized adapter.
    Requires explicit candidate confirmation before transitioning to 'submitted'.
    """
    res = await db.execute(select(Application).where(Application.id == app_id))
    app_db = res.scalar_one_or_none()
    if not app_db:
        raise HTTPException(status_code=404, detail="Application not found")

    # Load candidate info
    res_obj = None
    if app_db.resume_id:
        r_res = await db.execute(select(Resume).where(Resume.id == app_db.resume_id))
        res_obj = r_res.scalar_one_or_none()

    candidate_name = res_obj.structured_profile.get("contact_info", {}).get("name") if (res_obj and res_obj.structured_profile) else "Candidate"
    candidate_email = res_obj.structured_profile.get("contact_info", {}).get("email") if (res_obj and res_obj.structured_profile) else None

    # Prepare submission package
    package = SubmissionPackage(
        application_id=app_db.id,
        job_title=app_db.job_title or "Software Engineer",
        company=app_db.company or "Company",
        job_url=app_db.job_url,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        tailored_resume_text=app_db.tailored_resume_text or (res_obj.raw_text if res_obj else ""),
        cover_letter=app_db.cover_letter
    )

    adapter = get_submission_adapter(req.submission_type)
    result = await adapter.submit(package, user_confirmed=req.candidate_confirmed)

    app_db.status = result.status
    app_db.submission_type = req.submission_type
    app_db.submission_response = result.model_dump()
    if result.is_submitted:
        app_db.submitted_at = datetime.now(timezone.utc)

    event = ApplicationEvent(
        application_id=app_id,
        event_type="submission_attempt",
        message=result.message,
        details=result.details
    )
    db.add(event)
    await db.commit()
    await db.refresh(app_db)
    return app_db

@router.get("/applications/{app_id}/events", response_model=List[ApplicationEventResponse])
async def get_application_events(app_id: int, db: AsyncSession = Depends(get_async_db)):
    """Retrieve chronological activity log and audit history for an application."""
    res = await db.execute(
        select(ApplicationEvent).where(ApplicationEvent.application_id == app_id).order_by(ApplicationEvent.created_at.desc())
    )
    return res.scalars().all()

@router.get("/applications/{app_id}/export-resume")
@router.get("/applications/{app_id}/download-docx")
async def export_application_resume(app_id: int, db: AsyncSession = Depends(get_async_db)):
    """Downloads the tailored resume as a formatted DOCX document."""
    res = await db.execute(select(Application).where(Application.id == app_id))
    app_db = res.scalar_one_or_none()
    if not app_db or not app_db.tailored_resume_text:
        raise HTTPException(status_code=404, detail="Tailored resume not found for this application.")

    export_dir = "./data/exports"
    os.makedirs(export_dir, exist_ok=True)
    filename = f"tailored_resume_app_{app_id}.docx"
    filepath = os.path.join(export_dir, filename)

    export_tailored_resume_docx(app_db.tailored_resume_text, filepath)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
