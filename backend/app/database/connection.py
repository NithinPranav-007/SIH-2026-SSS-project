"""
Database Connection and Session Management.

Supports:
- PostgreSQL + PostGIS via psycopg/SQLAlchemy
- Resilient fallback to SQLite if PostgreSQL is offline or unconfigured
"""

import os
import logging

logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# DATABASE_URL must be set via environment variable.
# No credentials are hardcoded. Omit or leave blank to use SQLite fallback.
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Test primary connection and fallback gracefully if needed
engine = None
if DATABASE_URL and "postgresql" in DATABASE_URL:
    try:
        test_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=False,
            connect_args={"connect_timeout": 2}
        )
        with test_engine.connect() as _conn:
            pass
        engine = test_engine
        logger.info("Connected to PostGIS PostgreSQL database at %s", DATABASE_URL.split("@")[-1])
    except Exception as exc:
        logger.warning(
            "Primary PostGIS connection unavailable (%s). Activating SQLite local fallback mode.", exc
        )
        engine = None

if engine is None:
    # Use SQLite fallback database (safe for development / demo)
    fallback_path = os.path.join(os.path.dirname(__file__), "..", "..", "sonar_intel_fallback.db")
    fallback_path = os.path.abspath(fallback_path)
    engine = create_engine(
        f"sqlite:///{fallback_path}",
        connect_args={"check_same_thread": False}
    )
    logger.info("Initialized local fallback SQLite at %s", fallback_path)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all ORM-managed tables in the database. Called once at application startup."""
    try:
        from backend.app.database import models  # noqa: F401 — import triggers model registration
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema synchronized successfully.")
    except Exception as exc:
        logger.warning("Warning during schema creation: %s", exc)


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

