"""
Operational Risk Scoring Module.

Computes a calibrated Risk Score (0–100) and Tier:
- CRITICAL (>= 80)
- HIGH     (>= 60)
- MEDIUM   (>= 35)
- LOW      (< 35)

SCIENTIFIC / DOMAIN HONESTY RULES:
1. Unknown acoustic anomalies are NEVER automatically tagged CRITICAL or HIGH
   without physical or geospatial hazard indicators (e.g., massive size or navigation hazard).
2. Tiers reflect actionable maritime hazards: navigation obstructions, ghost gear
   entanglements, ordnance/unexploded explosive hazards, and high-confidence debris.
"""

from typing import Dict, Any, Optional, Tuple


class RiskScorer:
    """
    Computes maritime operational risk score from contact telemetry and dimensions.
    """

    CLASS_BASE_RISK = {
        "mine_like": 85.0,
        "ordnance": 85.0,
        "shipwreck": 65.0,
        "ghost_net": 60.0,
        "shipping_container": 65.0,
        "pipeline": 50.0,
        "artificial_anomaly": 40.0,
        "boulder": 25.0,
        "tire": 20.0,
        "seabed_clutter": 10.0
    }

    def compute_risk(
        self,
        class_name: str,
        confidence: float,
        acoustic_prob: float,
        measurements: Optional[Dict[str, Any]] = None,
        novelty_score: float = 0.0,
        is_unknown: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates operational risk score, tier, and descriptive label.
        
        Returns:
            {
                "risk_score": float [0.0 - 100.0],
                "risk_level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
                "risk_label": str
            }
        """
        # Base class risk
        base = self.CLASS_BASE_RISK.get(class_name.lower(), 40.0)

        # Scale by model and acoustic confidence
        evidence_factor = 0.5 * confidence + 0.5 * acoustic_prob

        # Size hazard factor
        size_factor = 0.0
        if measurements:
            length_val = measurements.get("length", {}).get("value")
            if length_val and isinstance(length_val, (int, float)):
                if length_val > 15.0:
                    size_factor = 15.0  # Large obstruction
                elif length_val > 5.0:
                    size_factor = 8.0

        # Novelty contribution: modest bump, never auto-critical
        novelty_factor = (novelty_score / 100.0) * 10.0 if is_unknown else 0.0

        raw_score = (base * evidence_factor) + size_factor + novelty_factor
        score = round(float(min(99.0, max(5.0, raw_score))), 1)

        # Tier assignment
        if score >= 80.0:
            level = "CRITICAL"
        elif score >= 60.0:
            level = "HIGH"
        elif score >= 35.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Descriptive label
        if is_unknown:
            label = "Uncatalogued acoustic anomaly — triage verification recommended"
        elif "net" in class_name.lower():
            label = "Marine fauna entanglement and propeller fouling hazard"
        elif "container" in class_name.lower() or "wreck" in class_name.lower():
            label = "Submerged physical navigation hazard to vessel traffic"
        elif score >= 80.0:
            label = "Potential ordnance or critical seabed obstruction"
        else:
            label = "Minor acoustic contact — non-critical monitoring"

        return {
            "risk_score": score,
            "risk_level": level,
            "risk_label": label
        }
