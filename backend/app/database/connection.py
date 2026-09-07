"""
Database Connection and Session Management.

Supports:
- PostgreSQL + PostGIS via psycopg/SQLAlchemy
- Resilient fallback to SQLite if PostgreSQL is offline or unconfigured
"""

import logging

logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

Base = declarative_base()

# DATABASE_URL is configured centrally through settings (supports PostgreSQL/PostGIS and SQLite)
DATABASE_URL = settings.database.URL

# Test primary connection and fallback gracefully if needed
engine = None
if DATABASE_URL:
    if "postgresql" in DATABASE_URL:
        try:
            test_engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=settings.database.POOL_PRE_PING,
                connect_args={"connect_timeout": settings.database.CONNECT_TIMEOUT}
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
    elif "sqlite" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        logger.info("Connected to SQLite database at %s", DATABASE_URL)

if engine is None:
    # Use centralized SQLite fallback database (safe for development / demo)
    fallback_path = settings.database.fallback_path
    engine = create_engine(
        f"sqlite:///{fallback_path}",
        connect_args={"check_same_thread": False}
    )
    logger.info("Initialized local fallback SQLite at %s", fallback_path)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all ORM-managed tables in the database and adds any missing columns."""
    try:
        from backend.app.database import models  # noqa: F401 — import triggers model registration
        Base.metadata.create_all(bind=engine)

        # Safe additive migrations for SQLite/PostgreSQL
        from sqlalchemy import text, inspect
        inspector = inspect(engine)

        # Check contacts table
        if "contacts" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("contacts")}
            new_contact_cols = {
                "pipeline_version": "TEXT",
                "classifier_confidence": "FLOAT",
                "classifier_label": "TEXT",
                "classifier_method": "TEXT",
                "acoustic_probability": "FLOAT",
                "evidence_score": "FLOAT",
                "calibrated_confidence": "FLOAT",
                "track_id": "TEXT",
                "track_observations": "INTEGER",
                "track_confidence": "FLOAT",
                "track_stability": "FLOAT",
                "novelty_score": "FLOAT",
                "anomaly_type": "TEXT",
                "risk_score": "FLOAT",
                "risk_level": "TEXT",
                "measurements": "TEXT",
                "explanation": "TEXT",
                "has_embedding": "BOOLEAN DEFAULT 0"
            }
            with engine.connect() as conn:
                for col_name, col_type in new_contact_cols.items():
                    if col_name not in existing_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE contacts ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception as e:
                            logger.debug("Column %s might already exist or failed: %s", col_name, e)

        # Check surveys table
        if "surveys" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("surveys")}
            if "quality_report" not in existing_cols:
                with engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE surveys ADD COLUMN quality_report TEXT"))
                        conn.commit()
                    except Exception:
                        pass

        # Check reviews table
        if "reviews" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("reviews")}
            if "pipeline_version" not in existing_cols:
                with engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE reviews ADD COLUMN pipeline_version TEXT"))
                        conn.commit()
                    except Exception:
                        pass

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

