from app.tasks.celery_app import celery_app
from app.services.email_service import send_email, validate_email_address
from app.database import SyncSessionLocal
from app.models.application import Application, ApplicationEvent
from app.models.resume import Resume
from app.config import settings

@celery_app.task(name="process_job_application_task")
def process_job_application_task(app_id: int, job_url: str = None, resume_id: int = None):
    from app.orchestrator.runner import run_pipeline_sync
    return run_pipeline_sync(app_id=app_id, job_url=job_url, resume_id=resume_id)

@celery_app.task(name="send_followup_reminder")
def send_followup_reminder(app_id: int):
    """
    Enqueues and dispatches an authentic candidate reminder for an applied position.
    Validates recipient and logs outcomes to the ApplicationEvent audit trail.
    """
    db = SyncSessionLocal()
    try:
        app_record = db.query(Application).filter(Application.id == app_id).first()
        if not app_record:
            return "Application record not found"
            
        if app_record.status != "submitted":
            return f"Follow-up skipped: application status is '{app_record.status}', not 'submitted'."

        # Resolve candidate recipient
        candidate_email = None
        if app_record.resume_id:
            res = db.query(Resume).filter(Resume.id == app_record.resume_id).first()
            if res and res.structured_profile:
                candidate_email = res.structured_profile.get("contact_info", {}).get("email")
                
        candidate_email = candidate_email or settings.CANDIDATE_EMAIL

        if not candidate_email or not validate_email_address(candidate_email):
            event = ApplicationEvent(
                application_id=app_id,
                event_type="email_skipped",
                message="Follow-up reminder skipped: no valid candidate recipient email address configured.",
                details={"reason": "invalid_or_missing_email"}
            )
            db.add(event)
            db.commit()
            return "Follow-up skipped: invalid or missing recipient email."

        job_name = app_record.job_title or app_record.company or "the position"
        subject = f"Follow-up reminder: Application for {job_name}"
        body = (
            f"Hello,\n\n"
            f"This is an automated reminder regarding your application for {job_name} at {app_record.company or 'the company'}.\n"
            f"Job Link: {app_record.job_url}\n\n"
            f"It has been 3 business days since submission. Consider checking in on your application status.\n\n"
            f"Best regards,\nJob-hunt AI Assistant"
        )

        success, msg = send_email(to_email=candidate_email, subject=subject, body=body)

        event = ApplicationEvent(
            application_id=app_id,
            event_type="email_sent" if success else "email_failed",
            message=msg,
            details={"recipient": candidate_email, "success": success}
        )
        db.add(event)
        db.commit()

        return msg
    finally:
        db.close()
