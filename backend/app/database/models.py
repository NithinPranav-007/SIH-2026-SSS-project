"""
SQLAlchemy Database Models for SONAR-INTEL.

Tables (original):
  - SurveyModel
  - ContactModel     (extended with Phase 1 ML intelligence columns)
  - ReviewModel

Tables (new — Phase 1 ML Intelligence Upgrade):
  - ModelVersionModel   — model stack version registry
  - TrackModel          — multi-ping contact persistence tracks
  - MeasurementModel    — physical target dimension estimates
  - EmbeddingModel      — contact feature embeddings for similarity search
  - TrainingSampleModel — active learning dataset samples

MIGRATION STRATEGY (SQLite compatible):
  All new ContactModel columns are NULLABLE with defaults.
  init_db() uses Base.metadata.create_all() which is additive —
  it creates new tables and is a no-op for existing ones.
  Existing data is never modified.
"""

import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    LargeBinary,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base


# ─────────────────────────────────────────────────────────────────────────────
# EXISTING TABLES (backward-compatible extensions only)
# ─────────────────────────────────────────────────────────────────────────────

class SurveyModel(Base):
    __tablename__ = "surveys"

    survey_id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    raw_image_path = Column(String(512), nullable=False)
    processed_image_path = Column(String(512), nullable=True)
    nav_file_path = Column(String(512), nullable=True)
    image_width = Column(Integer, default=0)
    image_height = Column(Integer, default=0)
    data_quality = Column(Float, default=1.0)
    has_navigation = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Phase 1: enhanced quality metrics stored as JSON
    quality_report = Column(JSON, nullable=True)

    contacts = relationship("ContactModel", back_populates="survey", cascade="all, delete-orphan")


class ContactModel(Base):
    __tablename__ = "contacts"

    contact_id = Column(String(64), primary_key=True, index=True)
    survey_id = Column(String(64), ForeignKey("surveys.survey_id", ondelete="CASCADE"), nullable=False, index=True)
    class_name = Column(String(64), default="artificial_anomaly", nullable=False)
    confidence = Column(Float, nullable=False)

    # Pixel coordinates in survey swath
    bbox_x1 = Column(Integer, nullable=False)
    bbox_y1 = Column(Integer, nullable=False)
    bbox_x2 = Column(Integer, nullable=False)
    bbox_y2 = Column(Integer, nullable=False)

    # Acoustic metrics (original)
    data_quality = Column(Float, default=1.0)
    shadow_evidence = Column(Float, default=0.0)
    context_score = Column(Float, default=0.0)
    priority = Column(String(16), default="MEDIUM", index=True)  # HIGH, MEDIUM, LOW

    # Geospatial (original)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    localization_status = Column(String(24), default="UNAVAILABLE")

    # Human-in-the-loop triage (original)
    review_status = Column(String(24), default="AI_CANDIDATE", index=True)
    review_note = Column(Text, nullable=True)

    model_version = Column(String(32), default="yolov8n-sonar-baseline")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # ── Phase 1 ML Intelligence additions (all nullable) ──────────────────
    # Model provenance
    pipeline_version = Column(String(64), nullable=True, index=True)  # stack_id from ModelRegistry

    # Second-stage classifier output
    classifier_confidence = Column(Float, nullable=True)   # REAL_TARGET probability [0–1]
    classifier_label = Column(String(32), nullable=True)   # REAL_TARGET | SONAR_CLUTTER
    classifier_method = Column(String(64), nullable=True)

    # Learned acoustic fusion output
    acoustic_probability = Column(Float, nullable=True)    # acoustic evidence score [0–1]
    evidence_score = Column(Float, nullable=True)

    # Calibrated confidence
    calibrated_confidence = Column(Float, nullable=True)

    # Multi-ping tracking
    track_id = Column(String(64), nullable=True, index=True)
    track_observations = Column(Integer, nullable=True)    # number of pings this contact spans
    track_confidence = Column(Float, nullable=True)
    track_stability = Column(Float, nullable=True)

    # Novelty / unknown anomaly
    novelty_score = Column(Float, nullable=True)           # 0–100 (0 = well-known, 100 = highly novel)
    anomaly_type = Column(String(32), nullable=True)       # KNOWN_OBJECT | UNKNOWN_ANOMALY

    # Risk intelligence
    risk_score = Column(Float, nullable=True)              # 0–100
    risk_level = Column(String(16), nullable=True, index=True)  # CRITICAL | HIGH | MEDIUM | LOW

    # Target measurements (stored as JSON for flexibility)
    measurements = Column(JSON, nullable=True)

    # Explainability evidence (JSON blob)
    explanation = Column(JSON, nullable=True)

    # Embedding reference (FK to EmbeddingModel)
    has_embedding = Column(Boolean, default=False)

    survey = relationship("SurveyModel", back_populates="contacts")
    reviews = relationship("ReviewModel", back_populates="contact", cascade="all, delete-orphan")
    embedding = relationship("EmbeddingModel", back_populates="contact", uselist=False, cascade="all, delete-orphan")
    measurements_detail = relationship("MeasurementModel", back_populates="contact", cascade="all, delete-orphan")
    training_samples = relationship("TrainingSampleModel", back_populates="contact", cascade="all, delete-orphan")


