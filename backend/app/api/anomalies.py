"""
Acoustic Anomalies API Router.

GET /api/anomalies/unknown
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.repository import ContactRepository
from backend.app.schemas.contact import Contact

router = APIRouter(prefix="/api/anomalies", tags=["Acoustic Anomalies"])


@router.get("/unknown", response_model=List[Contact])
def get_unknown_acoustic_anomalies(
    min_novelty: float = Query(40.0, ge=0.0, le=100.0, description="Minimum novelty score cutoff"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Retrieves uncatalogued acoustic contacts identified as UNKNOWN_ANOMALY.
    Surfaces high-novelty acoustic signatures for hydrographic triage.
    """
    repo = ContactRepository(db)
    return repo.get_unknown_anomalies(min_novelty=min_novelty, limit=limit)
