"""
Root conftest.py for SONAR-INTEL test suite.

Sets up:
- SQLite in-memory test database (overrides DATABASE_URL before any app import)
- Shared FastAPI TestClient fixture
- Test data fixtures for surveys and contacts
"""

import os
import pytest

# Override DATABASE_URL BEFORE any backend module is imported so SQLAlchemy
# uses SQLite in-memory instead of attempting a PostgreSQL connection.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_sonar_intel.db")


@pytest.fixture(scope="session", autouse=True)
def test_db_setup():
    """
    Creates the test database schema once per session and tears it down after.
    """
    from backend.app.database.connection import Base, engine
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up the test db file if it was created on disk
    if os.path.exists("test_sonar_intel.db"):
        try:
            os.remove("test_sonar_intel.db")
        except OSError:
            pass


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for each test function."""
    from backend.app.database.connection import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def test_client():
    """FastAPI TestClient using the overridden test database."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    with TestClient(app) as client:
        yield client
