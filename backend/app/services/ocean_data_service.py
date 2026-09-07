"""
Ocean Environmental Data Monitoring Service.

Aggregates real-time availability, metadata, coordinate bounds, and freshness
for Copernicus Marine Service (GLORYS12V1) and INCOIS LAS catalogs.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ml.drift.ingestion.copernicus import CopernicusIngestor
from ml.drift.ingestion.incois_las import IncoisLasConnector

logger = logging.getLogger(__name__)


class OceanDataService:
    """Service providing operational health and dataset inventories for ocean data."""

    _cached_status: Optional[Dict[str, Any]] = None
    _last_checked: Optional[datetime] = None

    @classmethod
    def get_status(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves live or cached status of ocean data sources.
        """
        now = datetime.now(timezone.utc)
        if not force_refresh and cls._cached_status is not None and cls._last_checked is not None:
            # Cache for 60 seconds
            if (now - cls._last_checked).total_seconds() < 60:
                return cls._cached_status

        # 1. Copernicus status
        try:
            cop_ingestor = CopernicusIngestor()
            cop_audit = cop_ingestor.audit()
            copernicus_status = {
                "available": True,
                "dataset_product_id": cop_audit.get("dataset_product_id"),
                "dataset_id": cop_audit.get("dataset_id"),
                "drift_mode": cop_audit.get("drift_mode", "SURFACE_DRIFT_MODE"),
                "time_range": cop_audit.get("time_range", []),
                "depth_levels": cop_audit.get("depth_levels", []),
                "latitude_range": cop_audit.get("latitude_range", []),
                "longitude_range": cop_audit.get("longitude_range", []),
                "variables_available": list(cop_audit.get("variables", {}).keys()),
                "variables_count": cop_audit.get("variables_count", 0),
                "temporal_resolution": cop_audit.get("temporal_resolution", "P1D"),
                "spatial_resolution_deg": cop_audit.get("spatial_resolution_deg", 0.0833),
                "last_update": cop_audit.get("creation_date")
            }
        except Exception as e:
            logger.warning("Copernicus data unavailable: %s", e)
            copernicus_status = {
                "available": False,
                "error": str(e),
                "drift_mode": "UNAVAILABLE",
                "variables_available": []
            }

        # 2. INCOIS status
        try:
            inc_connector = IncoisLasConnector()
            inc_audit = inc_connector.audit()
            incois_status = {
                "available": inc_audit.get("status") == "AVAILABLE",
                "status": inc_audit.get("status", "INCOIS_SOURCE_UNAVAILABLE"),
                "source_mode": inc_audit.get("source_mode", "UNKNOWN"),
                "endpoint_url": inc_audit.get("endpoint_url"),
                "dataset_name": inc_audit.get("dataset_name"),
                "product_family": inc_audit.get("product_family"),
                "columns": inc_audit.get("columns", []),
                "variables": list(inc_audit.get("variables", {}).keys()),
                "total_records": inc_audit.get("total_records"),
                "spatial_coverage": inc_audit.get("spatial_coverage"),
                "last_update": inc_audit.get("last_audited")
            }
        except Exception as e:
            logger.warning("INCOIS LAS check failed: %s", e)
            incois_status = {
                "available": False,
                "status": "INCOIS_SOURCE_UNAVAILABLE",
                "error": str(e),
                "variables": []
            }

        status_payload = {
            "copernicus": copernicus_status,
            "incois": incois_status,
            "summary": {
                "all_sources_ready": copernicus_status.get("available", False),
                "drift_mode": copernicus_status.get("drift_mode", "SURFACE_DRIFT_MODE"),
                "copernicus_variables_count": len(copernicus_status.get("variables_available", [])),
                "incois_status": incois_status.get("status"),
                "missing_variables": ["wind_u", "wind_v", "wave_height", "wave_period"]
            },
            "last_checked": now.isoformat()
        }

        cls._cached_status = status_payload
        cls._last_checked = now
        return status_payload
