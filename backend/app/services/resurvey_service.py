"""
Resurvey Recommendation Service.

Generates operational decision-support recommendations for survey vessels:
- Identifies degraded swathes or regions where low data quality masks targets
- Identifies clusters of high-uncertainty contacts requiring optical/AUV ground-truthing
- Flags areas with positioning dropout

SCIENTIFIC RULE:
Decision-support only. The system never autonomously alters survey lines.
Recommendations are ranked with transparent rationales.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database.models import SurveyModel


class ResurveyService:
    def __init__(self, db: Session):
        self.db = db

    def generate_recommendations(self, survey_id: str = None) -> List[Dict[str, Any]]:
        """
        Analyzes surveys and contacts to identify areas needing resurvey or ground truth.
        """
        recommendations = []

        query = self.db.query(SurveyModel)
        if survey_id:
            query = query.filter(SurveyModel.survey_id == survey_id)

        surveys = query.all()

        for s in surveys:
            # 1. Quality-based recommendation
            qual = s.data_quality if s.data_quality is not None else 1.0
            if qual < 0.45:
                recommendations.append({
                    "survey_id": s.survey_id,
                    "target_area": f"Full Swath ({s.filename})",
                    "priority": "HIGH",
                    "recommendation_type": "ACOUSTIC_RESURVEY",
                    "reason": f"Acoustic signal quality is severely compromised ({qual:.0%}). Center nadir saturation or dropout likely masked targets.",
                    "suggested_action": "Re-run sonar trackline with adjusted gain and reduced vessel speed",
                    "confidence": 0.85
                })

            # 2. Uncertainty contact cluster recommendation
            uncertain_contacts = [
                c for c in s.contacts
                if c.review_status == "UNCERTAIN" or c.localization_status in ("UNCERTAIN", "UNAVAILABLE")
            ]
            if len(uncertain_contacts) >= 2:
                recommendations.append({
                    "survey_id": s.survey_id,
                    "target_area": f"Cluster Zone ({len(uncertain_contacts)} contacts)",
                    "priority": "MEDIUM",
                    "recommendation_type": "AUV_OPTICAL_VERIFICATION",
                    "reason": f"{len(uncertain_contacts)} contacts have unresolved acoustic ambiguity or low geolocation certainty.",
                    "suggested_action": "Deploy ROV/AUV with optical camera or high-frequency imaging sonar for visual ground truthing",
                    "confidence": 0.75
                })

            # 3. High Novelty Anomalies
            novel_contacts = [
                c for c in s.contacts
                if (c.novelty_score or 0.0) >= 60.0 or c.anomaly_type == "UNKNOWN_ANOMALY"
            ]
            if novel_contacts:
                recommendations.append({
                    "survey_id": s.survey_id,
                    "target_area": f"Coordinates around {novel_contacts[0].contact_id}",
                    "priority": "HIGH",
                    "recommendation_type": "GROUND_TRUTH_INTERVENTION",
                    "reason": f"Presence of {len(novel_contacts)} high-novelty acoustic anomalies uncharacteristic of local seabed geology.",
                    "suggested_action": "Targeted bathymetric or magnetometer sweep to determine target composition",
                    "confidence": 0.90
                })

        return recommendations
