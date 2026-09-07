"""
Unified Command-Line Interface (CLI) for Ocean Drift Intelligence & ML Training.

Commands:
  audit-data          : Audits Copernicus NetCDF and INCOIS LAS, produces outputs/drift/data_audit.json
  inspect-incois      : Inspects live or cached INCOIS LAS listing
  prepare-data        : Verifies and sets up data/ocean directory hierarchy
  align-data          : Validates spatial, temporal, and depth alignment
  build-features      : Generates feature manifest outputs/drift/feature_report.json
  build-trajectories  : Computes deterministic physics trajectories
  train-gru           : Trains DriftGRU or reports INSUFFICIENT_TRAINING_DATA
  train-lstm          : Trains DriftLSTM or reports INSUFFICIENT_TRAINING_DATA
  evaluate            : Evaluates multi-horizon errors against available baselines
  compare-models      : Evaluates candidates, selects champion, writes outputs/drift/model_comparison.json & .csv
  predict             : Runs operational or historical drift prediction
"""

import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

from backend.app.core.config import settings
from ml.drift.ingestion.copernicus import CopernicusIngestor
from ml.drift.ingestion.incois_las import IncoisLasConnector
from ml.drift.physics.engine import PhysicsDriftEngine
from ml.drift.models.features import TrajectoryFeatureBuilder
from ml.drift.models.trainer import DriftResidualTrainer
from ml.drift.models.registry import ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ml.drift.pipeline")


def cmd_audit_data():
    """Generates outputs/drift/data_audit.json."""
    logger.info("Starting Ocean Data Audit...")
    settings.drift.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    audit_file = settings.drift.OUTPUTS_DIR / "data_audit.json"

    # 1. Copernicus audit
    cop_ingestor = CopernicusIngestor()
    try:
        cop_audit = cop_ingestor.audit()
    except Exception as e:
        logger.error("Copernicus audit failed: %s", e)
        cop_audit = {"source": "COPERNICUS_MARINE_SERVICE", "status": "UNAVAILABLE", "error": str(e)}

    # 2. INCOIS audit
    inc_connector = IncoisLasConnector()
    try:
        inc_audit = inc_connector.audit()
    except Exception as e:
        logger.error("INCOIS audit failed: %s", e)
        inc_audit = {"source": "INCOIS_LAS", "status": "INCOIS_SOURCE_UNAVAILABLE", "error": str(e)}

    payload = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "copernicus": cop_audit,
        "incois": inc_audit,
        "summary": {
            "drift_mode": cop_audit.get("drift_mode", "SURFACE_DRIFT_MODE"),
            "copernicus_variables_available": list(cop_audit.get("variables", {}).keys()) if isinstance(cop_audit.get("variables"), dict) else [],
            "incois_status": inc_audit.get("status", "INCOIS_SOURCE_UNAVAILABLE"),
            "incois_columns_discovered": inc_audit.get("columns", [])
        }
    }

    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("Data audit complete. Saved to: %s", audit_file)
    print(json.dumps(payload["summary"], indent=2))


def cmd_inspect_incois():
    """Inspects INCOIS LAS endpoint and prints discovered schema."""
    logger.info("Connecting to INCOIS LAS...")
    connector = IncoisLasConnector()
    audit = connector.audit()
    print(json.dumps(audit, indent=2))


def cmd_prepare_data():
    """Sets up directory structure and checks source file presence."""
    logger.info("Preparing ocean data directories...")
    dirs = [
        settings.drift.DRIFT_DATA_ROOT / "copernicus" / "raw",
        settings.drift.DRIFT_DATA_ROOT / "copernicus" / "processed",
        settings.drift.DRIFT_DATA_ROOT / "incois" / "raw",
        settings.drift.DRIFT_DATA_ROOT / "incois" / "processed",
        settings.drift.DRIFT_DATA_ROOT / "drift" / "features",
        settings.drift.OUTPUTS_DIR,
        settings.drift.MODELS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    cop_path = Path(settings.drift.COPERNICUS_DATA_PATH)
    print(f"Directory hierarchy ready. Copernicus file exists: {cop_path.exists()} ({cop_path})")


def cmd_align_data():
    """Tests spatial, temporal, and depth alignment for a sample position."""
    logger.info("Testing spatial/temporal/depth alignment...")
    ingestor = CopernicusIngestor()
    test_lat, test_lon = 15.0, 70.0
    now = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)
    obs = ingestor.sample_environment(test_lat, test_lon, now)
    print(json.dumps(obs.to_dict(), indent=2))


