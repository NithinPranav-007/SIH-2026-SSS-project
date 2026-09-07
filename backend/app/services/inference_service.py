"""
Inference Orchestration Service.

Orchestrates the full end-to-end processing pipeline:
SSS Input -> Data Quality -> DRISHTI Preprocessing -> DRISHTI Detector ->
Tile Deduplication -> Acoustic Context Analysis -> Geolocation -> Priority Scoring ->
Canonical Contact Transformation.

Pluggable and configuration-driven.
"""

from typing import List, Optional
import os
import logging
import cv2

logger = logging.getLogger(__name__)

from backend.app.schemas.contact import Contact, ContactMeasurements, ContactExplanation
from backend.app.core.config import settings
from backend.app.core.model_registry import ModelRegistry
from ml.preprocessing.tiling import generate_tiles
from ml.preprocessing.quality import compute_image_quality
from ml.inference.drishti_detector import DrishtiDetector, DrishtiDetection
from ml.inference.postprocess import deduplicate_detections
from ml.inference.context import extract_acoustic_context
from ml.inference.classifier import SonarCropClassifier
from ml.inference.acoustic_fusion import AcousticFusionModel
from ml.inference.calibration import ConfidenceCalibrator
from ml.tracking.ping_tracker import SonarPingTracker
from ml.inference.measurement import TargetMeasurer
from ml.inference.embedding import ContactEmbedder
from ml.inference.anomaly import UnknownAnomalyDetector
from ml.inference.risk import RiskScorer
from ml.inference.explanation import ExplainabilityEngine
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
        self.classifier = SonarCropClassifier()
        self.acoustic_fusion = AcousticFusionModel()
        self.calibrator = ConfidenceCalibrator()
        self.tracker = SonarPingTracker()
        self.measurer = TargetMeasurer()
        self.embedder = ContactEmbedder()
        self.anomaly_detector = UnknownAnomalyDetector()
        self.risk_scorer = RiskScorer()
        self.expl_engine = ExplainabilityEngine()

    def run_survey_analysis(
        self,
        survey_id: str,
        raw_image_path: str,
        nav_file_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None
    ) -> List[Contact]:
        """
        Executes the full anomaly detection pipeline on an SSS survey swath.
        Returns a list of Canonical Contact objects with complete ML Intelligence metadata.
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
        quality_norm = float(quality_metrics.get("quality_score_normalized", 1.0))
        quality_100 = float(quality_metrics.get("quality_score", 100.0))

        # 2. Tiling for side-scan sonar waterfall swaths
        if img_w <= settings.IMAGE_SIZE and img_h <= settings.IMAGE_SIZE:
            raw_detections = self.detector.predict(
                image=raw_image,
                tile_id=f"{survey_id}_FULL",
                offset_x=0,
                offset_y=0
            )
        else:
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

        # 4. Multi-ping tracking association
        track_map = self.tracker.associate_detections(filtered_dicts, survey_id=survey_id)

        # 5. Geolocation service initialization
        geo_service = GeolocationService(nav_file_path=nav_file_path)

        # 6. Transform internal DrishtiDetection -> initial Canonical Contact schema
        contacts = transform_drishti_detections_to_contacts(
            detections=deduped_detections,
            survey_id=survey_id,
            data_quality=quality_norm,
            context_evaluator=None,
            geo_service=geo_service,
            image_width=img_w,
            image_height=img_h
        )

        # 7. ML Intelligence Upgrade Enrichment (Phases 2-5)
        pipeline_version = ModelRegistry.get_instance().get_active_stack_id()

        for idx, contact in enumerate(contacts):
            x1 = contact.bbox.x1
            y1 = contact.bbox.y1
            x2 = contact.bbox.x2
            y2 = contact.bbox.y2
            bbox_dict = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

            # Safe crop extraction
            crop = raw_image[max(0, y1):min(img_h, y2), max(0, x1):min(img_w, x2)]

            # Acoustic Context (extended 10 indicators)
            ctx = extract_acoustic_context(raw_image, bbox_dict, nadir_x=img_w // 2)
            contact.shadow_evidence = ctx["shadow_evidence"]
            contact.context_score = ctx["context_score"]

            # Second-stage Crop Classification (FP reduction)
            crop_res = self.classifier.classify_crop(crop, ctx)
            contact.classifier_confidence = crop_res["probability"]
            contact.classifier_label = crop_res["label"]
            contact.classifier_method = crop_res["method"]

            # Learned Acoustic Fusion
            fusion_res = self.acoustic_fusion.predict(
                ctx,
                detector_confidence=contact.confidence,
                data_quality=quality_norm
            )
            contact.acoustic_probability = fusion_res["acoustic_probability"]
            contact.evidence_score = fusion_res["evidence_score"]

            # Confidence Calibration
            calibrated = self.calibrator.calibrate(contact.confidence, data_quality=quality_norm)
            contact.calibrated_confidence = calibrated

            # Multi-ping Tracking Linkage
            track_obs = track_map.get(idx)
            if track_obs:
                contact.track_id = track_obs.track_id
                contact.track_observations = track_obs.observation_count
                contact.track_confidence = track_obs.track_confidence
                contact.track_stability = track_obs.track_stability
            else:
                contact.track_observations = 1

            # Metric Measurements
            measurements_dict = self.measurer.compute_measurements(
                bbox=bbox_dict,
                context=ctx,
                localization_status=contact.localization_status
            )
            contact.measurements = ContactMeasurements(**measurements_dict)

            # 37-dim Feature Embedding
            emb_vec = self.embedder.extract_embedding(
                crop=crop,
                context=ctx,
                bbox=bbox_dict,
                image_shape=(img_h, img_w),
                data_quality=quality_norm
            )

            # Unknown Anomaly Detection
            anomaly_res = self.anomaly_detector.compute_novelty(
                embedding=emb_vec,
                detector_confidence=calibrated,
                data_quality=quality_norm
            )
            contact.novelty_score = anomaly_res["novelty_score"]
            contact.anomaly_type = anomaly_res["anomaly_type"]

            # Calibrated Risk Scoring
            is_anomaly = (anomaly_res["anomaly_type"] == "UNKNOWN_ANOMALY")
            risk_res = self.risk_scorer.compute_risk(
                class_name=contact.class_name,
                confidence=calibrated,
                acoustic_prob=contact.acoustic_probability,
                measurements=measurements_dict,
                novelty_score=contact.novelty_score,
                is_unknown=is_anomaly
            )
            contact.risk_score = risk_res["risk_score"]
            contact.risk_level = risk_res["risk_level"]
            contact.risk_label = risk_res["risk_label"]

            # Explainability Evidence
            expl_dict = self.expl_engine.generate_explanation(
                detector_confidence=contact.confidence,
                acoustic_prob=contact.acoustic_probability,
                classifier_confidence=contact.classifier_confidence,
                context=ctx,
                track_persistence=contact.track_observations,
                novelty_score=contact.novelty_score,
                sonar_quality_score=quality_100,
                risk_score=contact.risk_score
            )
            contact.explanation = ContactExplanation(**expl_dict)

            # Model Provenance
            contact.pipeline_version = pipeline_version

        # Sort descending: HIGH priority first, then calibrated confidence or risk
        priority_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        contacts.sort(
            key=lambda c: (priority_rank.get(c.priority, 1), c.calibrated_confidence or c.confidence),
            reverse=True
        )

        # Re-number sorted contacts with survey-scoped IDs to prevent DB key collisions
        survey_prefix = survey_id[:16].replace("-", "_")
        for idx, contact in enumerate(contacts):
            contact.contact_id = f"{survey_prefix}_C{idx + 1:03d}"

        logger.info(
            "Survey '%s' analysis complete: %d contacts enriched with ML intelligence.",
            survey_id, len(contacts)
        )
        return contacts
