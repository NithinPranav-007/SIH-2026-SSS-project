"""
Centralized Configuration Architecture for SONAR-INTEL.

Structured into domain categories:
- APPLICATION  : Environment (development | test | production), debug mode, logging level
- SERVER       : Host, port, CORS origins
- DATABASE     : Connection URL, timeouts, fallback paths
- SONAR        : Waterfall tiling, Lee speckle filter, CLAHE enhancement
- DETECTOR     : Model provenance, paths, thresholds, inference devices
- SCORING      : Priority weights (confidence, context, quality, localization) & triage thresholds
- RISK         : Calibrated hazard thresholds & dimensions
- TRACKING     : Multi-ping tracking association tolerances
- STORAGE      : Project-relative storage paths (raw, processed, demo, export)
- SECURITY     : Upload limits, allowed extensions, sanitization policies

All settings support environment variable overrides with safe production defaults.
No secrets or machine-specific paths are hardcoded.
"""

import os
from pathlib import Path
from typing import List, Tuple


# Base workspace directory (project-relative, OS-independent)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class AppConfig:
    """Application & runtime environment configuration."""
    ENV: str = os.getenv("ENVIRONMENT", "development").lower()  # development | test | production
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    PROJECT_NAME: str = "SONAR-INTEL"
    PROJECT_VERSION: str = "2.0.0-industry"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


class ServerConfig:
    """Server & networking configuration."""
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
        ).split(",")
        if origin.strip()
    ]


class DatabaseConfig:
    """Database connectivity & fallback configuration."""
    URL: str = os.getenv("DATABASE_URL", "")
    CONNECT_TIMEOUT: int = int(os.getenv("DB_CONNECT_TIMEOUT", "2"))
    POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "false").lower() in ("true", "1", "yes")
    SQLITE_FALLBACK_NAME: str = "sonar_intel_fallback.db"

    @property
    def fallback_path(self) -> str:
        return str(BASE_DIR / self.SQLITE_FALLBACK_NAME)


class SonarConfig:
    """Sonar waterfall preprocessing & tiling hyperparameters."""
    IMAGE_SIZE: int = int(os.getenv("IMAGE_SIZE", "640"))
    TILE_SIZE: int = int(os.getenv("TILE_SIZE", "640"))
    TILE_OVERLAP: float = float(os.getenv("TILE_OVERLAP", "0.20"))

    PREPROCESSING_VERSION: str = os.getenv("PREPROCESSING_VERSION", "drishti-prep-v1")
    PREPROCESSING_SPECKLE_FILTER: str = os.getenv("PREPROCESSING_SPECKLE_FILTER", "lee")
    PREPROCESSING_CLAHE: bool = os.getenv("PREPROCESSING_CLAHE", "true").lower() in ("true", "1", "yes")

    LEE_WINDOW_SIZE: int = int(os.getenv("LEE_WINDOW_SIZE", "5"))
    LEE_NOISE_VAR: float = float(os.getenv("LEE_NOISE_VAR", "0.04"))
    CLAHE_CLIP_LIMIT: float = float(os.getenv("CLAHE_CLIP_LIMIT", "2.0"))
    CLAHE_TILE_GRID_SIZE: Tuple[int, int] = (
        int(os.getenv("CLAHE_GRID_X", "8")),
        int(os.getenv("CLAHE_GRID_Y", "8"))
    )


class DetectorConfig:
    """Primary detector model provenance & inference hyperparameters."""
    @staticmethod
    def _resolve_default_model_path() -> str:
        canonical = BASE_DIR / "ml" / "models" / "drishti" / "best_detector.pt"
        legacy = BASE_DIR / "ml" / "models" / "dristri" / "best_detector.pt"
        if canonical.exists():
            return str(canonical)
        if legacy.exists():
            return str(legacy)
        return str(canonical)

    @staticmethod
    def _resolve_default_calibrator_path() -> str:
        canonical = BASE_DIR / "ml" / "models" / "drishti" / "calibrator.pkl"
        legacy = BASE_DIR / "ml" / "models" / "dristri" / "calibrator.pkl"
        if canonical.exists():
            return str(canonical)
        if legacy.exists():
            return str(legacy)
        return str(canonical)

    MODEL_PATH: str = os.getenv("MODEL_PATH", _resolve_default_model_path())
    CALIBRATOR_PATH: str = os.getenv("CALIBRATOR_PATH", _resolve_default_calibrator_path())
    MODEL_NAME: str = os.getenv("MODEL_NAME", "DRISHTI-YOLOv8s")
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "baseline-v1")
    MODEL_SHA256: str = os.getenv(
        "MODEL_SHA256",
        "2f55eec5d8fe6b4737706392e259c02660a8542cddbcbd603f96d606c54cb927"
    )
    MODEL_SOURCE: str = os.getenv(
        "MODEL_SOURCE",
        "https://huggingface.co/rehan9599/drishti-detector"
    )
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
    IOU_THRESHOLD: float = float(os.getenv("IOU_THRESHOLD", "0.45"))
    NMS_IOU_THRESHOLD: float = float(os.getenv("NMS_IOU_THRESHOLD", "0.35"))
    MIN_BOX_SIZE: int = int(os.getenv("MIN_BOX_SIZE", "15"))
    DEVICE: str = os.getenv("DEVICE", "")  # Empty string triggers auto CUDA/CPU detection

    RAW_CLASSES: List[str] = [
        "crab_pot",
        "submarine_pipeline",
        "shipwreck",
        "ghost_net",
        "mine_cylinder"
    ]
    # Classes filtered from production contact creation (low precision raw classes)
    FILTERED_CLASSES: List[str] = [
        c.strip()
        for c in os.getenv("FILTERED_CLASSES", "crab_pot").split(",")
        if c.strip()
    ]


