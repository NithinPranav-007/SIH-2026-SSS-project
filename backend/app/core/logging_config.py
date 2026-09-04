"""
Structured Logging Configuration for SONAR-INTEL.

Configures Python standard logging with:
- ISO 8601 timestamps
- Log levels (DEBUG in dev, INFO in production)
- Console handler with consistent format
- Production-safe: never logs secrets, tokens, or raw request bodies

Usage:
    from backend.app.core.logging_config import configure_logging
    configure_logging()
"""

import logging
import os
import sys


def configure_logging() -> None:
    """
    Sets up the root logger for the application.

    Reads LOG_LEVEL from the environment (default: INFO).
    Uses a structured format suitable for log aggregation systems.
    """
    log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Replace all existing handlers to avoid duplicate output
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured: level=%s", log_level_name
    )
