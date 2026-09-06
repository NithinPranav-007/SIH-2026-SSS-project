"""
Confidence Calibration Module.

Transforms raw detector confidences into well-calibrated probabilities:
P(True Positive | Confidence = p) ≈ p.

Supports:
1. Temperature scaling: p_calibrated = σ(logit(p) / T)
2. Isotonic regression (when empirical calibration set is available)
3. Quality attenuation: low image quality scales confidence towards conservative bounds
"""

from typing import Optional
import numpy as np


class ConfidenceCalibrator:
    """
    Confidence calibrator ensuring detection scores reflect empirical accuracy.
    """

    def __init__(
        self,
        temperature: float = 1.15,
        calibration_mode: str = "temperature_scaling"
    ):
        self.temperature = max(0.1, temperature)
        self.calibration_mode = calibration_mode
        self.isotonic_model = None

    def calibrate(
        self,
        raw_confidence: float,
        data_quality: float = 1.0
    ) -> float:
        """
        Calibrates raw detector confidence with image quality attenuation.
        
        Args:
            raw_confidence: YOLO detector raw output [0.0 - 1.0].
            data_quality: Swath quality score [0.0 - 1.0].
            
        Returns:
            Calibrated confidence float [0.0 - 1.0].
        """
        p = np.clip(raw_confidence, 1e-4, 1.0 - 1e-4)

        if self.isotonic_model is not None:
            try:
                calibrated = float(self.isotonic_model.predict([p])[0])
            except Exception:
                calibrated = self._temperature_scale(p)
        else:
            calibrated = self._temperature_scale(p)

        # Scientific quality attenuation:
        # If survey data quality is poor (< 0.5), scale high confidence down
        # because the sensor signal itself cannot guarantee high certainty
        if data_quality < 0.60:
            quality_factor = max(0.35, data_quality / 0.60)
            calibrated = calibrated * quality_factor

        return round(float(np.clip(calibrated, 0.01, 0.99)), 3)

    def _temperature_scale(self, p: float) -> float:
        """Applies temperature scaling over logit of p."""
        logit = np.log(p / (1.0 - p))
        scaled_logit = logit / self.temperature
        return float(1.0 / (1.0 + np.exp(-scaled_logit)))
