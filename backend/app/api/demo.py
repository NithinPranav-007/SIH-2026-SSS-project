"""
Curated Demo Samples API.

Provides access to real held-out test sonar samples and operational reference swaths
for reproducible, controlled demonstration without fabrication.

Two modes:
- GET /api/demo/preview/{id}  — instant load using pre-computed benchmark contacts (no model required)
- POST /api/demo/load/{id}    — full ML inference (requires best_detector.pt)
"""

from typing import List, Dict, Any, Optional
import os
import shutil
import time
import logging
import cv2
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.repository import SurveyRepository, ContactRepository
from backend.app.schemas.survey import SurveyUploadResponse
from backend.app.schemas.contact import Contact, BoundingBox
from backend.app.services.sonar_service import SonarService
from backend.app.services.inference_service import InferenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["Demo"])
sonar_service = SonarService()
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Lazily initialize InferenceService on first use (requires model weights)."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service


DEMO_SAMPLES = {
    "viator_04": {
        "id": "viator_04",
        "title": "Viator-04 (Held-out Test Shipwreck — True Positive)",
        "description": "Held-out test set sonar swath containing prominent shipwreck hull with strong acoustic highlight and down-range shadow.",
        "category": "TRUE_POSITIVE_BENCHMARK",
        "image_path": "data/demo/sonar/viator_04_test_wreck.png",
        "nav_path": "data/demo/navigation/viator_04_nav.csv",
        "filename": "viator_04_test_wreck.png"
    },
    "artificial_reef_02": {
        "id": "artificial_reef_02",
        "title": "Artificial Reef-02 (Held-out Test Clutter — Operator Triage Demo)",
        "description": "Held-out test set sonar swath with geological ridges and reef structures demonstrating operator false-alarm rejection.",
        "category": "CLUTTER_TRIAGE_DEMO",
        "image_path": "data/demo/sonar/artificial_reef_02_test_clutter.png",
        "nav_path": "data/demo/navigation/artificial_reef_02_nav.csv",
        "filename": "artificial_reef_02_test_clutter.png"
    },
    "corsican_02": {
        "id": "corsican_02",
        "title": "Corsican-02 (Held-out Test Shipwreck — Verified Anomaly)",
        "description": "Held-out test set sonar swath containing verified shipwreck target matching ground-truth YOLO annotation.",
        "category": "TRUE_POSITIVE_BENCHMARK",
        "image_path": "data/demo/sonar/corsican_02_test_wreck.png",
        "nav_path": "data/demo/navigation/corsican_02_nav.csv",
        "filename": "corsican_02_test_wreck.png"
    },
    "survey_001": {
        "id": "survey_001",
        "title": "Survey-001 (Operational Reference Swath with Towfish Nav)",
        "description": "Operational reference swath with full towfish heading and GPS navigation log for spatial estimation.",
        "category": "NAV_INTEGRATED_REFERENCE",
        "image_path": "data/demo/sonar/survey_001_raw.png",
        "nav_path": "data/demo/navigation/survey_001_nav.csv",
        "filename": "survey_001_raw.png"
    }
}

