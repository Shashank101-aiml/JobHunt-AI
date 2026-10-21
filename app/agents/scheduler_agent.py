from typing import Dict, Any
from app.config import settings

def schedule_followup(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review & Finalization Node in the LangGraph pipeline.
    Prepares the application review package.
    Does NOT falsely mark applications as submitted without verified adapter or user approval.
    """
    if state.get("error"):
        return {"status": "failed"}

    user_approved = state.get("user_approved", False)
    
    if not user_approved:
        # Awaiting candidate review before submission
        return {
            "status": "ready_for_review"
        }

    # If candidate approved, handle post-submission scheduling only if email is enabled
    app_id = state.get("application_id", 0)
    if settings.EMAIL_ENABLED:
        try:
            from app.tasks.follow_up_task import send_followup_reminder
            # Schedule follow-up check after 3 days (259200 seconds)
            send_followup_reminder.apply_async(args=[app_id], countdown=259200)
        except Exception as e:
            print(f"Could not enqueue Celery reminder task: {e}")

    return {
        "status": state.get("status", "ready_for_review")
    }
