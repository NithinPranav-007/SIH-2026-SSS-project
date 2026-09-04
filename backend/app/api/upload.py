"""
Survey Ingestion / Upload API Endpoint.

POST /api/surveys/upload
"""

import os
import time
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.repository import SurveyRepository
from backend.app.services.sonar_service import SonarService
from backend.app.schemas.survey import SurveyUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/surveys", tags=["Surveys"])
sonar_service = SonarService()

# Configurable max upload size — defaults to 100 MB
_MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "100")) * 1024 * 1024

# Allowed MIME type prefixes for sonar imagery
_ALLOWED_MIME_PREFIXES = ("image/png", "image/jpeg", "image/tiff", "image/gif", "image/bmp")


@router.post("/upload", response_model=SurveyUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_survey(
    sonar_file: UploadFile = File(..., description="Raw side-scan sonar waterfall image"),
    nav_file: Optional[UploadFile] = File(None, description="Optional navigation track CSV"),
    survey_id_override: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingests, validates, and stores a side-scan sonar swath and optional navigation log.
    The raw image is preserved unconditionally.
    """
    if not sonar_file.filename:
        raise HTTPException(status_code=400, detail="Missing sonar image file.")

    # Validate MIME type early to reject non-image uploads
    content_type = (sonar_file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{content_type}'. Only image files (PNG, JPEG, TIFF) are accepted."
        )

    # Generate or use survey ID
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    survey_id = survey_id_override or f"SURV_{timestamp_str}"

    # Read image contents (enforcing size limit)
    file_bytes = await sonar_file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded sonar file is empty.")

    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        limit_mb = _MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds the maximum allowed size of {limit_mb} MB."
        )

    logger.info(
        "Ingesting survey '%s': file='%s' size=%d bytes",
        survey_id, sonar_file.filename, len(file_bytes)
    )

    try:
        raw_path, width, height, quality = sonar_service.store_raw_upload(
            file_bytes=file_bytes,
            survey_id=survey_id,
            original_filename=sonar_file.filename
        )
    except Exception as exc:
        logger.exception("Image validation failed for survey '%s'", survey_id)
        raise HTTPException(status_code=422, detail=f"Image validation failed: {str(exc)}")

    # Handle optional navigation CSV
    nav_path = None
    if nav_file and nav_file.filename:
        nav_bytes = await nav_file.read()
        if len(nav_bytes) > 0:
            nav_dir = "data/raw"
            os.makedirs(nav_dir, exist_ok=True)
            nav_path = os.path.join(nav_dir, f"{survey_id}_nav.csv")
            with open(nav_path, "wb") as f:
                f.write(nav_bytes)

    # Save to database
    repo = SurveyRepository(db)
    processed_path = sonar_service.get_processed_path(survey_id)
    repo.save_survey(
        survey_id=survey_id,
        filename=sonar_file.filename,
        raw_image_path=raw_path,
        image_width=width,
        image_height=height,
        data_quality=quality["quality_score"],
        nav_file_path=nav_path,
        processed_image_path=processed_path if os.path.exists(processed_path) else None
    )

    logger.info(
        "Survey '%s' ingested successfully (%dx%d px, quality=%.2f)",
        survey_id, width, height, quality["quality_score"]
    )

    return SurveyUploadResponse(
        survey_id=survey_id,
        filename=sonar_file.filename,
        image_width=width,
        image_height=height,
        data_quality=quality["quality_score"],
        has_navigation=bool(nav_path),
        raw_image_url=f"/api/surveys/{survey_id}/image/raw",
        processed_image_url=f"/api/surveys/{survey_id}/image/processed",
        message="Survey uploaded and validated successfully."
    )
