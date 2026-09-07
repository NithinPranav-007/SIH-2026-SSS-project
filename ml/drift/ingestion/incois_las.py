"""
INCOIS LAS (Live Access Server) Ferret Listing Connector.

Interacts with the Indian National Centre for Ocean Information Services (INCOIS)
LAS catalog endpoint. Parses Ferret listings, discovers schemas dynamically,
caches sampled records, and provides resilient offline/online dual-mode operation.
"""

import re
import json
import time
import ssl
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone

from backend.app.core.config import settings
from ml.drift.ingestion.validators import FERRET_BAD_FLAG, is_bad_value

logger = logging.getLogger(__name__)


class IncoisLasConnector:
    """
    Connector for INCOIS Live Access Server (LAS) Ferret output listings.
    Discovers data structures dynamically without hardcoded assumptions.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        online_mode: Optional[bool] = None,
        timeout: int = 15,
        max_retries: int = 3
    ):
        self.url = url or settings.drift.INCOIS_LAS_URL
        self.cache_dir = Path(cache_dir or settings.drift.INCOIS_CACHE_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.cache_dir.parent / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.online_mode = online_mode if online_mode is not None else settings.drift.INCOIS_ONLINE_MODE
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch_header_and_sample(self, max_lines: int = 100) -> Tuple[List[str], str]:
        """
        Fetches the initial lines of the Ferret listing containing metadata and header definitions.
        Uses exponential backoff retries. Falls back to cached file if offline or unreachable.
        
        Returns:
            (lines, source_mode) where source_mode is "ONLINE" or "CACHED"
        """
        cached_file = self.cache_dir / "incois_las_sample.csv"

        if not self.online_mode:
            logger.info("INCOIS_ONLINE_MODE=False. Using local cache.")
            if cached_file.exists():
                with open(cached_file, "r", encoding="utf-8", errors="replace") as f:
                    lines = [f.readline() for _ in range(max_lines)]
                return [l for l in lines if l], "CACHED"
            return [], "INCOIS_SOURCE_UNAVAILABLE"

        # Online fetch with exponential backoff
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        headers = {"User-Agent": "Mozilla/5.0 (SONAR-INTEL Ocean Intelligence Adapter)"}
        req = urllib.request.Request(self.url, headers=headers)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Connecting to INCOIS LAS (attempt %d/%d)...", attempt, self.max_retries)
                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                    lines = []
                    for _ in range(max_lines):
                        line = resp.readline().decode("utf-8", errors="replace")
                        if not line:
                            break
                        lines.append(line)

                    # Cache sample to disk
                    with open(cached_file, "w", encoding="utf-8") as f:
                        f.writelines(lines)

                    return lines, "ONLINE"
            except Exception as exc:
                wait_time = 2 ** attempt
                logger.warning("INCOIS LAS request failed (attempt %d): %s. Backing off %ds...", attempt, exc, wait_time)
                if attempt < self.max_retries:
                    time.sleep(wait_time)

        # If online failed, check cached sample
        if cached_file.exists():
            logger.info("Online INCOIS request failed. Falling back to cached sample.")
            with open(cached_file, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
            return [l for l in lines if l], "CACHED"

        return [], "INCOIS_SOURCE_UNAVAILABLE"

    def audit(self) -> Dict[str, Any]:
        """
        Parses discovered INCOIS LAS metadata, variable definitions, coordinate system,
        and records information into data_audit.json schema.
        """
        lines, source_mode = self.fetch_header_and_sample(max_lines=150)

        if source_mode == "INCOIS_SOURCE_UNAVAILABLE" or not lines:
            return {
                "source": "INCOIS_LAS",
                "status": "INCOIS_SOURCE_UNAVAILABLE",
                "endpoint_url": self.url,
                "source_mode": source_mode,
                "message": "INCOIS LAS endpoint could not be reached and no local cache was found."
            }

        # Parse header lines
        dataset_name = "Unknown"
        total_records = None
        bad_flag = FERRET_BAD_FLAG
        column_descriptions = {}
        header_row_index = None

        for idx, line in enumerate(lines):
            line_str = line.strip()
            if "Total Number of Records" in line_str:
                m = re.search(r"Total Number of Records\s+([\d\.]+)", line_str)
                if m:
                    total_records = int(float(m.group(1)))
            elif "DATA SET:" in line_str:
                dataset_name = line_str.split("DATA SET:")[-1].strip()
            elif "Column" in line_str and "is" in line_str:
                # E.g. "Column  5: D26 is Depth of 26 Isotherm (mts) (no units)   BAD FLAG : -1.E+34"
                m_col = re.search(r"Column\s+(\d+):\s+([A-Za-z0-9_]+)\s+is\s+(.*?)(?:BAD FLAG\s*:\s*([^\s]+))?$", line_str)
                if m_col:
                    col_num = int(m_col.group(1))
                    col_name = m_col.group(2)
                    desc = m_col.group(3).strip()
                    flag = m_col.group(4)
                    column_descriptions[col_name] = {
                        "column_index": col_num,
                        "description": desc,
                        "bad_flag": flag or "-1.E+34"
                    }
            elif line_str.startswith("DATETIME,") or ("," in line_str and "TIME" in line_str):
                header_row_index = idx
                break

        # Discover columns from header row
        columns = []
        if header_row_index is not None and header_row_index < len(lines):
            columns = [c.strip() for c in lines[header_row_index].strip().split(",")]

        # Parse sample data rows
        sample_rows = []
        if header_row_index is not None:
            for row_line in lines[header_row_index + 1:]:
                row_str = row_line.strip()
                if not row_str or row_str.startswith("#"):
                    continue
                parts = [p.strip().strip('"') for p in row_str.split(",")]
                if len(parts) == len(columns):
                    sample_rows.append(parts)

        # Variables inventory
        variables_audit = {}
        for col_name in columns:
            col_info = column_descriptions.get(col_name, {})
            desc = col_info.get("description", "")
            unit = "unknown"
            if "degrees_east" in desc:
                unit = "degrees_east"
            elif "degrees_north" in desc:
                unit = "degrees_north"
            elif "DAYS since" in desc:
                unit = "days"
            elif "(mts)" in desc or "meters" in desc:
                unit = "m"
            elif "Time String" in desc:
                unit = "date_string"

            # Check sample values
            vals = []
            col_idx = columns.index(col_name)
            for r in sample_rows:
                v = r[col_idx]
                if not is_bad_value(v):
                    try:
                        vals.append(float(v))
                    except ValueError:
                        pass

            vmin = min(vals) if vals else None
            vmax = max(vals) if vals else None
            vmean = sum(vals) / len(vals) if vals else None

            variables_audit[col_name] = {
                "name": col_name,
                "description": desc,
                "units": unit,
                "bad_flag": col_info.get("bad_flag", "-1.E+34"),
                "sample_valid_count": len(vals),
                "sample_min": vmin,
                "sample_max": vmax,
                "sample_mean": round(vmean, 4) if vmean is not None else None
            }

        audit_result = {
            "source": "INCOIS_LAS",
            "status": "AVAILABLE",
            "source_mode": source_mode,
            "endpoint_url": self.url,
            "dataset_name": dataset_name,
            "product_family": "Argo Value Added Products",
            "total_records": total_records,
            "columns": columns,
            "variables": variables_audit,
            "spatial_coverage": "Indian Ocean Basin (Argo Array)",
            "observation_type": "Gridded / Value Added Isotherm Depth",
            "contains_currents_uo_vo": "uo" in columns or "vo" in columns,
            "contains_winds": "wind_u" in columns or "wind_v" in columns,
            "contains_waves": "wave_height" in columns,
            "last_audited": datetime.now(timezone.utc).isoformat()
        }

        # Save metadata JSON
        meta_file = self.metadata_dir / "incois_metadata.json"
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(audit_result, f, indent=2)
        except Exception as e:
            logger.warning("Could not write INCOIS metadata cache: %s", e)

        return audit_result
