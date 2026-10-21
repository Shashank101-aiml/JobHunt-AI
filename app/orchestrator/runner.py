from datetime import datetime
from typing import Optional, Dict, Any

import app.database
from app.models.application import Application, ApplicationEvent
from app.models.resume import Resume
from app.models.job import Job
from app.orchestrator.graph import pipeline_graph

def run_pipeline_sync(
    app_id: int,
    job_url: Optional[str] = None,
    resume_id: Optional[int] = None,
    job_text: Optional[str] = None,
    job_id: Optional[int] = None,
    user_approved: bool = False
) -> Dict[str, Any]:
    """
    Synchronous execution of the LangGraph agent pipeline.
    Updates application state, feedback, diffs, and creates audit trail events.
    """
    app_record = None
    db = app.database.SyncSessionLocal()
    try:
        app_record = db.query(Application).filter(Application.id == app_id).first()
        
        # 1. Resolve Resume
        res = None
        if resume_id:
            res = db.query(Resume).filter(Resume.id == resume_id).first()
        if not res:
            res = db.query(Resume).filter(Resume.is_active == True).order_by(Resume.created_at.desc()).first()
        if not res:
            res = db.query(Resume).order_by(Resume.created_at.desc()).first()
            
        resume_text = res.raw_text if res else "Professional Software Engineer with full-stack and cloud experience."
        resume_profile = res.structured_profile if res and res.structured_profile else {}
        actual_resume_id = res.id if res else 1

        # 2. Resolve Job details if job_id was linked
        raw_jd = job_text or ""
        structured_jd = {}
        target_url = job_url or ""
        
        if job_id:
            job_obj = db.query(Job).filter(Job.id == job_id).first()
            if job_obj:
                raw_jd = job_obj.raw_description
                structured_jd = job_obj.structured_jd or {}
                target_url = job_obj.source_url or target_url

        initial_state = {
            "application_id": app_id,
            "job_id": job_id,
            "job_url": target_url,
            "job_text": raw_jd,
            "resume_id": actual_resume_id,
            "raw_jd": raw_jd,
            "structured_jd": structured_jd,
            "resume_text": resume_text,
            "resume_profile": resume_profile,
            "relevant_chunks": [],
            "tailored_resume": "",
            "tailored_diff": {},
            "cover_letter": "",
            "ats_score": 0.0,
            "ats_feedback": {},
            "status": "processing",
            "user_approved": user_approved,
            "submission_type": app_record.submission_type if app_record else "manual",
            "submission_result": None,
            "error": None
        }

        if app_record:
            app_record.status = "processing"
            app_record.resume_id = actual_resume_id
            db.commit()

        # Execute LangGraph Pipeline
        final_state = pipeline_graph.invoke(initial_state)

        if app_record:
            if final_state.get("error"):
                app_record.status = "failed"
                event = ApplicationEvent(
                    application_id=app_id,
                    event_type="error",
                    message=f"Pipeline failed: {final_state['error']}",
                    details={"error": final_state["error"]}
                )
                db.add(event)
            else:
                app_record.status = final_state.get("status", "ready_for_review")
                app_record.ats_score = final_state.get("ats_score")
                app_record.ats_feedback = final_state.get("ats_feedback")
                app_record.tailored_resume_text = final_state.get("tailored_resume")
                app_record.tailored_resume_diff = final_state.get("tailored_diff")
                app_record.cover_letter = final_state.get("cover_letter")
                
                title = final_state.get("structured_jd", {}).get("title")
                company = final_state.get("structured_jd", {}).get("company")
                if title:
                    app_record.job_title = title
                if company:
                    app_record.company = company

                event = ApplicationEvent(
                    application_id=app_id,
                    event_type="analyzed_and_tailored",
                    message=f"Pipeline completed with ATS score {app_record.ats_score}%. Review package ready.",
                    details={
                        "ats_score": app_record.ats_score,
                        "tailoring_mode": final_state.get("tailored_diff", {}).get("mode", "standard")
                    }
                )
                db.add(event)
                
            db.commit()

        return final_state
    except Exception as e:
        if app_record:
            app_record.status = "failed"
            db.commit()
        raise e
    finally:
        db.close()

def trigger_pipeline_async(
    app_id: int,
    job_url: Optional[str] = None,
    resume_id: Optional[int] = None,
    job_text: Optional[str] = None,
    job_id: Optional[int] = None
):
    """
    Attempts to enqueue Celery task; seamlessly falls back to sync execution if Celery/Redis is offline.
    """
    try:
        from app.tasks.follow_up_task import process_job_application_task
        process_job_application_task.delay(app_id, job_url, resume_id)
    except Exception:
        run_pipeline_sync(
            app_id=app_id,
            job_url=job_url,
            resume_id=resume_id,
            job_text=job_text,
            job_id=job_id
        )
