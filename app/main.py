from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import async_engine, Base
from app.api import resume_router, apply_router, applications_router, jobs_router
from app.vector_store.chroma_client import chroma_client
from app.services.llm_client import llm_client
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Database table initialization warning: {e}")
    yield
    await async_engine.dispose()

app = FastAPI(
    title="Job-hunt AI Platform API",
    description="Agentic Job Discovery, Resume Tailoring, ATS Evaluation, and Application Tracking",
    version="2.0.0",
    lifespan=lifespan,
)

# Development CORS configuration allowing local frontend origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(resume_router, prefix="/api/v1", tags=["Resumes"])
app.include_router(jobs_router, prefix="/api/v1", tags=["Jobs"])
app.include_router(apply_router, prefix="/api/v1", tags=["Apply"])
app.include_router(applications_router, prefix="/api/v1", tags=["Applications"])

@app.get("/health")
async def health_check():
    """System health check verifying database, vector store, and LLM configuration."""
    db_status = "ok"
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    chroma_status = "ok"
    try:
        count = chroma_client.resume_collection.count()
        chroma_status = f"ok ({count} vectors indexed)"
    except Exception as e:
        chroma_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "job-hunt-api",
        "version": "2.0.0",
        "database": db_status,
        "vector_store": chroma_status,
        "llm_provider": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "is_configured": llm_client.is_configured()
        },
        "email_service": {
            "enabled": settings.EMAIL_ENABLED,
            "smtp_host": settings.SMTP_HOST
        }
    }