class ScoringConfig:
    """Composite priority scoring weights and triage thresholds."""
    W_CONFIDENCE: float = float(os.getenv("SCORING_CONFIDENCE_WEIGHT", "0.50"))
    W_CONTEXT: float = float(os.getenv("SCORING_CONTEXT_WEIGHT", "0.25"))
    W_QUALITY: float = float(os.getenv("SCORING_QUALITY_WEIGHT", "0.15"))
    W_LOCALIZATION: float = float(os.getenv("SCORING_LOCALIZATION_WEIGHT", "0.10"))

    HIGH_THRESHOLD: float = float(os.getenv("SCORING_HIGH_THRESHOLD", "0.72"))
    MEDIUM_THRESHOLD: float = float(os.getenv("SCORING_MEDIUM_THRESHOLD", "0.48"))


class RiskConfig:
    """Operational hazard risk assessment thresholds and constraints."""
    CRITICAL_THRESHOLD: float = float(os.getenv("RISK_CRITICAL_THRESHOLD", "80.0"))
    HIGH_THRESHOLD: float = float(os.getenv("RISK_HIGH_THRESHOLD", "60.0"))
    MEDIUM_THRESHOLD: float = float(os.getenv("RISK_MEDIUM_THRESHOLD", "35.0"))

    HAZARD_OBSTRUCTION_AREA_M2: float = float(os.getenv("HAZARD_OBSTRUCTION_AREA_M2", "100.0"))
    MIN_NOVELTY_ALERT: float = float(os.getenv("MIN_NOVELTY_ALERT", "40.0"))


class TrackingConfig:
    """Multi-ping along-track target association parameters."""
    MAX_TRACK_DISTANCE_M: float = float(os.getenv("TRACK_MAX_DISTANCE_M", "15.0"))
    MIN_OBSERVATIONS_STABLE: int = int(os.getenv("TRACK_MIN_OBSERVATIONS", "2"))
    TRACK_CONFIRMATION_THRESHOLD: float = float(os.getenv("TRACK_CONFIRMATION_THRESHOLD", "0.75"))


class StorageConfig:
    """Project-relative storage paths."""
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    DEMO_DIR: Path = BASE_DIR / "data" / "demo"
    EXPORT_DIR: Path = BASE_DIR / "data" / "active_learning_export"


class SecurityConfig:
    """Upload and security validation parameters."""
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "250")) * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"]
    ALLOWED_NAV_EXTENSIONS: List[str] = [".csv", ".txt", ".nav"]


