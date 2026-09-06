"""
Active Learning API Router.

GET  /api/active-learning/samples
POST /api/active-learning/export
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.services.active_learning_service import ActiveLearningService
from ml.training.active_learning_export import export_active_learning_dataset

router = APIRouter(prefix="/api/active-learning", tags=["Active Learning"])


@router.get("/samples")
def get_curated_training_samples(
    priority: str = Query("MEDIUM", description="Minimum priority tier: HIGH | MEDIUM | ALL"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Surfaces high-value review samples (high uncertainty, operator corrections, rare anomalies)
    for curation into retraining datasets.
    """
    al_service = ActiveLearningService(db)
    samples = al_service.get_high_value_samples(min_priority=priority, limit=limit)
    return {
        "status": "success",
        "sample_count": len(samples),
        "samples": samples
    }


@router.post("/export")
def trigger_dataset_export(
    include_uncertain: bool = False,
    output_dir: str = "data/active_learning_export",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Exports confirmed contacts and curated samples into standard YOLO annotation format.
    Manual trigger only.
    """
    res = export_active_learning_dataset(db=db, output_dir=output_dir, include_uncertain=include_uncertain)
    return res
