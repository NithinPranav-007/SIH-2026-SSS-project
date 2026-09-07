"""
Active Learning Service.

Captures operator review feedback as annotated training samples for model improvement.
Prioritizes samples with:
- High epistemic uncertainty (|p - 0.5| is low)
- Operator corrections (e.g. AI said HIGH, operator marked FALSE_POSITIVE)
- High novelty scores (rare / uncatalogued targets)

SAFETY RULE:
Captured samples inform retraining datasets but NEVER automatically
overwrite or update the active production model stack.
"""

from typing import List, Dict, Any, Optional
import datetime
import logging
from sqlalchemy.orm import Session

from backend.app.database.models import ContactModel, TrainingSampleModel

logger = logging.getLogger(__name__)


class ActiveLearningService:
    def __init__(self, db: Session):
        self.db = db

    def capture_review_sample(
        self,
        contact_id: str,
        review_status: str,
        review_note: Optional[str] = None
    ) -> Optional[TrainingSampleModel]:
        """
        Captures an operator review decision into the training_samples table.
        """
        contact = self.db.query(ContactModel).filter(ContactModel.contact_id == contact_id).first()
        if not contact:
            return None

        # Calculate sample priority & uncertainty score
        conf = contact.confidence if contact.confidence is not None else 0.5
        uncertainty = 1.0 - abs(conf - 0.5) * 2.0  # 1.0 when conf=0.5, 0.0 when conf=0 or 1

        is_fp_correction = (review_status == "FALSE_POSITIVE")
        is_novel = (contact.novelty_score or 0.0) >= 50.0

        if is_fp_correction or is_novel or uncertainty >= 0.70:
            priority = "HIGH"
        elif uncertainty >= 0.40:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Build feature snapshot
        acoustic_features = {
            "shadow_evidence": contact.shadow_evidence,
            "context_score": contact.context_score,
            "data_quality": contact.data_quality,
            "classifier_confidence": contact.classifier_confidence,
            "acoustic_probability": contact.acoustic_probability,
            "class_name": contact.class_name
        }

        sample = TrainingSampleModel(
            contact_id=contact.contact_id,
            survey_id=contact.survey_id,
            review_decision=review_status,
            review_note=review_note,
            reviewed_at=datetime.datetime.now(datetime.timezone.utc),
            pipeline_version=contact.pipeline_version,
            detector_confidence=contact.confidence,
            classifier_confidence=contact.classifier_confidence,
            acoustic_probability=contact.acoustic_probability,
            novelty_score=contact.novelty_score,
            risk_score=contact.risk_score,
            acoustic_features=acoustic_features,
            sample_priority=priority,
            uncertainty_score=round(uncertainty, 3)
        )

        try:
            self.db.add(sample)
            self.db.commit()
            self.db.refresh(sample)
            logger.info("Captured active learning sample for contact %s (Priority: %s)", contact_id, priority)
            return sample
        except Exception as exc:
            self.db.rollback()
            logger.warning("Failed to save active learning sample: %s", exc)
            return None

    def get_high_value_samples(self, min_priority: str = "MEDIUM", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Queries captured training samples surfaced for operator curation or model export.
        """
        priority_filter = ["HIGH"] if min_priority == "HIGH" else ["HIGH", "MEDIUM", "LOW"]
        samples = (
            self.db.query(TrainingSampleModel)
            .filter(TrainingSampleModel.sample_priority.in_(priority_filter))
            .order_by(TrainingSampleModel.uncertainty_score.desc())
            .limit(limit)
            .all()
        )

        results = []
        for s in samples:
            results.append({
                "sample_id": s.id,
                "contact_id": s.contact_id,
                "survey_id": s.survey_id,
                "review_decision": s.review_decision,
                "review_note": s.review_note,
                "sample_priority": s.sample_priority,
                "uncertainty_score": s.uncertainty_score,
                "detector_confidence": s.detector_confidence,
                "novelty_score": s.novelty_score,
                "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None
            })
        return results
