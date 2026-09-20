"""
GhostWatch Data Loader
=======================
Loads and validates CSV data into typed model objects.
"""

from __future__ import annotations

from typing import Tuple

import pandas as pd

from src.config import ASSET_REGISTRY_PATH, GRIEVANCES_PATH
from src.models import Asset, Grievance
from src.utils import logger, strip_pii

# ── Required fields per schema ───────────────────────────────────

_REQUIRED_ASSET_FIELDS = [
    "asset_id", "asset_type", "location_name", "latitude", "longitude",
    "install_date", "expected_service_interval_months", "warranty_end_date",
    "contractor_name",
]

_REQUIRED_GRIEVANCE_FIELDS = [
    "complaint_id", "complaint_text", "approx_location", "date_reported",
]


def load_asset_registry(path=None) -> Tuple[list[Asset], list[dict]]:
    """Load the asset registry CSV, validate required fields, return (assets, invalid_records)."""
    path = path or ASSET_REGISTRY_PATH
    logger.info("Loading asset registry from %s", path)

    df = pd.read_csv(path, dtype={"asset_id": str})
    assets: list[Asset] = []
    invalid: list[dict] = []

    for idx, row in df.iterrows():
        # Check required columns (last_maintenance_log_date may be null)
        missing = [f for f in _REQUIRED_ASSET_FIELDS if f not in df.columns or pd.isna(row.get(f))]
        if missing:
            invalid.append({"row": int(idx), "missing_fields": missing, "asset_id": row.get("asset_id", "UNKNOWN")})
            logger.warning("Row %d: missing %s", idx, missing)
            continue

        try:
            last_maint = None
            raw = row.get("last_maintenance_log_date")
            if pd.notna(raw) and str(raw).strip():
                last_maint = pd.to_datetime(raw).date()

            asset = Asset(
                asset_id=str(row["asset_id"]).strip(),
                asset_type=str(row["asset_type"]).strip(),
                location_name=str(row["location_name"]).strip(),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                install_date=pd.to_datetime(row["install_date"]).date(),
                expected_service_interval_months=int(row["expected_service_interval_months"]),
                warranty_end_date=pd.to_datetime(row["warranty_end_date"]).date(),
                contractor_name=str(row["contractor_name"]).strip(),
                last_maintenance_log_date=last_maint,
            )
            assets.append(asset)
        except Exception as exc:
            invalid.append({"row": int(idx), "error": str(exc), "asset_id": row.get("asset_id", "UNKNOWN")})
            logger.warning("Row %d parse error: %s", idx, exc)

    logger.info("Loaded %d valid assets, %d invalid records", len(assets), len(invalid))
    return assets, invalid


def load_grievances(path=None) -> list[Grievance]:
    """Load grievance corpus CSV, strip PII from complaint text on load."""
    path = path or GRIEVANCES_PATH
    logger.info("Loading grievances from %s", path)

    df = pd.read_csv(path, dtype={"complaint_id": str})
    grievances: list[Grievance] = []

    for idx, row in df.iterrows():
        missing = [f for f in _REQUIRED_GRIEVANCE_FIELDS if f not in df.columns or pd.isna(row.get(f))]
        if missing:
            logger.warning("Grievance row %d: missing %s — skipped", idx, missing)
            continue

        try:
            text = strip_pii(str(row["complaint_text"]))
            grievances.append(Grievance(
                complaint_id=str(row["complaint_id"]).strip(),
                complaint_text=text,
                approx_location=str(row["approx_location"]).strip(),
                date_reported=pd.to_datetime(row["date_reported"]).date(),
                category_tag=str(row["category_tag"]).strip() if pd.notna(row.get("category_tag")) else None,
            ))
        except Exception as exc:
            logger.warning("Grievance row %d parse error: %s", idx, exc)

    logger.info("Loaded %d grievances", len(grievances))
    return grievances
