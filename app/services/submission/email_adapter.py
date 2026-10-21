from datetime import datetime
from app.services.submission.base import BaseSubmissionAdapter, SubmissionPackage, SubmissionResult
from app.services.email_service import send_email, is_smtp_configured, validate_email_address

class EmailSubmissionAdapter(BaseSubmissionAdapter):
    """
    Submits application directly via email to hiring email addresses.
    Requires candidate approval and valid SMTP credentials.
    """

    def can_handle(self, submission_type: str) -> bool:
        return submission_type == "email"

    async def submit(self, package: SubmissionPackage, user_confirmed: bool) -> SubmissionResult:
        recipient = package.candidate_email  # Or employer email passed in metadata
        
        if not user_confirmed:
            return SubmissionResult(
                status="ready_for_review",
                is_submitted=False,
                message="Email application draft ready. Explicit user approval required to send.",
                requires_user_action=True,
                action_instructions="Review your cover letter and resume, then confirm to dispatch email."
            )

        if not is_smtp_configured():
            return SubmissionResult(
                status="failed",
                is_submitted=False,
                message="Cannot send application email: SMTP credentials are not configured in .env."
            )

        subject = f"Application for {package.job_title} - {package.candidate_name}"
        body = f"{package.cover_letter}\n\n---\nResume:\n{package.tailored_resume_text}"
        attachments = [package.resume_attachment_path] if package.resume_attachment_path else None

        success, msg = send_email(
            to_email=recipient,
            subject=subject,
            body=body,
            attachment_paths=attachments
        )

        if success:
            return SubmissionResult(
                status="submitted",
                is_submitted=True,
                receipt_id=f"email_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                message=f"Application emailed successfully to {recipient}.",
                details={"sent_at": datetime.utcnow().isoformat(), "recipient": recipient}
            )
        else:
            return SubmissionResult(
                status="failed",
                is_submitted=False,
                message=f"Email delivery failed: {msg}"
            )
