"""
Explainability Engine (XAI) for Sonar Contacts.

Synthesizes structured, interpretable explanations for operators:
- Positive acoustic/geometric evidence supporting detection
- Negative evidence or caveats dampening confidence
- Overall confidence label (HIGH CONFIDENCE | MODERATE | LOW | UNCERTAIN)
- Model provenance

SCIENTIFIC RULE:
Never fabricate evidence. If an indicator was not evaluated or unavailable,
it is omitted from the explanation list.
"""

from typing import Dict, Any, List, Optional


class ExplainabilityEngine:
    """
    Generates structured explainability evidence records for contacts.
    """

    def generate_explanation(
        self,
        detector_confidence: float,
        acoustic_prob: Optional[float] = None,
        classifier_confidence: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        track_persistence: Optional[int] = None,
        novelty_score: Optional[float] = None,
        sonar_quality_score: Optional[float] = None,
        risk_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds positive and negative evidence lists based on actual metrics.
        """
        positive_evidence: List[str] = []
        negative_evidence: List[str] = []

        # 1. Detector confidence
        if detector_confidence >= 0.75:
            positive_evidence.append(f"Strong YOLO detector feature activation ({detector_confidence:.0%})")
        elif detector_confidence < 0.45:
            negative_evidence.append(f"Marginal detector feature match ({detector_confidence:.0%})")

        # 2. Acoustic Context
        if context:
            shadow = float(context.get("shadow_evidence", 0.0))
            contrast = float(context.get("local_contrast", 0.0))
            shadow_len = float(context.get("shadow_length_est", 0.0))

            if shadow >= 0.60:
                positive_evidence.append(f"Distinct down-range acoustic shadow deficit ({shadow:.2f})")
            elif shadow < 0.20:
                negative_evidence.append("Minimal acoustic shadow deficit observed behind contact")

            if contrast >= 0.60:
                positive_evidence.append(f"High target highlight contrast against ambient seabed ({contrast:.2f})")
            elif contrast < 0.25:
                negative_evidence.append("Low contrast difference between contact and surrounding seabed")

            if shadow_len > 15.0:
                positive_evidence.append(f"Elongated acoustic shadow indicates significant vertical relief ({shadow_len:.0f} px)")

        # 3. Second-stage classifier
        if classifier_confidence is not None:
            if classifier_confidence >= 0.70:
                positive_evidence.append(f"Crop classifier confirms target morphology ({classifier_confidence:.0%})")
            elif classifier_confidence < 0.40:
                negative_evidence.append(f"Crop classifier indicates potential seabed clutter ({classifier_confidence:.0%})")

        # 4. Multi-ping tracking
        if track_persistence is not None and track_persistence > 1:
            positive_evidence.append(f"Target persists across {track_persistence} consecutive acoustic pings")
        elif track_persistence == 1:
            negative_evidence.append("Single-ping detection — not yet verified across multiple pings")

        # 5. Quality
        if sonar_quality_score is not None:
            if sonar_quality_score < 40.0:
                negative_evidence.append(f"Degraded sonar swath quality ({sonar_quality_score:.1f}/100) limits confidence")
            elif sonar_quality_score >= 80.0:
                positive_evidence.append(f"Optimal acoustic swath signal clarity ({sonar_quality_score:.1f}/100)")

        # 6. Novelty
        if novelty_score is not None and novelty_score >= 50.0:
            negative_evidence.append(f"High acoustic novelty ({novelty_score:.0f}/100) — does not match known archetypes")

        # Overall confidence tier
        evidence_balance = len(positive_evidence) - len(negative_evidence)
        if detector_confidence >= 0.75 and evidence_balance >= 2:
            confidence_label = "HIGH CONFIDENCE"
        elif detector_confidence >= 0.50 and evidence_balance >= 0:
            confidence_label = "MODERATE CONFIDENCE"
        elif detector_confidence < 0.40 or evidence_balance < -1:
            confidence_label = "LOW CONFIDENCE"
        else:
            confidence_label = "UNCERTAIN"

        return {
            "detector_confidence": round(detector_confidence, 3),
            "acoustic_probability": round(acoustic_prob, 3) if acoustic_prob is not None else None,
            "classifier_confidence": round(classifier_confidence, 3) if classifier_confidence is not None else None,
            "track_persistence_score": float(track_persistence) if track_persistence is not None else None,
            "novelty_score": round(novelty_score, 1) if novelty_score is not None else None,
            "sonar_quality_score": round(sonar_quality_score, 1) if sonar_quality_score is not None else None,
            "risk_score": round(risk_score, 1) if risk_score is not None else None,
            "positive_evidence": positive_evidence,
            "negative_evidence": negative_evidence,
            "overall_confidence_label": confidence_label,
            "method": "evidence_fusion_v1",
            "is_complete": True
        }
