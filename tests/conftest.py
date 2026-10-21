import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

import app.database as app_db
from app.database import Base, get_async_db
from app.main import app

TEST_DB_FILE = "./test_jobhunt.db"
TEST_ASYNC_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
TEST_SYNC_URL = f"sqlite:///{TEST_DB_FILE}"

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Sync engine for table creation & sync runner helpers
    sync_test_engine = create_engine(TEST_SYNC_URL, connect_args={"check_same_thread": False})
    async_test_engine = create_async_engine(TEST_ASYNC_URL, connect_args={"check_same_thread": False})
    
    Base.metadata.create_all(bind=sync_test_engine)
    
    # Patch app_db engines and sessionmakers globally for testing
    app_db.sync_engine = sync_test_engine
    app_db.SyncSessionLocal = sessionmaker(bind=sync_test_engine, autocommit=False, autoflush=False)
    app_db.async_engine = async_test_engine
    app_db.AsyncSessionLocal = async_sessionmaker(
        bind=async_test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    yield
    
    sync_test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def client():
    # Override get_async_db dependency with test database
    async def override_get_async_db():
        async with app_db.AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_async_db] = override_get_async_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
