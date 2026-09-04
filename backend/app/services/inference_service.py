"""
Inference Orchestration Service.

Orchestrates the full end-to-end processing pipeline:
SSS Input -> Data Quality -> DRISHTI Preprocessing -> DRISHTI Detector ->
Tile Deduplication -> Acoustic Context Analysis -> Geolocation -> Priority Scoring ->
Canonical Contact Transformation.

Pluggable and configuration-driven.
"""

from typing import List, Optional, Dict, Any
import os
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

from backend.app.schemas.contact import Contact, BoundingBox
from backend.app.core.config import settings
from ml.preprocessing.tiling import generate_tiles
from ml.preprocessing.quality import compute_image_quality
from ml.inference.drishti_detector import DrishtiDetector, DrishtiDetection
from ml.inference.postprocess import deduplicate_detections
from ml.inference.context import extract_acoustic_context
from backend.app.services.scoring_service import calculate_contact_priority
from backend.app.services.geolocation_service import GeolocationService
from backend.app.services.transformer import transform_drishti_detections_to_contacts


class InferenceService:
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        device: Optional[str] = None
    ):
        self.detector = DrishtiDetector(
            model_path=model_path or settings.MODEL_PATH,
            model_name=settings.MODEL_NAME,
            model_version=settings.MODEL_VERSION,
            confidence_threshold=confidence_threshold if confidence_threshold is not None else settings.CONFIDENCE_THRESHOLD,
            iou_threshold=iou_threshold if iou_threshold is not None else settings.IOU_THRESHOLD,
            device=device or settings.DEVICE
        )

    def run_survey_analysis(
        self,
        survey_id: str,
        raw_image_path: str,
        nav_file_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None
    ) -> List[Contact]:
        """
        Executes the full anomaly detection pipeline on an SSS survey swath.
        Returns a list of Canonical Contact objects.
        """
        if confidence_threshold is not None:
            self.detector.confidence_threshold = confidence_threshold

        if not os.path.exists(raw_image_path):
            raise FileNotFoundError(f"Sonar image not found: {raw_image_path}")

        raw_image = cv2.imread(raw_image_path)
        if raw_image is None:
            raise ValueError(f"Failed to decode image file: {raw_image_path}")

        img_h, img_w = raw_image.shape[:2]

        # 1. Compute Data Quality
        quality_metrics = compute_image_quality(raw_image)
        quality_score = quality_metrics.get("quality_score", 1.0)

        # 2. Tiling for side-scan sonar waterfall swaths
        # If image dimensions fit directly in 640x640, run directly
        if img_w <= settings.IMAGE_SIZE and img_h <= settings.IMAGE_SIZE:
            raw_detections = self.detector.predict(
                image=raw_image,
                tile_id=f"{survey_id}_FULL",
                offset_x=0,
                offset_y=0
            )
        else:
            # Generate deterministic overlapping 640x640 tiles
            tiles = generate_tiles(
                raw_image,
                tile_size=settings.IMAGE_SIZE,
                overlap=0.20
            )
            raw_detections: List[DrishtiDetection] = []
            for tile in tiles:
                tile_img = tile["tile_image"]
                offset_x = tile["offset_x"]
                offset_y = tile["offset_y"]
                tile_dets = self.detector.predict(
                    image=tile_img,
                    tile_id=f"{survey_id}_T{tile['tile_id']:03d}",
                    offset_x=offset_x,
                    offset_y=offset_y
                )
                raw_detections.extend(tile_dets)


        # 3. Deduplicate detections across overlapping tile boundaries
        # Adapt to dict format for existing deduplicate_detections
        det_dicts = [
            {
                "class_name": d.class_name,
                "confidence": d.confidence,
                "bbox": {"x1": d.bbox[0], "y1": d.bbox[1], "x2": d.bbox[2], "y2": d.bbox[3]},
                "tile_id": d.tile_id,
                "_original_obj": d
            }
            for d in raw_detections
        ]
        filtered_dicts = deduplicate_detections(det_dicts, iou_threshold=self.detector.iou_threshold)
        deduped_detections = [item["_original_obj"] for item in filtered_dicts]

        # 4. Geolocation service initialization
        geo_service = GeolocationService(nav_file_path=nav_file_path)

        # 5. Acoustic context evaluator callback
        def context_eval(bbox_coords: List[int]) -> Dict[str, float]:
            return extract_acoustic_context(
                image=raw_image,
                bbox={"x1": bbox_coords[0], "y1": bbox_coords[1], "x2": bbox_coords[2], "y2": bbox_coords[3]},
                nadir_x=img_w // 2
            )

        # 6. Transform internal DrishtiDetection -> Canonical Contact schema
        contacts = transform_drishti_detections_to_contacts(
            detections=deduped_detections,
            survey_id=survey_id,
            data_quality=quality_score,
            context_evaluator=context_eval,
            geo_service=geo_service,
            image_width=img_w,
            image_height=img_h
        )

        # Sort descending: HIGH priority first, then confidence
        priority_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        contacts.sort(
            key=lambda c: (priority_rank.get(c.priority, 1), c.confidence),
            reverse=True
        )

        # Re-number sorted contacts with survey-scoped IDs to prevent DB key collisions
        # Format: {survey_id_prefix}_C{index:03d} — unique per survey, never collides across surveys
        survey_prefix = survey_id[:16].replace("-", "_")  # Keep IDs compact
        for idx, contact in enumerate(contacts):
            contact.contact_id = f"{survey_prefix}_C{idx + 1:03d}"

        logger.info(
            "Survey '%s' analysis complete: %d contacts found.", survey_id, len(contacts)
        )
        return contacts