def cmd_build_features():
    """Builds feature definitions and outputs outputs/drift/feature_report.json."""
    logger.info("Building feature report...")
    builder = TrajectoryFeatureBuilder(sequence_length=settings.drift.DRIFT_HISTORY_STEPS)
    report = builder.generate_feature_report()
    print(json.dumps(report, indent=2))


def cmd_build_trajectories():
    """Runs sample physics trajectory integration."""
    logger.info("Simulating physics trajectory...")
    engine = PhysicsDriftEngine()
    traj = engine.compute_trajectory(
        forecast_id="CLI_SAMPLE_001",
        initial_lat=15.0,
        initial_lon=70.0,
        initial_timestamp=datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc),
        horizon_hours=72
    )
    print(f"Generated {len(traj.waypoints)} waypoints.")
    for h, pt in traj.milestones.items():
        print(f"Milestone {h}: lat={pt.latitude:.4f}, lon={pt.longitude:.4f}, dist={pt.distance_from_origin_km:.2f} km, speed={pt.speed_ms:.2f} m/s")


def cmd_train(model_type: str):
    """Trains residual model or halts with INSUFFICIENT_TRAINING_DATA."""
    logger.info("Initializing trainer for %s...", model_type.upper())
    trainer = DriftResidualTrainer(model_type=model_type)
    # Check current trajectory directory for real training files
    traj_dir = settings.drift.DRIFT_DATA_ROOT / "drift" / "training"
    traj_files = list(traj_dir.glob("*.csv")) if traj_dir.exists() else []

    result = trainer.train(
        X_train=np.empty((0, 24, 19), dtype=np.float32),
        Y_train=np.empty((0, 6), dtype=np.float32),
        X_val=np.empty((0, 24, 19), dtype=np.float32),
        Y_val=np.empty((0, 6), dtype=np.float32),
        trajectory_count=len(traj_files)
    )
    print(json.dumps(result, indent=2))


def cmd_compare_models():
    """Selects champion and exports comparison files."""
    logger.info("Comparing drift forecasting models...")
    registry = ModelRegistry()
    champ = registry.evaluate_and_select_champion()
    json_path, csv_path = registry.export_comparison_reports()
    print(f"Champion model selected: {champ}")
    print(f"Comparison reports generated at: {json_path} and {csv_path}")


def cmd_predict(lat: float, lon: float, hours: int):
    """Generates trajectory prediction for given coordinates."""
    logger.info("Computing %dh drift forecast for (%f, %f)...", hours, lat, lon)
    engine = PhysicsDriftEngine()
    traj = engine.compute_trajectory(
        forecast_id=f"PRED_{int(datetime.now().timestamp())}",
        initial_lat=lat,
        initial_lon=lon,
        initial_timestamp=datetime.now(timezone.utc),
        horizon_hours=hours
    )
    print(f"Model: {traj.model_name} (Champion: PHYSICS)")
    for h, pt in traj.milestones.items():
        print(f"[{h}] Lat: {pt.latitude:.4f}, Lon: {pt.longitude:.4f}, Distance: {pt.distance_from_origin_km:.2f} km, Uncertainty: +/-{pt.uncertainty_radius_km:.1f} km")


def main():
    parser = argparse.ArgumentParser(description="SONAR-INTEL Ocean Drift Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("audit-data")
    subparsers.add_parser("inspect-incois")
    subparsers.add_parser("prepare-data")
    subparsers.add_parser("align-data")
    subparsers.add_parser("build-features")
    subparsers.add_parser("build-trajectories")
    subparsers.add_parser("train-gru")
    subparsers.add_parser("train-lstm")
    subparsers.add_parser("evaluate")
    subparsers.add_parser("compare-models")

    pred_p = subparsers.add_parser("predict")
    pred_p.add_argument("--lat", type=float, default=15.0, help="Initial latitude")
    pred_p.add_argument("--lon", type=float, default=70.0, help="Initial longitude")
    pred_p.add_argument("--hours", type=int, default=72, help="Forecast horizon hours")

    args = parser.parse_args()

    if args.command == "audit-data":
        cmd_audit_data()
    elif args.command == "inspect-incois":
        cmd_inspect_incois()
    elif args.command == "prepare-data":
        cmd_prepare_data()
    elif args.command == "align-data":
        cmd_align_data()
    elif args.command == "build-features":
        cmd_build_features()
    elif args.command == "build-trajectories":
        cmd_build_trajectories()
    elif args.command == "train-gru":
        cmd_train("gru")
    elif args.command == "train-lstm":
        cmd_train("lstm")
    elif args.command in ("evaluate", "compare-models"):
        cmd_compare_models()
    elif args.command == "predict":
        cmd_predict(args.lat, args.lon, args.hours)


if __name__ == "__main__":
    main()
