"""
AI Sonar Analyst API Router.

POST /api/analyst/query

Structured Natural Language Query Engine:
Maps natural language operator queries into deterministic database filters.
Operates 100% offline without external LLM dependencies, guaranteeing
zero hallucination and verifiable evidence.
"""

from typing import Dict, Any, List, Optional
import re
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import ContactModel
from backend.app.database.repository import to_canonical_contact
from backend.app.schemas.contact import Contact

router = APIRouter(prefix="/api/analyst", tags=["AI Analyst"])


class AnalystQueryRequest(BaseModel):
    query: str
    limit: Optional[int] = 25


class AnalystQueryResponse(BaseModel):
    query: str
    parsed_intent: str
    filters_applied: Dict[str, Any]
    total_matches: int
    summary_text: str
    contacts: List[Contact]


@router.post("/query", response_model=AnalystQueryResponse)
def execute_analyst_query(
    req: AnalystQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Interprets natural language queries from hydrographers into database filters.
    """
    raw_query = req.query.lower().strip()
    filters: Dict[str, Any] = {}
    intent_parts = []

    # 1. Risk level parsing
    if "critical risk" in raw_query or "critical" in raw_query:
        filters["risk_level"] = "CRITICAL"
        intent_parts.append("Risk = CRITICAL")
    elif "high risk" in raw_query:
        filters["risk_level"] = "HIGH"
        intent_parts.append("Risk = HIGH")
    elif "low risk" in raw_query:
        filters["risk_level"] = "LOW"
        intent_parts.append("Risk = LOW")
    elif "medium risk" in raw_query:
        filters["risk_level"] = "MEDIUM"
        intent_parts.append("Risk = MEDIUM")

    # 2. Priority parsing
    if "high priority" in raw_query:
        filters["priority"] = "HIGH"
        intent_parts.append("Priority = HIGH")
    elif "medium priority" in raw_query:
        filters["priority"] = "MEDIUM"
        intent_parts.append("Priority = MEDIUM")
    elif "low priority" in raw_query:
        filters["priority"] = "LOW"
        intent_parts.append("Priority = LOW")

    # 3. Review status parsing
    if "confirmed" in raw_query:
        filters["review_status"] = "CONFIRMED"
        intent_parts.append("Status = CONFIRMED")
    elif "false positive" in raw_query or "fp" in raw_query:
        filters["review_status"] = "FALSE_POSITIVE"
        intent_parts.append("Status = FALSE_POSITIVE")
    elif "uncertain" in raw_query:
        filters["review_status"] = "UNCERTAIN"
        intent_parts.append("Status = UNCERTAIN")
    elif "candidate" in raw_query:
        filters["review_status"] = "AI_CANDIDATE"
        intent_parts.append("Status = AI_CANDIDATE")

    # 4. Target class parsing
    if "ghost net" in raw_query or "net" in raw_query:
        filters["class_name"] = "ghost_net"
        intent_parts.append("Class = Ghost Net")
    elif "shipwreck" in raw_query or "wreck" in raw_query:
        filters["class_name"] = "shipwreck"
        intent_parts.append("Class = Shipwreck")
    elif "container" in raw_query:
        filters["class_name"] = "shipping_container"
        intent_parts.append("Class = Shipping Container")
    elif "pipeline" in raw_query:
        filters["class_name"] = "pipeline"
        intent_parts.append("Class = Pipeline")
    elif "mine" in raw_query or "ordnance" in raw_query:
        filters["class_name"] = "mine_like"
        intent_parts.append("Class = Mine-like / Ordnance")

    # 5. Unknown anomaly parsing
    if "unknown" in raw_query or "anomaly" in raw_query or "novel" in raw_query:
        filters["is_anomaly"] = True
        intent_parts.append("Target = Unknown Acoustic Anomaly")

    # 6. Survey ID parsing (e.g. survey 1, demo_survey, etc.)
    survey_match = re.search(r"survey\s+([a-zA-Z0-9_\-]+)", raw_query)
    if survey_match:
        matched_id = survey_match.group(1)
        filters["survey_id"] = matched_id
        intent_parts.append(f"Survey ID contains '{matched_id}'")

    # Build DB query
    query = db.query(ContactModel)

    if "risk_level" in filters:
        query = query.filter(ContactModel.risk_level == filters["risk_level"])
    if "priority" in filters:
        query = query.filter(ContactModel.priority == filters["priority"])
    if "review_status" in filters:
        query = query.filter(ContactModel.review_status == filters["review_status"])
    if "class_name" in filters:
        query = query.filter(ContactModel.class_name.ilike(f"%{filters['class_name']}%"))
    if filters.get("is_anomaly"):
        query = query.filter(
            (ContactModel.anomaly_type == "UNKNOWN_ANOMALY") |
            (ContactModel.novelty_score >= 40.0)
        )
    if "survey_id" in filters:
        query = query.filter(ContactModel.survey_id.ilike(f"%{filters['survey_id']}%"))

    # Order by risk score descending, then confidence
    query = query.order_by(ContactModel.risk_score.desc(), ContactModel.confidence.desc())
    records = query.limit(req.limit or 25).all()

    contacts = [to_canonical_contact(r) for r in records]
    parsed_intent = " & ".join(intent_parts) if intent_parts else "General contact catalog query"

    summary = (
        f"Identified {len(contacts)} contacts matching '{parsed_intent}'. "
        f"Ranked by operational risk and calibrated confidence."
    )

    return AnalystQueryResponse(
        query=req.query,
        parsed_intent=parsed_intent,
        filters_applied=filters,
        total_matches=len(contacts),
        summary_text=summary,
        contacts=contacts
    )
