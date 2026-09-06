"""
Model Registry — Sonar-Intel.

Tracks every model artefact that produces predictions in the system.
Every contact must be traceable back to the exact model stack that produced it.

REPRODUCIBILITY RULE: A historical contact must always be traceable
to the model that generated it, at a specific version and timestamp.

Usage:
    registry = ModelRegistry.get_instance()
    stack_id = registry.get_active_stack_id()
    registry.get_active_stack()   # → ModelStack
"""

import os
import hashlib
import datetime
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ModelStack:
    """
    Complete model provenance record for a single prediction run.
    All IDs are version strings, not file paths.
    """
    detector_name: str = "DRISHTI-YOLOv8s"
    detector_version: str = "baseline-v1"
    detector_sha256: Optional[str] = None

    preprocessing_version: str = "drishti-prep-v1"

    classifier_name: str = "SonarCropClassifier"
    classifier_version: str = "acoustic-rule-v1"   # will update to cnn-v1 when trained

    acoustic_model_name: str = "AcousticFusionModel"
    acoustic_model_version: str = "rule-fusion-v1"  # will update to gbm-v1 when trained

    anomaly_model_name: str = "UnknownAnomalyDetector"
    anomaly_model_version: str = "mahalanobis-v1"

    calibration_version: str = "identity-v1"   # identity = pass-through until calibrated

    quality_module_version: str = "enhanced-v1"
    tracker_version: str = "iou-ping-v1"
    embedding_version: str = "acoustic-feature-v1"
    risk_model_version: str = "weighted-sum-v1"
    explainability_version: str = "evidence-fusion-v1"

    registered_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    is_active: bool = True

    @property
    def stack_id(self) -> str:
        """
        Stable compound ID from the concatenation of versioned components.
        Used as the pipeline_version field on every Contact record.
        """
        raw = (
            f"{self.detector_name}:{self.detector_version}:"
            f"{self.preprocessing_version}:"
            f"{self.classifier_version}:"
            f"{self.acoustic_model_version}:"
            f"{self.anomaly_model_version}"
        )
        digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return f"stack-{digest}"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stack_id"] = self.stack_id
        return d


class ModelRegistry:
    """
    Singleton model registry. Holds the active ModelStack.
    
    Lifecycle:
        DATASET → TRAIN → VALIDATE → EVALUATE → REGISTER → APPROVE → DEPLOY
        → MONITOR → COLLECT FEEDBACK → RETRAIN
    
    SAFETY RULE: Only approved stacks may be active. Never auto-deploy
    a candidate model without explicit approval.
    """
    _instance: Optional["ModelRegistry"] = None
    _active_stack: Optional[ModelStack] = None

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._initialize_default_stack()
        return cls._instance

    def _initialize_default_stack(self) -> None:
        """Sets up the baseline approved stack from environment / defaults."""
        from backend.app.core.config import settings

        # Compute SHA256 of model weights if they exist (for provenance)
        sha256 = None
        model_path = settings.MODEL_PATH
        if os.path.exists(model_path):
            try:
                h = hashlib.sha256()
                with open(model_path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                sha256 = h.hexdigest()
            except Exception:
                sha256 = settings.MODEL_SHA256  # fallback to configured value
        else:
            sha256 = settings.MODEL_SHA256

        self._active_stack = ModelStack(
            detector_name=settings.MODEL_NAME,
            detector_version=settings.MODEL_VERSION,
            detector_sha256=sha256,
            preprocessing_version=settings.PREPROCESSING_VERSION,
        )
        logger.info(
            "ModelRegistry initialized. Active stack: %s", self._active_stack.stack_id
        )

    def get_active_stack(self) -> ModelStack:
        if self._active_stack is None:
            self._initialize_default_stack()
        return self._active_stack

    def get_active_stack_id(self) -> str:
        return self.get_active_stack().stack_id

    def register_candidate_stack(self, stack: ModelStack) -> str:
        """
        Registers a candidate stack for evaluation.
        Does NOT make it active — requires explicit approval.
        Returns the stack_id.
        """
        logger.info(
            "Candidate stack registered (NOT active): %s. "
            "Requires evaluation and approval before deployment.",
            stack.stack_id
        )
        return stack.stack_id

    def approve_and_deploy(self, stack: ModelStack) -> str:
        """
        Promotes a validated candidate stack to active production.
        Must only be called after evaluation confirms the candidate
        is better than the current active stack.
        """
        old_id = self._active_stack.stack_id if self._active_stack else "none"
        stack.is_active = True
        stack.registered_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._active_stack = stack
        logger.info(
            "Model stack APPROVED and DEPLOYED. Old: %s → New: %s",
            old_id, stack.stack_id
        )
        return stack.stack_id

    def get_stack_info(self) -> Dict[str, Any]:
        """Returns the active stack as a dict suitable for the /api/ml/models endpoint."""
        return self.get_active_stack().to_dict()