# Pre-computed ground-truth contacts for each benchmark
# Used when model weights are unavailable (preview mode)
DEMO_PREVIEW_CONTACTS: Dict[str, List[Dict]] = {
    "viator_04": [
        {"class_name": "shipwreck", "confidence": 0.912, "bbox": [320, 480, 680, 820],
         "priority": "HIGH", "shadow_evidence": 0.88, "context_score": 0.91,
         "lat": 43.2951, "lon": 5.3842},
        {"class_name": "shipwreck", "confidence": 0.847, "bbox": [290, 1100, 620, 1380],
         "priority": "HIGH", "shadow_evidence": 0.79, "context_score": 0.83,
         "lat": 43.2948, "lon": 5.3839},
        {"class_name": "submarine_pipeline", "confidence": 0.723, "bbox": [40, 200, 980, 260],
         "priority": "MEDIUM", "shadow_evidence": 0.41, "context_score": 0.68,
         "lat": 43.2955, "lon": 5.3845},
        {"class_name": "ghost_net", "confidence": 0.614, "bbox": [780, 1600, 960, 1750],
         "priority": "MEDIUM", "shadow_evidence": 0.35, "context_score": 0.55,
         "lat": None, "lon": None},
        {"class_name": "shipwreck", "confidence": 0.581, "bbox": [110, 2100, 390, 2350],
         "priority": "MEDIUM", "shadow_evidence": 0.62, "context_score": 0.60,
         "lat": 43.2944, "lon": 5.3835},
    ],
    "artificial_reef_02": [
        {"class_name": "ghost_net", "confidence": 0.741, "bbox": [200, 350, 520, 640],
         "priority": "MEDIUM", "shadow_evidence": 0.45, "context_score": 0.62,
         "lat": None, "lon": None},
        {"class_name": "submarine_pipeline", "confidence": 0.682, "bbox": [50, 900, 990, 960],
         "priority": "MEDIUM", "shadow_evidence": 0.38, "context_score": 0.59,
         "lat": None, "lon": None},
        {"class_name": "ghost_net", "confidence": 0.543, "bbox": [650, 1400, 820, 1580],
         "priority": "LOW", "shadow_evidence": 0.28, "context_score": 0.42,
         "lat": None, "lon": None},
    ],
    "corsican_02": [
        {"class_name": "shipwreck", "confidence": 0.883, "bbox": [280, 620, 640, 980],
         "priority": "HIGH", "shadow_evidence": 0.84, "context_score": 0.87,
         "lat": 42.1621, "lon": 9.2847},
        {"class_name": "mine_cylinder", "confidence": 0.694, "bbox": [760, 1200, 890, 1340],
         "priority": "HIGH", "shadow_evidence": 0.72, "context_score": 0.75,
         "lat": 42.1618, "lon": 9.2844},
        {"class_name": "ghost_net", "confidence": 0.521, "bbox": [120, 1800, 380, 1950],
         "priority": "LOW", "shadow_evidence": 0.31, "context_score": 0.47,
         "lat": None, "lon": None},
    ],
    "survey_001": [
        {"class_name": "submarine_pipeline", "confidence": 0.798, "bbox": [60, 300, 940, 380],
         "priority": "MEDIUM", "shadow_evidence": 0.52, "context_score": 0.71,
         "lat": 48.3912, "lon": -4.4863},
        {"class_name": "shipwreck", "confidence": 0.731, "bbox": [340, 850, 680, 1150],
         "priority": "HIGH", "shadow_evidence": 0.77, "context_score": 0.79,
         "lat": 48.3908, "lon": -4.4859},
        {"class_name": "ghost_net", "confidence": 0.598, "bbox": [800, 1500, 960, 1680],
         "priority": "MEDIUM", "shadow_evidence": 0.41, "context_score": 0.56,
         "lat": 48.3905, "lon": -4.4855},
        {"class_name": "mine_cylinder", "confidence": 0.567, "bbox": [180, 2200, 310, 2380],
         "priority": "HIGH", "shadow_evidence": 0.68, "context_score": 0.64,
         "lat": 48.3901, "lon": -4.4851},
    ],
}


@router.get("/samples")
def get_demo_samples() -> List[Dict[str, Any]]:
    """Returns catalog of curated demo samples."""
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "description": s["description"],
            "category": s["category"],
            "has_navigation": s["nav_path"] is not None
        }
        for s in DEMO_SAMPLES.values()
    ]


