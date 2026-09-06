"""
Resurvey Recommendations API Router.

GET /api/resurvey/recommendations
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.services.resurvey_service import ResurveyService

router = APIRouter(prefix="/api/resurvey", tags=["Survey Intelligence"])


@router.get("/recommendations")
def get_resurvey_recommendations(
    survey_id: Optional[str] = Query(None, description="Optional filter by survey ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generates actionable hydrographic resurvey recommendations based on swath signal quality,
    positioning uncertainty, and contact ambiguity.
    """
    service = ResurveyService(db)
    recs = service.generate_recommendations(survey_id=survey_id)
    return {
        "status": "success",
        "total_recommendations": len(recs),
        "recommendations": recs
    }
