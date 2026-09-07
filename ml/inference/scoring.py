"""
Decision and Priority Scoring Module.

Calculates operational Priority Score:
    priority_score = (
        w_conf * model_confidence +
        w_ctxt * context_score +
        w_qual * data_quality +
        w_loc  * localization_quality
    )

Triage tiers:
    - HIGH   (>= 0.75)
    - MEDIUM (>= 0.50)
    - LOW    (< 0.50)

SCIENTIFIC / DOMAIN HONESTY RULE:
Terminology is strictly 'Priority Score', never 'Probability of Ghost Net'
or 'Probability of Debris'. This score is an operational triage metric.
"""

from typing import Tuple


try:
    from backend.app.core.config import settings
    _DEFAULT_W_CONF = settings.scoring.W_CONFIDENCE
    _DEFAULT_W_CTXT = settings.scoring.W_CONTEXT
    _DEFAULT_W_QUAL = settings.scoring.W_QUALITY
    _DEFAULT_W_LOC = settings.scoring.W_LOCALIZATION
    _DEFAULT_HIGH = settings.scoring.HIGH_THRESHOLD
    _DEFAULT_MED = settings.scoring.MEDIUM_THRESHOLD
except Exception:
    _DEFAULT_W_CONF = 0.50
    _DEFAULT_W_CTXT = 0.25
    _DEFAULT_W_QUAL = 0.15
    _DEFAULT_W_LOC = 0.10
    _DEFAULT_HIGH = 0.72
    _DEFAULT_MED = 0.48


class PriorityScorer:
    def __init__(
        self,
        w_confidence: float = None,
        w_context: float = None,
        w_quality: float = None,
        w_localization: float = None,
        high_threshold: float = None,
        medium_threshold: float = None
    ):
        self.w_conf = _DEFAULT_W_CONF if w_confidence is None else w_confidence
        self.w_ctxt = _DEFAULT_W_CTXT if w_context is None else w_context
        self.w_qual = _DEFAULT_W_QUAL if w_quality is None else w_quality
        self.w_loc = _DEFAULT_W_LOC if w_localization is None else w_localization
        self.high_thresh = _DEFAULT_HIGH if high_threshold is None else high_threshold
        self.med_thresh = _DEFAULT_MED if medium_threshold is None else medium_threshold

    def calculate_priority(
        self,
        model_confidence: float,
        context_score: float,
        data_quality: float,
        localization_status: str
    ) -> Tuple[str, float]:
        """
        Computes composite priority score and category (HIGH, MEDIUM, LOW).
        
        Args:
            model_confidence: YOLO detector confidence [0.0 - 1.0].
            context_score: Acoustic physics plausibility [0.0 - 1.0].
            data_quality: Sonar swath quality index [0.0 - 1.0].
            localization_status: "VERIFIED", "ESTIMATED", "UNCERTAIN", or "UNAVAILABLE".
            
        Returns:
            Tuple of (priority_label, numeric_score)
        """
        # Map localization status to numerical quality
        loc_map = {
            "VERIFIED": 1.0,
            "ESTIMATED": 0.8,
            "UNCERTAIN": 0.4,
            "UNAVAILABLE": 0.0
        }
        loc_quality = loc_map.get(localization_status.upper(), 0.0)

        # Weighted calculation
        raw_score = (
            (self.w_conf * model_confidence) +
            (self.w_ctxt * context_score) +
            (self.w_qual * data_quality) +
            (self.w_loc * loc_quality)
        )
        score = round(max(0.0, min(1.0, raw_score)), 2)

        if score >= self.high_thresh:
            priority = "HIGH"
        elif score >= self.med_thresh:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return priority, score
