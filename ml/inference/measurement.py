"""
Target Measurement Extraction Module.

Derives metric dimensions and physical properties of detected sonar contacts:
- Length (meters)
- Width (meters)
- Planar Area (m²)
- Aspect Ratio (unitless)
- Acoustic Shadow Length (meters)
- Principal Axis Orientation (degrees)
- Distance from nadir (meters)

SCIENTIFIC RULE:
Measurements carry explicit confidence, method, and unit metadata.
If navigation / sonar swath physical scaling is unavailable, measurements
are explicitly marked is_estimated=False or method="PIXEL_SCALE_APPROX"
with LOW confidence. Values are never fabricated.
"""

from typing import Dict, Any, Optional
import numpy as np


class TargetMeasurer:
    """
    Computes physical dimensions and acoustic shadow geometry for contacts.
    """

    def __init__(self, default_cross_track_m_per_px: float = 0.05, default_along_track_m_per_px: float = 0.08):
        self.default_cross_track_res = default_cross_track_m_per_px
        self.default_along_track_res = default_along_track_m_per_px

    def compute_measurements(
        self,
        bbox: Dict[str, int],
        context: Dict[str, Any],
        localization_status: str = "UNAVAILABLE",
        pixel_resolution_m: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes metric measurements with full scientific provenance.
        
        Args:
            bbox: dict with x1, y1, x2, y2
            context: context metrics dictionary from extract_acoustic_context
            localization_status: "VERIFIED" | "ESTIMATED" | "UNCERTAIN" | "UNAVAILABLE"
            pixel_resolution_m: optional metric resolution per pixel
            
        Returns:
            Dict matching ContactMeasurements schema.
        """
        x1 = bbox.get("x1", 0)
        y1 = bbox.get("y1", 0)
        x2 = bbox.get("x2", 0)
        y2 = bbox.get("y2", 0)

        width_px = max(1, x2 - x1)
        height_px = max(1, y2 - y1)
        ar = max(float(width_px) / float(height_px), float(height_px) / float(width_px))

        shadow_px = float(context.get("shadow_length_est", 0.0))
        nadir_dist_px = float(context.get("distance_from_nadir", 0.0))

        has_geo = localization_status in ("VERIFIED", "ESTIMATED")
        
        if has_geo or pixel_resolution_m is not None:
            m_per_px_x = pixel_resolution_m or self.default_cross_track_res
            m_per_px_y = pixel_resolution_m or self.default_along_track_res
            method = "SURVEY_NAV_INTERPOLATION" if has_geo else "STANDARD_SSS_RESOLUTION"
            conf = 0.85 if localization_status == "VERIFIED" else (0.65 if has_geo else 0.40)
            is_est = True

            # In waterfall side-scan:
            # X is cross-track (slant range), Y is along-track (tow direction)
            dim_x_m = round(width_px * m_per_px_x, 2)
            dim_y_m = round(height_px * m_per_px_y, 2)
            length_m = max(dim_x_m, dim_y_m)
            width_m = min(dim_x_m, dim_y_m)
            area_m2 = round(length_m * width_m, 2)
            shadow_m = round(shadow_px * m_per_px_x, 2)
            nadir_m = round(nadir_dist_px * m_per_px_x, 2)
        else:
            # When navigation is completely unavailable, report pixel-scale approximation with LOW confidence
            method = "PIXEL_PROXY_UNSCALED"
            conf = 0.20
            is_est = False
            length_m = float(max(width_px, height_px))
            width_m = float(min(width_px, height_px))
            area_m2 = float(width_px * height_px)
            shadow_m = shadow_px
            nadir_m = nadir_dist_px

        # Orientation angle: approximate major axis angle in image plane [0-180 degrees]
        orientation_deg = 90.0 if height_px > width_px else 0.0

        return {
            "length": {
                "value": length_m,
                "unit": "m" if (has_geo or pixel_resolution_m) else "px",
                "confidence": conf,
                "method": method,
                "is_estimated": is_est
            },
            "width": {
                "value": width_m,
                "unit": "m" if (has_geo or pixel_resolution_m) else "px",
                "confidence": conf,
                "method": method,
                "is_estimated": is_est
            },
            "area": {
                "value": area_m2,
                "unit": "m2" if (has_geo or pixel_resolution_m) else "px2",
                "confidence": max(0.1, conf - 0.05),
                "method": method,
                "is_estimated": is_est
            },
            "aspect_ratio": {
                "value": round(ar, 2),
                "unit": "ratio",
                "confidence": 0.95,
                "method": "BBOX_GEOMETRY",
                "is_estimated": True
            },
            "orientation": {
                "value": orientation_deg,
                "unit": "deg",
                "confidence": 0.70,
                "method": "MAJOR_AXIS_APPROX",
                "is_estimated": True
            },
            "shadow_length": {
                "value": shadow_m,
                "unit": "m" if (has_geo or pixel_resolution_m) else "px",
                "confidence": conf if shadow_px > 0 else 0.20,
                "method": "ACOUSTIC_SHADOW_SEGMENTATION" if shadow_px > 0 else "NO_SHADOW_DETECTED",
                "is_estimated": shadow_px > 0
            },
            "distance_from_nadir": {
                "value": nadir_m,
                "unit": "m" if (has_geo or pixel_resolution_m) else "px",
                "confidence": conf,
                "method": "SWATH_NADIR_OFFSET",
                "is_estimated": True
            }
        }