class ReviewModel(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(64), ForeignKey("contacts.contact_id", ondelete="CASCADE"), nullable=False, index=True)
    survey_id = Column(String(64), nullable=False)
    review_status = Column(String(24), nullable=False)
    review_note = Column(Text, nullable=True)
    model_version = Column(String(32), nullable=False)
    pipeline_version = Column(String(64), nullable=True)   # Phase 1 addition
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    contact = relationship("ContactModel", back_populates="reviews")


# ─────────────────────────────────────────────────────────────────────────────
# NEW TABLES (Phase 1 ML Intelligence Upgrade)
# ─────────────────────────────────────────────────────────────────────────────

class ModelVersionModel(Base):
    """
    Persistent record of every registered model stack.
    Every contact's pipeline_version FK references a stack_id here.
    """
    __tablename__ = "model_versions"

    stack_id = Column(String(64), primary_key=True)
    detector_name = Column(String(64), nullable=False)
    detector_version = Column(String(64), nullable=False)
    detector_sha256 = Column(String(64), nullable=True)
    preprocessing_version = Column(String(64), nullable=True)
    classifier_version = Column(String(64), nullable=True)
    acoustic_model_version = Column(String(64), nullable=True)
    anomaly_model_version = Column(String(64), nullable=True)
    calibration_version = Column(String(64), nullable=True)
    risk_model_version = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=False)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    notes = Column(Text, nullable=True)


class TrackModel(Base):
    """
    Multi-ping contact track: a sequence of spatially associated detections
    that represent the same physical object across consecutive sonar pings.
    """
    __tablename__ = "tracks"

    track_id = Column(String(64), primary_key=True)
    survey_id = Column(String(64), ForeignKey("surveys.survey_id", ondelete="CASCADE"), nullable=False, index=True)
    observation_count = Column(Integer, default=1)
    track_confidence = Column(Float, nullable=True)
    track_stability = Column(Float, nullable=True)
    start_ping_y = Column(Integer, nullable=True)   # Y-pixel proxy for start ping
    end_ping_y = Column(Integer, nullable=True)     # Y-pixel proxy for end ping
    # Representative centroid
    centroid_x = Column(Float, nullable=True)
    centroid_y = Column(Float, nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    primary_class = Column(String(64), nullable=True)
    mean_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))


class MeasurementModel(Base):
    """
    Physical measurement estimates for a contact.

    SCIENTIFIC RULE: Every measurement carries confidence and method.
    If measurement cannot be reliably derived, it is NOT stored.
    Operators see 'NOT ESTIMATED' rather than fabricated values.
    """
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(64), ForeignKey("contacts.contact_id", ondelete="CASCADE"), nullable=False, index=True)
    survey_id = Column(String(64), nullable=False)

    # Measurements — all nullable (stored only when defensible)
    length_m = Column(Float, nullable=True)
    length_confidence = Column(Float, nullable=True)    # 0–1
    length_method = Column(String(64), nullable=True)

    width_m = Column(Float, nullable=True)
    width_confidence = Column(Float, nullable=True)
    width_method = Column(String(64), nullable=True)

    area_m2 = Column(Float, nullable=True)
    area_confidence = Column(Float, nullable=True)

    aspect_ratio = Column(Float, nullable=True)         # always available from bbox
    orientation_deg = Column(Float, nullable=True)      # PCA-derived, may be None

    shadow_length_m = Column(Float, nullable=True)
    shadow_length_confidence = Column(Float, nullable=True)

    distance_from_nadir_m = Column(Float, nullable=True)
    localization_status = Column(String(24), nullable=True)

    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    contact = relationship("ContactModel", back_populates="measurements_detail")


