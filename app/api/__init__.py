from app.api.routes_resume import router as resume_router
from app.api.routes_apply import router as apply_router
from app.api.routes_applications import router as applications_router
from app.api.routes_jobs import router as jobs_router

__all__ = ["resume_router", "apply_router", "applications_router", "jobs_router"]
