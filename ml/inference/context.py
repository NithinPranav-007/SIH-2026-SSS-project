"""
Acoustic-Context Intelligence Module.

Evaluates interpretable acoustic evidence around detected candidates:
1. Local Contrast: Target highlight vs. ambient seabed backscatter.
2. Acoustic Shadow Evidence: Deficit zone behind target highlight away from nadir.
3. Candidate Geometry: Aspect ratio, compactness, linearity.
4. Image Quality: Local acoustic signal quality.

Phase 2 additions (backward compatible):
5. Shadow length estimate (pixel shadow zone width)
6. Highlight intensity (97th percentile backscatter in crop)
7. Edge density (Sobel edge fraction)
8. Texture standard deviation (proxy for surface roughness)
9. Distance from nadir (cross-track pixels)
10. Object geometry metrics (area_px, bbox_width, bbox_height, aspect_ratio)

CRITICAL DOMAIN PRINCIPLE:
'No shadow evidence' != 'Negative shadow evidence'.
A flat, buried, or low-profile anthropogenic target (e.g. sunken cable, flat net)
may legitimately exhibit minimal shadow. Candidates are evaluated with graded
evidence without binary rejection.
"""

from typing import Dict, Any, Tuple
import numpy as np
import cv2


def extract_acoustic_context(
    image: np.ndarray,
    bbox: Dict[str, int],
    nadir_x: int = 640
) -> Dict[str, Any]:
    """
    Analyzes acoustic evidence for a bounding box region in the sonar image.

    Args:
        image: Full 2D grayscale or 3D BGR sonar image.
        bbox: dict with "x1", "y1", "x2", "y2".
        nadir_x: Horizontal center/nadir coordinate of the survey swath.

    Returns (backward-compatible + Phase 2 additions):
        {
            # Original 4 (unchanged)
            "shadow_evidence": float [0.0 - 1.0],
            "context_score": float [0.0 - 1.0],
            "quality_score": float [0.0 - 1.0],
            "local_contrast": float [0.0 - 1.0],

            # Phase 2 additions
            "shadow_length_est": float (pixels),
            "highlight_intensity": float [0.0 - 255.0],
            "edge_density": float [0.0 - 1.0],
            "texture_std": float,
            "distance_from_nadir": float (pixels),
            "object_area_px": int,
            "bbox_width": int,
            "bbox_height": int,
            "aspect_ratio": float,
        }
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h_img, w_img = gray.shape[:2]
    x1 = max(0, min(w_img - 1, bbox["x1"]))
    y1 = max(0, min(h_img - 1, bbox["y1"]))
    x2 = max(0, min(w_img, bbox["x2"]))
    y2 = max(0, min(h_img, bbox["y2"]))

    _null = {
        "shadow_evidence": 0.0, "context_score": 0.1,
        "quality_score": 0.5, "local_contrast": 0.0,
        "shadow_length_est": 0.0, "highlight_intensity": 0.0,
        "edge_density": 0.0, "texture_std": 0.0,
        "distance_from_nadir": float(abs((x1 + x2) // 2 - nadir_x)),
        "object_area_px": 0, "bbox_width": 0, "bbox_height": 0, "aspect_ratio": 1.0
    }

    if x2 <= x1 or y2 <= y1:
        return _null

    target_crop = gray[y1:y2, x1:x2]
    target_mean = float(np.mean(target_crop))
    target_max = float(np.max(target_crop))

    # ── Bounding box geometry ─────────────────────────────────────────────
    bbox_width = int(x2 - x1)
    bbox_height = int(y2 - y1)
    object_area_px = bbox_width * bbox_height
    aspect_ratio = max(float(bbox_width) / (float(bbox_height) + 1e-5),
                       float(bbox_height) / (float(bbox_width) + 1e-5))

    # ── 1. Local Ambient Seabed Ring (Neighborhood) ───────────────────────
    pad = int(max(15, (x2 - x1) * 0.5))
    amb_x1 = max(0, x1 - pad)
    amb_y1 = max(0, y1 - pad)
    amb_x2 = min(w_img, x2 + pad)
    amb_y2 = min(h_img, y2 + pad)
    ambient_crop = gray[amb_y1:amb_y2, amb_x1:amb_x2]
    ambient_mean = float(np.mean(ambient_crop)) if ambient_crop.size > 0 else 128.0

    # Local Contrast
    contrast_diff = max(0.0, target_max - ambient_mean)
    local_contrast = min(1.0, contrast_diff / 120.0)

    # ── 2. Highlight Intensity ────────────────────────────────────────────
    highlight_intensity = float(np.percentile(target_crop, 97)) if target_crop.size > 0 else 0.0

    # ── 3. Down-Range Acoustic Shadow Analysis ────────────────────────────
    target_center_x = (x1 + x2) / 2.0
    shadow_pad = int((x2 - x1) * 0.8)

    if target_center_x >= nadir_x:
        sh_x1 = min(w_img - 1, x2)
        sh_x2 = min(w_img, x2 + shadow_pad)
    else:
        sh_x1 = max(0, x1 - shadow_pad)
        sh_x2 = max(0, x1)

    shadow_length_est = 0.0
    if sh_x2 > sh_x1:
        shadow_crop = gray[y1:y2, sh_x1:sh_x2]
        shadow_mean = float(np.mean(shadow_crop)) if shadow_crop.size > 0 else ambient_mean
        shadow_deficit = max(0.0, ambient_mean - shadow_mean)
        shadow_evidence = min(1.0, shadow_deficit / max(20.0, ambient_mean * 0.6))

        # Estimate shadow zone extent: contiguous pixels darker than threshold
        shadow_threshold = ambient_mean * 0.60
        shadow_cols = shadow_crop if shadow_crop.ndim == 2 else shadow_crop[:, :, 0]
        col_means = np.mean(shadow_cols, axis=0)
        dark_cols = np.sum(col_means < shadow_threshold)
        shadow_length_est = float(dark_cols)
    else:
        shadow_evidence = 0.35  # neutral default at swath edge

    # ── 4. Geometric Regularity ───────────────────────────────────────────
    geom_score = 0.8 if 1.2 <= aspect_ratio <= 5.0 else 0.6

    # ── 5. Local Quality ──────────────────────────────────────────────────
    local_quality = min(1.0, float(np.std(target_crop)) / 45.0)

    # ── 6. Edge Density (Sobel) ───────────────────────────────────────────
    crop_u8 = target_crop.astype(np.uint8)
    sobel_x = cv2.Sobel(crop_u8, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(crop_u8, cv2.CV_64F, 0, 1, ksize=3)
    edge_mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    edge_density = float(np.mean(edge_mag > 30.0)) if crop_u8.size > 0 else 0.0

    # ── 7. Texture Standard Deviation ────────────────────────────────────
    texture_std = float(np.std(target_crop))

    # ── 8. Distance from Nadir ────────────────────────────────────────────
    distance_from_nadir = float(abs(target_center_x - nadir_x))

    # ── Composite Context Score (original formula preserved) ─────────────
    context_score = (
        0.40 * local_contrast +
        0.35 * shadow_evidence +
        0.15 * geom_score +
        0.10 * local_quality
    )
    context_score = round(max(0.1, min(0.99, context_score)), 2)

    return {
        # Original 4 (backward-compatible)
        "shadow_evidence": round(max(0.05, min(0.99, shadow_evidence)), 2),
        "context_score": context_score,
        "quality_score": round(max(0.2, min(0.99, local_quality)), 2),
        "local_contrast": round(local_contrast, 2),

        # Phase 2 additions
        "shadow_length_est": round(shadow_length_est, 1),
        "highlight_intensity": round(highlight_intensity, 1),
        "edge_density": round(edge_density, 3),
        "texture_std": round(texture_std, 2),
        "distance_from_nadir": round(distance_from_nadir, 1),
        "object_area_px": object_area_px,
        "bbox_width": bbox_width,
        "bbox_height": bbox_height,
        "aspect_ratio": round(aspect_ratio, 3),
    }