class EmbeddingModel(Base):
    """
    37-dimensional feature vector embedding for a contact.
    Stored as a binary blob (numpy array serialized with numpy.save).
    Used for cosine-similarity search (FIND SIMILAR CONTACTS).

    Abstraction note: designed so the blob column can be replaced
    with a pgvector column for PostgreSQL vector search.
    """
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(64), ForeignKey("contacts.contact_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    survey_id = Column(String(64), nullable=False, index=True)
    class_name = Column(String(64), nullable=True)
    embedding_blob = Column(LargeBinary, nullable=False)    # numpy array bytes
    embedding_dim = Column(Integer, default=37)
    embedding_version = Column(String(32), default="acoustic-feature-v1")
    review_status = Column(String(24), nullable=True)       # denormalized for fast similarity filtering
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    contact = relationship("ContactModel", back_populates="embedding")


class TrainingSampleModel(Base):
    """
    Active learning dataset samples.

    Captures operator review decisions along with model outputs and features
    so they can be used to improve future model versions.

    SAFETY RULE: These samples inform retraining but NEVER automatically
    replace the production model. Manual evaluation and approval required.
    """
    __tablename__ = "training_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(64), ForeignKey("contacts.contact_id", ondelete="CASCADE"), nullable=False, index=True)
    survey_id = Column(String(64), nullable=False)

    # Operator decision
    review_decision = Column(String(24), nullable=False)  # CONFIRMED | FALSE_POSITIVE | UNCERTAIN
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Model outputs at time of review (snapshot)
    pipeline_version = Column(String(64), nullable=True)
    detector_confidence = Column(Float, nullable=True)
    classifier_confidence = Column(Float, nullable=True)
    acoustic_probability = Column(Float, nullable=True)
    novelty_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)

    # Feature snapshot (JSON)
    acoustic_features = Column(JSON, nullable=True)
    quality_report = Column(JSON, nullable=True)

    # Path to saved crop image (for visual retraining)
    crop_image_path = Column(String(512), nullable=True)

    # Active learning priority metadata
    sample_priority = Column(String(16), nullable=True)    # HIGH | MEDIUM | LOW
    uncertainty_score = Column(Float, nullable=True)       # |p - 0.5| inverted — high = uncertain

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    contact = relationship("ContactModel", back_populates="training_samples")


# ─────────────────────────────────────────────────────────────────────────────
# DRIFT FORECASTING & OCEAN INTELLIGENCE MODELS (Phase 2 Upgrade)
# ─────────────────────────────────────────────────────────────────────────────

class DriftForecastModel(Base):
    """
    Persistent record of an ocean drift forecast for a marine contact (e.g. ghost net).
    """
    __tablename__ = "drift_forecasts"

    forecast_id = Column(String(64), primary_key=True, index=True)
    contact_id = Column(String(64), ForeignKey("contacts.contact_id", ondelete="SET NULL"), nullable=True, index=True)
    initial_latitude = Column(Float, nullable=False)
    initial_longitude = Column(Float, nullable=False)
    initial_timestamp = Column(DateTime(timezone=True), nullable=False)
    depth = Column(Float, default=0.494)
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(64), nullable=False)
    data_version = Column(String(64), default="glorys12v1-daily")
    status = Column(String(32), default="COMPLETED")
    execution_mode = Column(String(32), default="REANALYSIS_ESTIMATE")  # REANALYSIS_ESTIMATE | OPERATIONAL_FORECAST
    hotspot_score = Column(Float, default=0.0)
    hotspot_evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    contact = relationship("ContactModel", backref="drift_forecasts")
    trajectory_points = relationship("DriftTrajectoryPointModel", back_populates="forecast", cascade="all, delete-orphan")
    uncertainty_regions = relationship("DriftUncertaintyModel", back_populates="forecast", cascade="all, delete-orphan")


class DriftTrajectoryPointModel(Base):
    """
    Spatial-temporal waypoint along a simulated drift trajectory.
    """
    __tablename__ = "drift_trajectory_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_id = Column(String(64), ForeignKey("drift_forecasts.forecast_id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    horizon_hours = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    east_displacement = Column(Float, nullable=False)   # meters
    north_displacement = Column(Float, nullable=False)  # meters
    uncertainty_radius = Column(Float, nullable=False)  # km
    model = Column(String(64), nullable=False)
    speed = Column(Float, nullable=True)               # m/s
    heading = Column(Float, nullable=True)             # deg (0-360)

    forecast = relationship("DriftForecastModel", back_populates="trajectory_points")


class DriftModelRunModel(Base):
    """
    Provenance registry for trained drift ML models and experiments.
    """
    __tablename__ = "drift_model_runs"

    run_id = Column(String(64), primary_key=True)
    model_name = Column(String(64), nullable=False)
    version = Column(String(64), nullable=False)
    training_date = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    status = Column(String(32), default="candidate")  # candidate | validated | champion | rejected
    checksum = Column(String(64), nullable=True)


class DriftUncertaintyModel(Base):
    """
    Empirical or probabilistic spatial uncertainty boundaries for multi-horizon forecast.
    """
    __tablename__ = "drift_uncertainties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_id = Column(String(64), ForeignKey("drift_forecasts.forecast_id", ondelete="CASCADE"), nullable=False, index=True)
    horizon_hours = Column(Float, nullable=False)       # 24, 48, 72
    uncertainty_radius_km = Column(Float, nullable=False)
    polygon_geojson = Column(JSON, nullable=True)

    forecast = relationship("DriftForecastModel", back_populates="uncertainty_regions")