class DriftConfig:
    """Ocean intelligence and ghost net drift forecasting hyperparameters and paths."""
    DRIFT_DATA_ROOT: Path = Path(os.getenv("DRIFT_DATA_ROOT", str(BASE_DIR / "data" / "ocean")))

    @staticmethod
    def _resolve_default_copernicus_path() -> str:
        # Check standard ocean raw directory first, then fallback to initial dataset folder
        standard_path = BASE_DIR / "data" / "ocean" / "copernicus" / "raw" / "cmems_mod_glo_phy_my_0.083deg_P1D-m_1788771128865.nc"
        initial_path = BASE_DIR / "drift_forecasting_dataset" / "cmems_mod_glo_phy_my_0.083deg_P1D-m_1788771128865.nc"
        if standard_path.exists():
            return str(standard_path)
        if initial_path.exists():
            return str(initial_path)
        return str(initial_path)

    COPERNICUS_DATA_PATH: str = os.getenv("COPERNICUS_DATA_PATH", _resolve_default_copernicus_path())
    INCOIS_LAS_URL: str = os.getenv(
        "INCOIS_LAS_URL",
        "https://las.incois.gov.in/las/output/3E501F741E424922D358B673CBA82351_ferret_listing.txt"
    )
    INCOIS_CACHE_PATH: Path = Path(os.getenv("INCOIS_CACHE_PATH", str(BASE_DIR / "data" / "ocean" / "incois" / "raw")))
    INCOIS_ONLINE_MODE: bool = os.getenv("INCOIS_ONLINE_MODE", "true").lower() in ("true", "1", "yes")

    ARGO_DATA_PATH: Path = Path(os.getenv("ARGO_DATA_PATH", str(BASE_DIR / "data" / "ocean" / "argo" / "raw")))
    INSITU_DATA_PATH: Path = Path(os.getenv("INSITU_DATA_PATH", str(BASE_DIR / "data" / "ocean" / "insitu" / "raw")))

    DRIFT_HISTORY_STEPS: int = int(os.getenv("DRIFT_HISTORY_STEPS", "24"))
    DRIFT_HORIZONS: List[int] = [int(h.strip()) for h in os.getenv("DRIFT_HORIZONS", "24,48,72").split(",") if h.strip()]
    MAX_TIME_GAP: float = float(os.getenv("MAX_TIME_GAP", "12.0"))  # hours
    INTERPOLATION_METHOD: str = os.getenv("INTERPOLATION_METHOD", "bilinear")

    # ML Hyperparameters
    GRU_HIDDEN_SIZE: int = int(os.getenv("GRU_HIDDEN_SIZE", "64"))
    GRU_LAYERS: int = int(os.getenv("GRU_LAYERS", "2"))
    GRU_DROPOUT: float = float(os.getenv("GRU_DROPOUT", "0.2"))

    LSTM_HIDDEN_SIZE: int = int(os.getenv("LSTM_HIDDEN_SIZE", "64"))
    LSTM_LAYERS: int = int(os.getenv("LSTM_LAYERS", "2"))
    LSTM_DROPOUT: float = float(os.getenv("LSTM_DROPOUT", "0.2"))

    LEARNING_RATE: float = float(os.getenv("LEARNING_RATE", "0.001"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    EPOCHS: int = int(os.getenv("EPOCHS", "50"))
    EARLY_STOPPING_PATIENCE: int = int(os.getenv("EARLY_STOPPING_PATIENCE", "7"))
    MIN_TRAJECTORIES_FOR_TRAINING: int = int(os.getenv("MIN_TRAJECTORIES_FOR_TRAINING", "10"))

    OUTPUTS_DIR: Path = BASE_DIR / "outputs" / "drift"
    MODELS_DIR: Path = BASE_DIR / "ml" / "models" / "drift"


class Settings:
    """Unified Settings Object combining all domain categories with backwards-compatible attributes."""
    def __init__(self):
        self.app = AppConfig()
        self.server = ServerConfig()
        self.database = DatabaseConfig()
        self.sonar = SonarConfig()
        self.detector = DetectorConfig()
        self.scoring = ScoringConfig()
        self.risk = RiskConfig()
        self.tracking = TrackingConfig()
        self.storage = StorageConfig()
        self.security = SecurityConfig()
        self.drift = DriftConfig()

        # ------------------------------------------------------------------
        # Backwards Compatibility Aliases (Preserves 100% of existing imports)
        # ------------------------------------------------------------------
        self.MODEL_PATH = self.detector.MODEL_PATH
        self.MODEL_NAME = self.detector.MODEL_NAME
        self.MODEL_VERSION = self.detector.MODEL_VERSION
        self.MODEL_SHA256 = self.detector.MODEL_SHA256
        self.MODEL_SOURCE = self.detector.MODEL_SOURCE

        self.IMAGE_SIZE = self.sonar.IMAGE_SIZE
        self.TILE_SIZE = self.sonar.TILE_SIZE
        self.TILE_OVERLAP = self.sonar.TILE_OVERLAP
        self.CONFIDENCE_THRESHOLD = self.detector.CONFIDENCE_THRESHOLD
        self.IOU_THRESHOLD = self.detector.IOU_THRESHOLD
        self.NMS_IOU_THRESHOLD = self.detector.NMS_IOU_THRESHOLD
        self.MIN_BOX_SIZE = self.detector.MIN_BOX_SIZE
        self.DEVICE = self.detector.DEVICE

        self.PREPROCESSING_VERSION = self.sonar.PREPROCESSING_VERSION
        self.PREPROCESSING_SPECKLE_FILTER = self.sonar.PREPROCESSING_SPECKLE_FILTER
        self.PREPROCESSING_CLAHE = self.sonar.PREPROCESSING_CLAHE
        self.LEE_WINDOW_SIZE = self.sonar.LEE_WINDOW_SIZE
        self.LEE_NOISE_VAR = self.sonar.LEE_NOISE_VAR
        self.CLAHE_CLIP_LIMIT = self.sonar.CLAHE_CLIP_LIMIT
        self.CLAHE_TILE_GRID_SIZE = self.sonar.CLAHE_TILE_GRID_SIZE

        self.RAW_CLASSES = self.detector.RAW_CLASSES
        self.FILTERED_CLASSES = self.detector.FILTERED_CLASSES


settings = Settings()
