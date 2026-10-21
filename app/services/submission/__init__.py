from app.services.submission.base import (
    BaseSubmissionAdapter,
    SubmissionPackage,
    SubmissionResult
)
from app.services.submission.manual_adapter import ManualSubmissionAdapter
from app.services.submission.email_adapter import EmailSubmissionAdapter

ADAPTERS = [
    EmailSubmissionAdapter(),
    ManualSubmissionAdapter()
]

def get_submission_adapter(submission_type: str) -> BaseSubmissionAdapter:
    for adapter in ADAPTERS:
        if adapter.can_handle(submission_type):
            return adapter
    return ManualSubmissionAdapter()

__all__ = [
    "BaseSubmissionAdapter",
    "SubmissionPackage",
    "SubmissionResult",
    "ManualSubmissionAdapter",
    "EmailSubmissionAdapter",
    "get_submission_adapter"
]
