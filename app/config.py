from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database Configuration (Postgres or SQLite fallback)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobhunt"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jobhunt"
    
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM Settings
    LLM_PROVIDER: str = "anthropic"  # "anthropic", "openai", "none"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "claude-3-haiku-20240307"
    
    # Chroma Vector Store
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # Email / SMTP
    SMTP_HOST: str = "smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_SECURE: bool = False
    FROM_EMAIL: str = "agent@jobhunt.ai"
    EMAIL_ENABLED: bool = False
    
    # Scraping & Automation
    ENABLE_PLAYWRIGHT: bool = False
    SCRAPER_TIMEOUT_SECONDS: int = 15
    
    # Candidate Defaults
    CANDIDATE_NAME: Optional[str] = None
    CANDIDATE_EMAIL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
