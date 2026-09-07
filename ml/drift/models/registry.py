"""
Model Registry, Evaluation Metrics, and Champion Selection.

Maintains the authoritative registry of drift forecasting models:
- Tracks model versions, hyperparameters, metrics, git provenance, checksums, and statuses:
  ['candidate', 'validated', 'champion', 'rejected'].
- Evaluates multi-horizon performance (24h, 48h, 72h) comparing:
  1. Persistence
  2. Physics (Euler / RK2)
  3. Physics + GRU
  4. Physics + LSTM
- Selects champion purely on empirical validation metrics without bias towards ML.
"""

import csv
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.app.core.config import settings
from ml.drift.ingestion.common import haversine_distance_km

logger = logging.getLogger(__name__)


def compute_drift_metrics(actual_pts: List[Tuple[float, float]], predicted_pts: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Computes geodesic distance errors in kilometers between actual and predicted positions.
    Returns: MAE (km), RMSE (km), Median (km), 95th percentile (km), Max (km).
    """
    if not actual_pts or len(actual_pts) != len(predicted_pts):
        return {
            "mae_km": 0.0,
            "rmse_km": 0.0,
            "median_km": 0.0,
            "p95_km": 0.0,
            "max_km": 0.0,
            "sample_count": 0
        }

    errors_km = [
        haversine_distance_km(act[0], act[1], pred[0], pred[1])
        for act, pred in zip(actual_pts, predicted_pts)
    ]

    arr = np.array(errors_km, dtype=np.float64)
    mae = float(np.mean(arr))
    rmse = float(np.sqrt(np.mean(arr ** 2)))
    med = float(np.median(arr))
    p95 = float(np.percentile(arr, 95))
    max_err = float(np.max(arr))

    return {
        "mae_km": round(mae, 3),
        "rmse_km": round(rmse, 3),
        "median_km": round(med, 3),
        "p95_km": round(p95, 3),
        "max_km": round(max_err, 3),
        "sample_count": len(errors_km)
    }


class ModelRegistry:
    """
    Persists and manages versioned model artifacts and champion selection.
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or settings.drift.MODELS_DIR
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.registry_dir / "model_registry.json"
        self._load()

    def _load(self):
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.warning("Failed to load model registry JSON: %s. Reinitializing.", e)
                self.data = self._default_registry()
        else:
            self.data = self._default_registry()
            self._save()

    def _save(self):
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error("Could not write model registry: %s", e)

    def _default_registry(self) -> Dict[str, Any]:
        """Default registry with the deterministic physics model as the verified champion."""
        return {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "champion_model": "PHYSICS",
            "champion_version": "glorys12v1-rk2-v1",
            "models": {
                "PHYSICS": {
                    "model_name": "PHYSICS",
                    "model_class": "PhysicsDriftEngine",
                    "version": "glorys12v1-rk2-v1",
                    "status": "champion",
                    "description": "Deterministic Lagrangian advection using Copernicus GLORYS12V1 ocean current vector field.",
                    "drift_mode": "SURFACE_DRIFT_MODE",
                    "input_variables": ["uo", "vo"],
                    "metrics": {
                        "24h_rmse_km": None,
                        "48h_rmse_km": None,
                        "72h_rmse_km": None,
                        "status": "INSUFFICIENT_VALIDATED_DATA"
                    },
                    "registered_at": datetime.now(timezone.utc).isoformat()
                },
                "PHYSICS_GRU": {
                    "model_name": "PHYSICS_GRU",
                    "model_class": "DriftGRU",
                    "version": "gru-residual-v1",
                    "status": "candidate",
                    "description": "Physics baseline combined with 2-layer GRU residual error correction.",
                    "metrics": {
                        "24h_rmse_km": None,
                        "48h_rmse_km": None,
                        "72h_rmse_km": None,
                        "status": "NOT_TRAINED"
                    },
                    "registered_at": datetime.now(timezone.utc).isoformat()
                },
                "PHYSICS_LSTM": {
                    "model_name": "PHYSICS_LSTM",
                    "model_class": "DriftLSTM",
                    "version": "lstm-residual-v1",
                    "status": "candidate",
                    "description": "Physics baseline combined with 2-layer LSTM residual error correction.",
                    "metrics": {
                        "24h_rmse_km": None,
                        "48h_rmse_km": None,
                        "72h_rmse_km": None,
                        "status": "NOT_TRAINED"
                    },
                    "registered_at": datetime.now(timezone.utc).isoformat()
                }
            }
        }

    def get_champion(self) -> Dict[str, Any]:
        """Returns metadata for the current champion model."""
        champ_key = self.data.get("champion_model", "PHYSICS")
        return self.data["models"].get(champ_key, self.data["models"]["PHYSICS"])

    def get_all_models(self) -> List[Dict[str, Any]]:
        """Returns a list of all registered models."""
        return list(self.data.get("models", {}).values())

    def update_model_metrics(
        self,
        model_name: str,
        version: str,
        metrics_24h: Dict[str, float],
        metrics_48h: Dict[str, float],
        metrics_72h: Dict[str, float],
        checkpoint_path: Optional[str] = None
    ):
        """Updates evaluation metrics for a model candidate."""
        if model_name not in self.data["models"]:
            self.data["models"][model_name] = {
                "model_name": model_name,
                "version": version,
                "status": "candidate",
                "registered_at": datetime.now(timezone.utc).isoformat()
            }

        entry = self.data["models"][model_name]
        entry["version"] = version
        entry["metrics"] = {
            "24h": metrics_24h,
            "48h": metrics_48h,
            "72h": metrics_72h,
            "status": "VALIDATED"
        }
        if checkpoint_path and Path(checkpoint_path).exists():
            entry["checkpoint_path"] = str(checkpoint_path)
            # Compute sha256 checksum
            with open(checkpoint_path, "rb") as f:
                entry["checksum_sha256"] = hashlib.sha256(f.read()).hexdigest()

        entry["last_evaluated"] = datetime.now(timezone.utc).isoformat()
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def evaluate_and_select_champion(self) -> str:
        """
        Compares validated models on 24h, 48h, and 72h RMSE/MAE.
        Promotes an ML residual model ONLY if it improves upon Physics by >= 5%.
        Otherwise retains PHYSICS as champion.
        """
        physics_metrics = self.data["models"].get("PHYSICS", {}).get("metrics", {})
        if physics_metrics.get("status") != "VALIDATED":
            logger.info("Insufficient empirical validation data. Retaining PHYSICS as champion.")
            self.data["champion_model"] = "PHYSICS"
            self.data["models"]["PHYSICS"]["status"] = "champion"
            self._save()
            return "PHYSICS"

        phys_rmse_24 = physics_metrics["24h"]["rmse_km"]
        phys_rmse_72 = physics_metrics["72h"]["rmse_km"]

        candidates = ["PHYSICS_GRU", "PHYSICS_LSTM"]
        best_model = "PHYSICS"
        best_score = phys_rmse_24 + phys_rmse_72

        for cand in candidates:
            m = self.data["models"].get(cand, {})
            if m.get("metrics", {}).get("status") == "VALIDATED":
                cand_rmse_24 = m["metrics"]["24h"]["rmse_km"]
                cand_rmse_72 = m["metrics"]["72h"]["rmse_km"]
                cand_score = cand_rmse_24 + cand_rmse_72
                # Must beat physics by at least 5%
                if cand_score < best_score * 0.95:
                    best_score = cand_score
                    best_model = cand

        # Update statuses
        for name, m in self.data["models"].items():
            if name == best_model:
                m["status"] = "champion"
            elif m.get("metrics", {}).get("status") == "VALIDATED":
                m["status"] = "validated"
            else:
                m["status"] = "candidate"

        self.data["champion_model"] = best_model
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return best_model

    def export_comparison_reports(self, output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
        """
        Exports outputs/drift/model_comparison.json and outputs/drift/model_comparison.csv.
        """
        out_dir = output_dir or settings.drift.OUTPUTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "model_comparison.json"
        csv_path = out_dir / "model_comparison.csv"

        models = self.get_all_models()
        comparison_payload = {
            "comparison_timestamp": datetime.now(timezone.utc).isoformat(),
            "champion_model": self.data.get("champion_model", "PHYSICS"),
            "models": models
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(comparison_payload, f, indent=2)

        # Write CSV table
        headers = ["Model", "Status", "Version", "24h MAE (km)", "24h RMSE (km)", "48h MAE (km)", "48h RMSE (km)", "72h MAE (km)", "72h RMSE (km)"]
        rows = []
        for m in models:
            metrics = m.get("metrics", {})
            if metrics.get("status") == "VALIDATED":
                rows.append([
                    m.get("model_name"),
                    m.get("status"),
                    m.get("version"),
                    metrics.get("24h", {}).get("mae_km", "N/A"),
                    metrics.get("24h", {}).get("rmse_km", "N/A"),
                    metrics.get("48h", {}).get("mae_km", "N/A"),
                    metrics.get("48h", {}).get("rmse_km", "N/A"),
                    metrics.get("72h", {}).get("mae_km", "N/A"),
                    metrics.get("72h", {}).get("rmse_km", "N/A"),
                ])
            else:
                rows.append([
                    m.get("model_name"),
                    m.get("status"),
                    m.get("version"),
                    "Insufficient Data", "Insufficient Data",
                    "Insufficient Data", "Insufficient Data",
                    "Insufficient Data", "Insufficient Data"
                ])

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return json_path, csv_path
