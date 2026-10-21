import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

Base = declarative_base()

def get_engine_args(url: str):
    if "sqlite" in url:
        return {"connect_args": {"check_same_thread": False}}
    return {}

def create_resilient_sync_engine():
    if "sqlite" in settings.SYNC_DATABASE_URL:
        return create_engine(settings.SYNC_DATABASE_URL, **get_engine_args(settings.SYNC_DATABASE_URL))
    try:
        eng = create_engine(settings.SYNC_DATABASE_URL, **get_engine_args(settings.SYNC_DATABASE_URL))
        with eng.connect() as conn:
            pass
        return eng
    except Exception as e:
        sqlite_fallback = "sqlite:///./jobhunt.db"
        print(f"[Database Notice] PostgreSQL is unreachable or authentication failed ({e}). Falling back to local SQLite ({sqlite_fallback}) for development.")
        return create_engine(sqlite_fallback, connect_args={"check_same_thread": False})

def create_resilient_async_engine():
    if "sqlite" in settings.DATABASE_URL:
        return create_async_engine(settings.DATABASE_URL, **get_engine_args(settings.DATABASE_URL))
    try:
        test_eng = create_engine(settings.SYNC_DATABASE_URL, **get_engine_args(settings.SYNC_DATABASE_URL))
        with test_eng.connect() as conn:
            pass
        return create_async_engine(settings.DATABASE_URL, **get_engine_args(settings.DATABASE_URL))
    except Exception:
        sqlite_async_fallback = "sqlite+aiosqlite:///./jobhunt.db"
        return create_async_engine(sqlite_async_fallback, connect_args={"check_same_thread": False})

# Async engine & session for FastAPI routes
async_engine = create_resilient_async_engine()
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

# Sync engine & session for Celery / synchronous background runners
sync_engine = create_resilient_sync_engine()
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# Async dependency for FastAPI
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Sync helper
def get_sync_db():
    return SyncSessionLocal()