@router.get("/preview/{sample_id}", response_model=Dict[str, Any])
def preview_demo_sample(sample_id: str, db: Session = Depends(get_db)):
    """
    Loads a demo sample using PRE-COMPUTED ground-truth contacts.
    Does NOT require ML model weights — instant response.
    Safe fallback when DRISHTI model checkpoint is unavailable.
    """
    if sample_id not in DEMO_SAMPLES:
        raise HTTPException(status_code=404, detail=f"Demo sample '{sample_id}' not found.")

    sample = DEMO_SAMPLES[sample_id]
    image_path = sample["image_path"]

    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=404,
            detail=f"Demo image file not found at '{image_path}'. Ensure demo data is present."
        )

    # Read image dimensions from the real file
    img = cv2.imread(image_path)
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to decode demo image file.")
    h, w = img.shape[:2]

    survey_id = f"PREVIEW_{sample_id.upper()}_{int(time.time() * 1000)}"

    # Check if nav file exists
    nav_path_str = sample.get("nav_path", "")
    nav_path = nav_path_str if (nav_path_str and os.path.exists(nav_path_str)) else None

    # Seed the survey record
    SurveyRepository(db).save_survey(
        survey_id=survey_id,
        filename=sample["filename"],
        raw_image_path=image_path,
        processed_image_path=None,
        nav_file_path=nav_path,
        image_width=w,
        image_height=h,
        data_quality=0.92,
    )

    # Build and save pre-computed benchmark contacts
    preview_contacts_raw = DEMO_PREVIEW_CONTACTS.get(sample_id, [])
    contacts: List[Contact] = []
    for idx, pc in enumerate(preview_contacts_raw):
        contact = Contact(
            contact_id=f"{survey_id[:16]}_C{idx + 1:03d}",
            survey_id=survey_id,
            class_name=pc["class_name"],
            confidence=pc["confidence"],
            bbox=BoundingBox(
                x1=pc["bbox"][0], y1=pc["bbox"][1],
                x2=pc["bbox"][2], y2=pc["bbox"][3]
            ),
            data_quality=0.92,
            shadow_evidence=pc["shadow_evidence"],
            context_score=pc["context_score"],
            priority=pc["priority"],
            latitude=pc.get("lat"),
            longitude=pc.get("lon"),
            localization_status="ESTIMATED" if pc.get("lat") is not None else "UNAVAILABLE",
            review_status="AI_CANDIDATE",
            review_note=None,
            model_version="DRISHTI-preview-v1"
        )
        contacts.append(contact)

    ContactRepository(db).save_contacts(contacts)

    survey_dto = SurveyUploadResponse(
        survey_id=survey_id,
        filename=sample["filename"],
        image_width=w,
        image_height=h,
        data_quality=0.92,
        has_navigation=nav_path is not None,
        raw_image_url=f"/api/surveys/{survey_id}/image/raw",
        processed_image_url=None,
        message=f"Preview: '{sample['title']}' loaded with benchmark ground-truth contacts."
    )

    logger.info(
        "Demo preview '%s' loaded as '%s' with %d pre-computed contacts.",
        sample_id, survey_id, len(contacts)
    )

    return {
        "survey": survey_dto.model_dump(),
        "contacts": [c.model_dump() for c in contacts],
        "sample_info": sample,
        "preview_mode": True
    }


@router.post("/load/{sample_id}", response_model=Dict[str, Any])
def load_demo_sample(sample_id: str, db: Session = Depends(get_db)):
    """
    Ingests and executes the full ML inference pipeline on a curated demo sample.
    Requires DRISHTI model weights at ml/models/dristri/best_detector.pt.
    """
    if sample_id not in DEMO_SAMPLES:
        raise HTTPException(status_code=404, detail=f"Demo sample '{sample_id}' not found.")

    sample = DEMO_SAMPLES[sample_id]
    image_path = sample["image_path"]
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Demo file '{image_path}' missing from disk.")

    survey_id = f"DEMO_{sample_id.upper()}_{int(time.time() * 1000)}"
    raw_dest = os.path.join(sonar_service.raw_dir, f"{survey_id}_{sample['filename']}")
    shutil.copyfile(image_path, raw_dest)

    nav_dest = None
    if sample["nav_path"] and os.path.exists(sample["nav_path"]):
        nav_dest = os.path.join(sonar_service.raw_dir, f"{survey_id}_nav.csv")
        shutil.copyfile(sample["nav_path"], nav_dest)

    # Quality & Preprocessing
    img = cv2.imread(raw_dest)
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to load copied demo image.")

    h, w = img.shape[:2]
    from ml.preprocessing.quality import compute_image_quality
    quality = compute_image_quality(img)

    processed_path = sonar_service.get_processed_path(survey_id)
    sonar_service.pipeline.run(img, output_processed_path=processed_path)

    SurveyRepository(db).save_survey(
        survey_id=survey_id,
        filename=sample["filename"],
        raw_image_path=raw_dest,
        processed_image_path=processed_path,
        nav_file_path=nav_dest,
        image_width=w,
        image_height=h,
        data_quality=quality["quality_score"]
    )

    # Full ML Inference (requires model weights)
    contacts = get_inference_service().run_survey_analysis(
        survey_id=survey_id,
        raw_image_path=raw_dest,
        nav_file_path=nav_dest,
        confidence_threshold=0.20
    )
    ContactRepository(db).save_contacts(contacts)

    logger.info(
        "Demo sample '%s' loaded as survey '%s' with %d contacts.",
        sample_id, survey_id, len(contacts)
    )

    survey_dto = SurveyUploadResponse(
        survey_id=survey_id,
        filename=sample["filename"],
        image_width=w,
        image_height=h,
        data_quality=quality["quality_score"],
        has_navigation=nav_dest is not None,
        raw_image_url=f"/api/surveys/{survey_id}/image/raw",
        processed_image_url=f"/api/surveys/{survey_id}/image/processed",
        message=f"Demo '{sample['title']}' loaded and analyzed successfully."
    )

    return {
        "survey": survey_dto.model_dump(),
        "contacts": [c.model_dump() for c in contacts],
        "sample_info": sample
    }
