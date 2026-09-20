"""
GhostWatch REST API Server (FastAPI)
===================================
Bridges the existing Python agent pipeline and data layer to modern frontends (React).
Maintains 100% of the existing backend architecture and business logic.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import (
    CROSS_REF_THRESHOLD,
    DEMO_MODE,
    ESCALATION_THRESHOLD,
    IBM_CREDENTIALS_AVAILABLE,
)
from src.data_loader import load_asset_registry, load_grievances
from src.orchestrator import PipelineResult, run_pipeline
from src.utils import ASSET_TYPE_DISPLAY, logger

app = FastAPI(
    title="GhostWatch AI Agent API",
    description="REST API for Public Sustainability Infrastructure Failure Detection",
    version="1.0.0",
)

# Enable CORS for React development (Vite, local servers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for audit pipeline results
_cached_result: Optional[PipelineResult] = None


def _serialize_obj(obj: Any) -> Any:
    """Recursively serialize dates and dataclasses into JSON-serializable structures."""
    if isinstance(obj, date):
        return obj.isoformat()
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize_obj(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _serialize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_obj(item) for item in obj]
    return obj


def get_pipeline_data(force_refresh: bool = False) -> PipelineResult:
    global _cached_result
    if _cached_result is None or force_refresh:
        logger.info("Running GhostWatch pipeline for API...")
        assets, _ = load_asset_registry()
        grievances = load_grievances()
        _cached_result = run_pipeline(assets=assets, grievances=grievances, save_traces=True)
    return _cached_result


@app.get("/api/health")
def health_check():
    """Health and engine configuration status."""
    return {
        "status": "healthy",
        "demo_mode": DEMO_MODE,
        "ibm_credentials_available": IBM_CREDENTIALS_AVAILABLE,
        "cross_ref_threshold": CROSS_REF_THRESHOLD,
        "escalation_threshold": ESCALATION_THRESHOLD,
    }


@app.get("/api/audit")
def get_audit_data():
    """
    Returns the complete GhostWatch audit pipeline output:
    summary KPIs, assets, flag reports, escalations, and agent traces.
    """
    data = get_pipeline_data()
    return {
        "summary": data.summary,
        "assets": [_serialize_obj(a) for a in data.assets],
        "reports": [_serialize_obj(r) for r in data.reports],
        "escalations": [_serialize_obj(e) for e in data.escalations],
        "traces": data.traces,
        "type_display_map": ASSET_TYPE_DISPLAY,
        "meta": {
            "demo_mode": DEMO_MODE,
            "ibm_credentials_available": IBM_CREDENTIALS_AVAILABLE,
            "escalation_threshold": ESCALATION_THRESHOLD,
        },
    }


@app.get("/api/asset/{asset_id}")
def get_asset_detail(asset_id: str):
    """Retrieve deep dive inspection data and agent trace for a specific asset."""
    data = get_pipeline_data()
    asset = next((a for a in data.assets if a.asset_id == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    report = next((r for r in data.reports if r.asset_id == asset_id), None)
    trace = data.traces.get(asset_id, {})
    escalation = next((e for e in data.escalations if e.asset_id == asset_id), None)

    return {
        "asset": _serialize_obj(asset),
        "report": _serialize_obj(report),
        "trace": trace,
        "escalation": _serialize_obj(escalation),
    }


@app.get("/api/escalations")
def get_escalations():
    """Retrieve all high-priority escalation notices."""
    data = get_pipeline_data()
    return {
        "count": len(data.escalations),
        "escalations": [_serialize_obj(e) for e in data.escalations],
    }


@app.post("/api/rerun")
def rerun_pipeline():
    """Trigger a fresh agent pipeline audit run and return updated results."""
    fresh_data = get_pipeline_data(force_refresh=True)
    return {
        "status": "success",
        "summary": fresh_data.summary,
        "reports_count": len(fresh_data.reports),
        "escalations_count": len(fresh_data.escalations),
    }


# Mount built React SPA in production if dist/ exists
from pathlib import Path
from fastapi.staticfiles import StaticFiles

_dist_dir = Path(__file__).parent / "frontend" / "dist"
if _dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(_dist_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
