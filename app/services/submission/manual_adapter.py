import uuid
from datetime import datetime, timezone
from app.services.submission.base import BaseSubmissionAdapter, SubmissionPackage, SubmissionResult

class ManualSubmissionAdapter(BaseSubmissionAdapter):
    """
    Standard submission adapter for standard job postings.
    Compiles tailored application package and provides direct link + instructions.
    Only marks status as 'submitted' upon explicit user confirmation.
    """

    def can_handle(self, submission_type: str) -> bool:
        return submission_type in ["manual", "direct_url", "external_portal"]

    async def submit(self, package: SubmissionPackage, user_confirmed: bool) -> SubmissionResult:
        if not user_confirmed:
            instructions = (
                f"1. Open the application portal: {package.job_url}\n"
                f"2. Copy the tailored resume and cover letter provided in your application review package.\n"
                f"3. Submit the application through the employer's portal.\n"
                f"4. Click 'Confirm Submission' to track your application as submitted."
            )
            return SubmissionResult(
                status="requires_manual_action",
                is_submitted=False,
                message="Application package prepared. Manual submission on company portal required.",
                requires_user_action=True,
                action_instructions=instructions,
                details={
                    "portal_url": package.job_url,
                    "prepared_at": datetime.now(timezone.utc).isoformat()
                }
            )

        # User explicitly confirmed completion of external submission
        receipt = f"manual_{uuid.uuid4().hex[:8]}"
        return SubmissionResult(
            status="submitted",
            is_submitted=True,
            receipt_id=receipt,
            message=f"Application for '{package.job_title}' at {package.company} confirmed as submitted by candidate.",
            requires_user_action=False,
            details={
                "confirmed_by_candidate": True,
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                "portal_url": package.job_url
            }
        )
