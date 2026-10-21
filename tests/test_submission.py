import pytest
from app.services.submission.base import SubmissionPackage
from app.services.submission.manual_adapter import ManualSubmissionAdapter
from app.services.submission.email_adapter import EmailSubmissionAdapter
from app.services.email_service import validate_email_address

def test_validate_email_address():
    assert validate_email_address("alex.rivera@company.com") is True
    assert validate_email_address("candidate@example.com") is False  # Rejects mock
    assert validate_email_address("invalid-email") is False
    assert validate_email_address("") is False

@pytest.mark.asyncio
async def test_manual_submission_requires_user_action():
    adapter = ManualSubmissionAdapter()
    package = SubmissionPackage(
        application_id=10,
        job_title="Backend Engineer",
        company="Stripe",
        job_url="https://stripe.com/jobs/123",
        candidate_name="Alex Rivera",
        tailored_resume_text="Tailored content..."
    )

    # Without user confirmation -> requires_manual_action, NOT submitted
    result_unconfirmed = await adapter.submit(package, user_confirmed=False)
    assert result_unconfirmed.is_submitted is False
    assert result_unconfirmed.status == "requires_manual_action"
    assert result_unconfirmed.requires_user_action is True
    assert "portal" in result_unconfirmed.action_instructions.lower()

    # With user confirmation -> submitted
    result_confirmed = await adapter.submit(package, user_confirmed=True)
    assert result_confirmed.is_submitted is True
    assert result_confirmed.status == "submitted"
    assert result_confirmed.receipt_id is not None

@pytest.mark.asyncio
async def test_email_submission_fails_honestly_when_unconfigured():
    adapter = EmailSubmissionAdapter()
    package = SubmissionPackage(
        application_id=11,
        job_title="Python Lead",
        company="TechCorp",
        job_url="https://techcorp.com/job/456",
        candidate_name="Alex Rivera",
        candidate_email="hiring@techcorp.com",
        tailored_resume_text="Resume...",
        cover_letter="Cover letter..."
    )
    # When unconfirmed -> review status
    res1 = await adapter.submit(package, user_confirmed=False)
    assert res1.is_submitted is False
    assert res1.status == "ready_for_review"

    # When confirmed without SMTP credentials -> fails honestly, does not report fake success
    res2 = await adapter.submit(package, user_confirmed=True)
    assert res2.is_submitted is False
    assert res2.status == "failed"
    assert "SMTP" in res2.message
