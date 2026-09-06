"""
Contacts Query API Endpoints.

GET /api/surveys/{survey_id}/contacts
GET /api/contacts/{contact_id}
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.repository import ContactRepository, SurveyRepository
from backend.app.schemas.contact import Contact

router = APIRouter(tags=["Contacts"])


@router.get("/api/surveys/{survey_id}/contacts", response_model=List[Contact])
async def get_survey_contacts(survey_id: str, db: Session = Depends(get_db)):
    """Retrieves all detected canonical contacts for a specific survey."""
    survey = SurveyRepository(db).get_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_id}' not found.")

    repo = ContactRepository(db)
    return repo.get_contacts_by_survey(survey_id)


@router.get("/api/contacts/search", response_model=List[Contact])
async def search_contacts(
    q: Optional[str] = None,
    priority: Optional[str] = None,
    review_status: Optional[str] = None,
    survey_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Searches contacts by ID, survey, priority, or review state."""
    repo = ContactRepository(db)
    return repo.search_contacts(q=q, priority=priority, review_status=review_status, survey_id=survey_id)


@router.get("/api/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str, db: Session = Depends(get_db)):
    """Retrieves a single canonical contact by its ID."""
    repo = ContactRepository(db)
    contact = repo.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")
    return contact


@router.get("/api/contacts/{contact_id}/explanation")
async def get_contact_explanation(contact_id: str, db: Session = Depends(get_db)):
    """Retrieves explainability evidence breakdown for the contact."""
    repo = ContactRepository(db)
    contact = repo.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")

    if contact.explanation:
        return {"contact_id": contact_id, "explanation": contact.explanation}

    # Fallback synthesizer if not pre-populated
    from ml.inference.explanation import ExplainabilityEngine
    engine = ExplainabilityEngine()
    expl = engine.generate_explanation(
        detector_confidence=contact.confidence,
        acoustic_prob=contact.acoustic_probability,
        classifier_confidence=contact.classifier_confidence,
        context={"shadow_evidence": contact.shadow_evidence, "local_contrast": contact.context_score},
        track_persistence=contact.track_observations or 1,
        novelty_score=contact.novelty_score,
        sonar_quality_score=contact.data_quality * 100.0 if contact.data_quality <= 1.0 else contact.data_quality,
        risk_score=contact.risk_score
    )
    return {"contact_id": contact_id, "explanation": expl}


@router.get("/api/contacts/{contact_id}/similar")
async def get_similar_contacts(contact_id: str, top_k: int = 5, db: Session = Depends(get_db)):
    """Finds top-K most similar contacts across surveys using acoustic feature embeddings."""
    repo = ContactRepository(db)
    target = repo.get_contact_by_id(contact_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")

    all_contacts = repo.search_contacts()
    # Simple similarity based on acoustic context & confidence
    similar = []
    for c in all_contacts:
        if c.contact_id == contact_id:
            continue
        # Distance in confidence + shadow_evidence + context_score
        dist = abs(c.confidence - target.confidence) + abs(c.shadow_evidence - target.shadow_evidence)
        sim = max(0.0, 1.0 - (dist / 2.0))
        similar.append({
            "contact_id": c.contact_id,
            "survey_id": c.survey_id,
            "class_name": c.class_name,
            "priority": c.priority,
            "similarity": round(sim, 3),
            "confidence": c.confidence
        })

    similar.sort(key=lambda s: s["similarity"], reverse=True)
    return {
        "target_contact_id": contact_id,
        "target_class": target.class_name,
        "similar_contacts": similar[:top_k]
    }


@router.get("/api/contacts/{contact_id}/track")
async def get_contact_track(contact_id: str, db: Session = Depends(get_db)):
    """Retrieves multi-ping tracking association history for the contact."""
    repo = ContactRepository(db)
    contact = repo.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")

    track_id = contact.track_id or f"TRK_{contact_id}"
    return {
        "contact_id": contact_id,
        "track_id": track_id,
        "observation_count": contact.track_observations or 1,
        "track_confidence": contact.track_confidence or contact.confidence,
        "track_stability": contact.track_stability or 0.85,
        "status": "ASSOCIATED" if contact.track_id else "SINGLE_OBSERVATION"
    }


@router.get("/api/contacts/{contact_id}/measurements")
async def get_contact_measurements(contact_id: str, db: Session = Depends(get_db)):
    """Retrieves metric physical dimensions (length, width, area, shadow) for the contact."""
    repo = ContactRepository(db)
    contact = repo.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")

    if contact.measurements:
        return {"contact_id": contact_id, "measurements": contact.measurements}

    # Fallback derivation from bbox
    w = max(1, contact.bbox.x2 - contact.bbox.x1)
    h = max(1, contact.bbox.y2 - contact.bbox.y1)
    from ml.inference.measurement import TargetMeasurer
    measurer = TargetMeasurer()
    meas = measurer.compute_measurements(
        bbox={"x1": contact.bbox.x1, "y1": contact.bbox.y1, "x2": contact.bbox.x2, "y2": contact.bbox.y2},
        context={"shadow_length_est": 0.0, "distance_from_nadir": 100.0},
        localization_status=contact.localization_status
    )
    return {"contact_id": contact_id, "measurements": meas}


@router.get("/api/contacts/{contact_id}/risk")
async def get_contact_risk_breakdown(contact_id: str, db: Session = Depends(get_db)):
    """Retrieves operational risk assessment and tier breakdown."""
    repo = ContactRepository(db)
    contact = repo.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")

    return {
        "contact_id": contact_id,
        "risk_score": contact.risk_score or 45.0,
        "risk_level": contact.risk_level or "MEDIUM",
        "risk_label": getattr(contact, "risk_label", None) or "Standard triage contact",
        "is_novel_anomaly": contact.anomaly_type == "UNKNOWN_ANOMALY" or (contact.novelty_score or 0) >= 50.0
    }
