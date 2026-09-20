"""
GhostWatch Utility Functions
==============================
Date maths, PII stripping, JSON serialisation, logging, keyword maps.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ── Logging ──────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)-12s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("ghostwatch")

logger = setup_logging()

# ── Date helpers ─────────────────────────────────────────────────

def months_between(d1: date, d2: date) -> float:
    """Return approximate months between *d1* and *d2* (d2 > d1 → positive)."""
    return (d2.year - d1.year) * 12 + (d2.month - d1.month) + (d2.day - d1.day) / 30.0

# ── PII patterns & stripping ────────────────────────────────────

PII_PATTERNS: dict[str, re.Pattern] = {
    "phone":       re.compile(r"\b(?:\+91[\s-]?)?(?:\d{10}|\d{5}[\s-]\d{5})\b"),
    "email":       re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "aadhaar":     re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "name_prefix": re.compile(
        r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Shri|Smt\.?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
    ),
}


def strip_pii(text: str) -> str:
    """Remove obvious PII (phone, email, Aadhaar, titled names)."""
    result = text
    for label, pattern in PII_PATTERNS.items():
        result = pattern.sub(f"[REDACTED_{label.upper()}]", result)
    return result

# ── JSON helpers ─────────────────────────────────────────────────

def _json_default(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def save_trace(asset_id: str, trace: dict, logs_dir: Path) -> Path:
    """Persist the per-asset agent trace as a JSON file in *logs_dir*."""
    logs_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = logs_dir / f"trace_{asset_id}_{ts}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(trace, fh, indent=2, default=_json_default)
    return path

# ── Asset-type keyword maps ─────────────────────────────────────

ASSET_TYPE_KEYWORDS: dict[str, list[str]] = {
    "solar_streetlight": [
        "light", "streetlight", "solar", "dark", "lamp",
        "lighting", "illumination", "street light", "bulb",
    ],
    "water_atm": [
        "water", "atm", "dispenser", "drinking", "vending",
        "water machine", "purifier", "tap", "aqua",
    ],
    "ev_charger": [
        "ev", "charger", "charging", "electric vehicle",
        "charge point", "charging station", "battery",
    ],
    "rainwater_unit": [
        "rainwater", "harvest", "rain", "collection",
        "rainwater harvesting", "rain water", "rooftop",
    ],
}

ASSET_TYPE_DISPLAY: dict[str, str] = {
    "solar_streetlight": "Solar Streetlight",
    "water_atm":         "Water ATM",
    "ev_charger":        "EV Charger",
    "rainwater_unit":    "Rainwater Harvesting Unit",
}
