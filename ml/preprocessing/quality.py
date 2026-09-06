"""
Enhanced Sonar Quality Assessment Module.

Computes a comprehensive set of acoustic quality indicators for sonar waterfall imagery.
Used to scale downstream detection confidence appropriately.

SCIENTIFIC RULE: A low-quality sonar image must NOT produce the same
level of trust as a high-quality image. Quality propagates to confidence.

Indicators:
  - quality_score:        Composite 0–100 operational quality score
  - snr_db:              Signal-to-Noise Ratio proxy (dB)
  - dynamic_range:       Fraction of 256 gray-levels utilized [0.0 – 1.0]
  - blur_metric:         Laplacian variance (higher = sharper)
  - contrast_score:      Weber contrast measure [0.0 – 1.0]
  - shadow_visibility:   Bimodal histogram separation index [0.0 – 1.0]
  - nadir_interference:  Centre-column intensity spike indicator [0.0 – 1.0]
  - dropout_ratio:       Fraction of near-zero (dead-pixel) rows [0.0 – 1.0]
  - saturation_ratio:    Fraction of near-255 (clipped) pixels [0.0 – 1.0]
  - speckle_index:       Coefficient of variation in homogeneous region [0.0 – 1.0]
  - usable_area_ratio:   Fraction of image considered acoustically usable [0.0 – 1.0]
  - is_usable:           Boolean — True if composite quality >= 0.25
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any
import numpy as np
import cv2


@dataclass
class SonarQualityReport:
    """Structured quality report for a sonar swath image."""
    # --- Core (backward-compatible) ---
    quality_score: float          # 0–100 composite score (was 0–1, scaled for UI)
    snr_db: float
    dynamic_range: float
    blur_metric: float
    is_usable: bool

    # --- Enhanced indicators (Phase 1 additions) ---
    contrast_score: float         # Weber contrast [0–1]
    shadow_visibility: float      # Bimodal separation [0–1]
    nadir_interference: float     # Centre-column spike [0–1], higher = worse
    dropout_ratio: float          # Dead-pixel rows fraction [0–1]
    saturation_ratio: float       # Clipped pixel fraction [0–1]
    speckle_index: float          # CoV in flat region [0–1], higher = noisier
    usable_area_ratio: float      # Fraction of image usable [0–1]

    # --- Quality warnings ---
    warnings: list

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Expose quality_score_normalized for backward-compatible callers expecting [0,1]
        d["quality_score_normalized"] = round(self.quality_score / 100.0, 4)
        return d


def compute_image_quality(image: np.ndarray) -> Dict[str, Any]:
    """
    Computes a comprehensive sonar quality report.

    Args:
        image: Grayscale or BGR numpy array of the sonar swath.

    Returns:
        Dict matching SonarQualityReport fields. Always includes:
          - 'quality_score'     : float 0–100  (primary composite)
          - 'quality_score_normalized' : float 0–1  (backward compat)
          - 'snr_db', 'dynamic_range', 'blur_metric', 'is_usable'
          - Enhanced indicators: contrast_score, shadow_visibility, etc.
          - 'warnings': list of quality warning strings
    """
    if image is None or image.size == 0:
        report = SonarQualityReport(
            quality_score=0.0, snr_db=0.0, dynamic_range=0.0,
            blur_metric=0.0, is_usable=False, contrast_score=0.0,
            shadow_visibility=0.0, nadir_interference=0.0, dropout_ratio=1.0,
            saturation_ratio=0.0, speckle_index=1.0, usable_area_ratio=0.0,
            warnings=["INVALID_IMAGE: Empty or null input"]
        )
        return report.to_dict()

    # --- Convert to grayscale ---
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    gray = gray.astype(np.float32)
    h, w = gray.shape
    warnings = []

    # ---------------------------------------------------------------
    # 1. DYNAMIC RANGE  — fraction of 256 levels occupied
    # ---------------------------------------------------------------
    min_val, max_val = float(np.min(gray)), float(np.max(gray))
    dr_fraction = min(1.0, (max_val - min_val) / 255.0)
    if dr_fraction < 0.30:
        warnings.append("LOW_DYNAMIC_RANGE: Image uses fewer than 30% of grayscale range")

    # ---------------------------------------------------------------
    # 2. BLUR INDEX — variance of Laplacian (higher = sharper)
    # ---------------------------------------------------------------
    laplacian = cv2.Laplacian(gray.astype(np.uint8), cv2.CV_64F)
    laplacian_var = float(laplacian.var())
    blur_score = min(1.0, laplacian_var / 250.0)
    if blur_score < 0.20:
        warnings.append("LOW_SHARPNESS: Image is significantly blurred or defocused")

    # ---------------------------------------------------------------
    # 3. ACOUSTIC SNR PROXY — signal variability over mean backscatter
    # ---------------------------------------------------------------
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    snr_proxy = std_val / (mean_val + 1e-6)
    snr_score = min(1.0, snr_proxy / 0.8)
    snr_db = round(20.0 * np.log10(max(1.0, std_val)), 1)

    # ---------------------------------------------------------------
    # 4. WEBER CONTRAST SCORE — highlight vs. ambient mean
    # ---------------------------------------------------------------
    # Split image into top and bottom thirds as seabed reference zones
    region_h = h // 4
    top_region = gray[:region_h, :]
    bot_region = gray[h - region_h:, :]
    ambient_mean = float(np.mean(np.concatenate([top_region.ravel(), bot_region.ravel()])))
    highlight_peak = float(np.percentile(gray, 97))  # 97th percentile = near-max, robust to noise
    weber_contrast = abs(highlight_peak - ambient_mean) / (ambient_mean + 1e-6)
    contrast_score = min(1.0, weber_contrast / 2.5)
    if contrast_score < 0.20:
        warnings.append("LOW_CONTRAST: Insufficient highlight/shadow contrast for reliable detection")

    # ---------------------------------------------------------------
    # 5. SHADOW VISIBILITY — bimodal histogram separation
    # ---------------------------------------------------------------
    # In good SSS imagery, backscatter histogram is bimodal:
    # dark mode (shadow) separated from bright mode (highlight/seabed)
    hist, _ = np.histogram(gray, bins=64, range=(0, 256))
    hist_norm = hist / (hist.sum() + 1e-6)
    # Find two dominant peaks
    sorted_bins = np.argsort(hist_norm)[::-1]
    p1_idx = sorted_bins[0]
    # Second peak must be at least 8 bins away from the first
    p2_idx = next((b for b in sorted_bins[1:] if abs(int(b) - int(p1_idx)) >= 8), None)
    if p2_idx is not None:
        peak_separation = abs(int(p1_idx) - int(p2_idx)) / 64.0
        shadow_visibility = min(1.0, peak_separation * 2.0)
    else:
        shadow_visibility = 0.1
    if shadow_visibility < 0.25:
        warnings.append("LOW_SHADOW_VISIBILITY: Shadow/highlight separation not clear — difficult to assess acoustic context")

    # ---------------------------------------------------------------
    # 6. NADIR INTERFERENCE — centre-column intensity spike
    # ---------------------------------------------------------------
    # Side-scan sonar nadir produces a bright vertical stripe at swath centre
    nadir_half = max(1, int(w * 0.06))  # 6% of width each side
    nadir_strip = gray[:, max(0, w // 2 - nadir_half): min(w, w // 2 + nadir_half)]
    nadir_mean = float(np.mean(nadir_strip)) if nadir_strip.size > 0 else mean_val
    flanks_left = gray[:, max(0, w // 2 - nadir_half * 4): max(0, w // 2 - nadir_half)]
    flanks_right = gray[:, min(w, w // 2 + nadir_half): min(w, w // 2 + nadir_half * 4)]
    flank_parts = [p for p in [flanks_left, flanks_right] if p.size > 0]
    flank_mean = float(np.mean(np.concatenate([p.ravel() for p in flank_parts]))) if flank_parts else mean_val
    nadir_excess = max(0.0, nadir_mean - flank_mean)
    nadir_interference = min(1.0, nadir_excess / (flank_mean + 1e-6))
    if nadir_interference > 0.50:
        warnings.append("HIGH_NADIR_INTERFERENCE: Strong centre-stripe saturation may mask near-nadir targets")

    # ---------------------------------------------------------------
    # 7. DROPOUT RATIO — rows where >80% pixels are near-zero (dead lines)
    # ---------------------------------------------------------------
    row_means = np.mean(gray, axis=1)
    dropout_rows = np.sum(row_means < 5.0)
    dropout_ratio = float(dropout_rows) / float(h)
    if dropout_ratio > 0.05:
        warnings.append(f"SIGNAL_DROPOUT: {dropout_ratio * 100:.1f}% of rows are near-zero — possible data dropout")

    # ---------------------------------------------------------------
    # 8. SATURATION RATIO — fraction of pixels near 255 (clipped)
    # ---------------------------------------------------------------
    clipped_px = np.sum(gray > 248.0)
    saturation_ratio = float(clipped_px) / float(gray.size)
    if saturation_ratio > 0.05:
        warnings.append(f"SATURATION: {saturation_ratio * 100:.1f}% of pixels are clipped/saturated")

    # ---------------------------------------------------------------
    # 9. SPECKLE INDEX — coefficient of variation in a flat central region
    # ---------------------------------------------------------------
    # Use a 128×128 patch from the swath centre (typical flat seabed region)
    hy, hx = h // 2, w // 2
    ph = min(64, h // 8)
    pw = min(64, w // 8)
    flat_patch = gray[max(0, hy - ph): hy + ph, max(0, hx - pw): hx + pw]
    if flat_patch.size > 0:
        patch_mean = float(np.mean(flat_patch))
        patch_std = float(np.std(flat_patch))
        speckle_cov = patch_std / (patch_mean + 1e-6)
        # Ideal SSS speckle CoV is ~0.5; normalize so higher CoV = higher noise
        speckle_index = min(1.0, speckle_cov / 1.2)
    else:
        speckle_index = 0.5
    if speckle_index > 0.75:
        warnings.append("HIGH_SPECKLE: Excessive speckle noise in flat seabed region")

    # ---------------------------------------------------------------
    # 10. USABLE AREA RATIO
    # ---------------------------------------------------------------
    usable_px = np.sum((gray > 5.0) & (gray < 250.0))
    usable_area_ratio = float(usable_px) / float(gray.size)

    # ---------------------------------------------------------------
    # COMPOSITE QUALITY SCORE (0–100)
    # ---------------------------------------------------------------
    # Penalty factors from new indicators
    nadir_penalty = nadir_interference * 0.10
    dropout_penalty = dropout_ratio * 0.20
    saturation_penalty = saturation_ratio * 0.15

    base_score = (
        0.25 * dr_fraction +
        0.20 * blur_score +
        0.20 * snr_score +
        0.15 * contrast_score +
        0.12 * shadow_visibility +
        0.08 * usable_area_ratio
    )
    penalized_score = base_score - nadir_penalty - dropout_penalty - saturation_penalty
    composite_01 = round(max(0.05, min(0.99, penalized_score)), 4)
    quality_score_100 = round(composite_01 * 100.0, 1)

    report = SonarQualityReport(
        quality_score=quality_score_100,
        snr_db=snr_db,
        dynamic_range=round(dr_fraction, 3),
        blur_metric=round(laplacian_var, 1),
        is_usable=composite_01 >= 0.25,
        contrast_score=round(contrast_score, 3),
        shadow_visibility=round(shadow_visibility, 3),
        nadir_interference=round(nadir_interference, 3),
        dropout_ratio=round(dropout_ratio, 4),
        saturation_ratio=round(saturation_ratio, 4),
        speckle_index=round(speckle_index, 3),
        usable_area_ratio=round(usable_area_ratio, 3),
        warnings=warnings
    )
    return report.to_dict()
