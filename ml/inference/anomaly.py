"""
Unknown Acoustic Anomaly Detection Module.

Identifies novel, uncatalogued acoustic contacts that do not match known
training prototypes (e.g. standard ghost nets, boulders, shipwrecks, tires).

SCIENTIFIC PRINCIPLE:
- Computes Mahalanobis / Euclidean distance in the 37-dimensional feature space
  from verified class prototype centroids.
- Outputs novelty_score: 0–100 (0 = archetypal known object, 100 = completely unprecedented).
- Contacts with novelty_score >= 40.0, detector confidence >= 0.30, and quality >= 0.40
  are designated as UNKNOWN_ANOMALY.
- CRITICAL DOMAIN HONESTY RULE:
  UNKNOWN ANOMALY != HIGH RISK.
  A novel contact is simply unfamiliar to the model distribution.
  It is tagged for specialist operator inspection without false panic.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class UnknownAnomalyDetector:
    """
    Evaluates contact embedding distance from known prototype distributions.
    """

    def __init__(
        self,
        novelty_threshold: float = 40.0,
        min_confidence: float = 0.30,
        min_quality: float = 0.40
    ):
        self.novelty_threshold = novelty_threshold
        self.min_confidence = min_confidence
        self.min_quality = min_quality
        self.prototypes: Dict[str, np.ndarray] = {}
        self._init_default_prototypes()

    def _init_default_prototypes(self):
        """Initializes baseline acoustic prototype centroids."""
        # Simulated representative centroid vectors in 37-dim space
        np.random.seed(42)
        classes = ["ghost_net", "shipwreck", "pipeline", "boulder", "tire"]
        for c in classes:
            # Deterministic pseudo-prototype
            v = np.random.normal(loc=0.15, scale=0.1, size=(37,)).astype(np.float32)
            norm = np.linalg.norm(v)
            self.prototypes[c] = v / (norm + 1e-6)

    def compute_novelty(
        self,
        embedding: np.ndarray,
        detector_confidence: float = 0.50,
        data_quality: float = 1.0,
        known_prototypes: Optional[List[np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Computes novelty score and anomaly classification.
        
        Args:
            embedding: 37-dim L2-normalized vector
            detector_confidence: model confidence
            data_quality: swath quality score
            known_prototypes: optional custom prototype list
            
        Returns:
            {
                "novelty_score": float [0.0 - 100.0],
                "anomaly_type": "KNOWN_OBJECT" | "UNKNOWN_ANOMALY",
                "nearest_prototype_distance": float,
                "is_confident_anomaly": bool
            }
        """
        if embedding is None or len(embedding) == 0:
            return {
                "novelty_score": 50.0,
                "anomaly_type": "KNOWN_OBJECT",
                "nearest_prototype_distance": 0.5,
                "is_confident_anomaly": False
            }

        protos = known_prototypes if known_prototypes else list(self.prototypes.values())

        if len(protos) < 2:
            return {
                "novelty_score": 50.0,
                "anomaly_type": "KNOWN_OBJECT",
                "nearest_prototype_distance": 0.5,
                "is_confident_anomaly": False
            }

        # Calculate minimum Euclidean distance to any known prototype centroid
        distances = [float(np.linalg.norm(embedding - p)) for p in protos]
        min_dist = min(distances)

        # In L2 normalized space, maximum Euclidean distance is 2.0.
        # Typically between 0.3 (close) and 1.4 (distant).
        # Scale distance to 0–100 novelty score
        scaled_novelty = (min_dist / 1.4) * 100.0
        novelty_score = round(float(np.clip(scaled_novelty, 0.0, 100.0)), 1)

        # Classification rule
        is_unknown = (
            novelty_score >= self.novelty_threshold and
            detector_confidence >= self.min_confidence and
            data_quality >= self.min_quality
        )

        anomaly_type = "UNKNOWN_ANOMALY" if is_unknown else "KNOWN_OBJECT"

        return {
            "novelty_score": novelty_score,
            "anomaly_type": anomaly_type,
            "nearest_prototype_distance": round(min_dist, 3),
            "is_confident_anomaly": is_unknown
        }
