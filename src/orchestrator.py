"""
GhostWatch Agentic Orchestrator
===============================
Coordinates the multi-step agent pipeline using LangGraph (with built-in fallback):
  load_asset_registry → retrieve_signals → silence_scorer →
  cross_reference_classifier → generate_flag_report → guardrails → escalate

Logs every reasoning step and saves per-asset JSON audit traces to logs/.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional, TypedDict

from src.config import LOGS_DIR
from src.data_loader import load_asset_registry, load_grievances
from src.models import (
    Asset,
    CrossRefMatch,
    EscalationNotice,
    FlagReport,
    Grievance,
    SilenceResult,
)
from src.rag import get_rag_store
from src.tools import (
    tool_cross_reference_classifier,
    tool_escalate,
    tool_generate_flag_report,
    tool_guardrails,
    tool_retrieve_signals,
    tool_silence_scorer,
)
from src.utils import logger, save_trace


class AgentState(TypedDict, total=False):
    """LangGraph / Pipeline state dictionary."""
    asset: Asset
    retrieved_signals: list[dict]
    silence_result: SilenceResult
    matched_complaints: list[CrossRefMatch]
    flag_report: FlagReport
    escalation_notice: Optional[EscalationNotice]
    trace: dict[str, Any]
    reference_date: Optional[date]


@dataclass
class PipelineResult:
    """Consolidated results of a full GhostWatch run."""
    assets: list[Asset] = field(default_factory=list)
    grievances: list[Grievance] = field(default_factory=list)
    reports: list[FlagReport] = field(default_factory=list)
    escalations: list[EscalationNotice] = field(default_factory=list)
    traces: dict[str, dict] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)


def evaluate_asset(
    asset: Asset,
    reference_date: Optional[date] = None,
    save_log: bool = True,
) -> tuple[FlagReport, Optional[EscalationNotice], dict]:
    """
    Execute full agent reasoning chain for a single asset.

    Steps:
      1. RAG retrieval of citizen grievance signals
      2. Silence score calculation (fairness: maintenance time gap only)
      3. Cross-reference classifier (similarity matching)
      4. Report synthesis (hedged language)
      5. Guardrail screening (PII, hedge check, evidence audit)
      6. Escalation dispatch check (>= 0.75 threshold)
    """
    start_time = time.perf_counter()
    steps_log: list[dict] = []

    # Step 1: RAG retrieval
    t0 = time.perf_counter()
    signals = tool_retrieve_signals(asset.location_name, asset.asset_type, top_k=5)
    steps_log.append({
        "step": 1,
        "name": "retrieve_signals",
        "description": "Retrieved grievance candidates from vector store using asset type and location",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "output_count": len(signals),
        "candidates": [s.get("complaint_id") for s in signals],
    })

    # Step 2: Silence Scorer
    t0 = time.perf_counter()
    silence_res = tool_silence_scorer(asset, reference_date=reference_date)
    steps_log.append({
        "step": 2,
        "name": "silence_scorer",
        "description": "Computed time-gap silence score based purely on maintenance logs vs expected interval",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "silence_flag": silence_res.silence_flag,
        "months_overdue": silence_res.months_overdue,
        "silence_score": silence_res.silence_score,
    })

    # Step 3: Cross-Reference Classifier
    t0 = time.perf_counter()
    matched_complaints = tool_cross_reference_classifier(asset, signals)
    steps_log.append({
        "step": 3,
        "name": "cross_reference_classifier",
        "description": "Filtered retrieved grievances using composite similarity (semantic + location + category)",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "matches": [
            {"id": m.complaint_id, "similarity": m.similarity} for m in matched_complaints
        ],
    })

    # Step 4: Report Generator
    t0 = time.perf_counter()
    raw_report = tool_generate_flag_report(
        asset, silence_res, matched_complaints, reference_date=reference_date
    )
    steps_log.append({
        "step": 4,
        "name": "generate_flag_report",
        "description": "Synthesized structured flag report with hedged language",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "confidence_score": raw_report.confidence_score,
        "recommended_action": raw_report.recommended_action,
    })

    # Step 5: Guardrails Screening
    t0 = time.perf_counter()
    guarded_report = tool_guardrails(raw_report, signals)
    steps_log.append({
        "step": 5,
        "name": "guardrails",
        "description": "Audited for hedged terminology, evidence ID validity, and PII redaction",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "hedge_check_passed": guarded_report.output_language_hedge_check,
    })

    # Step 6: Escalation check
    t0 = time.perf_counter()
    escalation = tool_escalate(guarded_report, asset, reference_date=reference_date)
    steps_log.append({
        "step": 6,
        "name": "escalate",
        "description": "Generated formal inspection recommendation notice if confidence >= 0.75",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "escalated": escalation is not None,
        "responsible_party": escalation.responsible_party if escalation else None,
    })

    total_duration = round((time.perf_counter() - start_time) * 1000, 2)

    # Compile trace object
    trace = {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type,
        "location": asset.location_name,
        "timestamp": date.today().isoformat(),
        "total_duration_ms": total_duration,
        "confidence_score": guarded_report.confidence_score,
        "silence_flag": guarded_report.silence_flag,
        "matched_complaints": guarded_report.matched_complaints,
        "recommended_action": guarded_report.recommended_action,
        "hedge_check_passed": guarded_report.output_language_hedge_check,
        "escalated": escalation is not None,
        "steps": steps_log,
    }

    if save_log:
        save_trace(asset.asset_id, trace, LOGS_DIR)

    return guarded_report, escalation, trace


def run_pipeline(
    assets: Optional[list[Asset]] = None,
    grievances: Optional[list[Grievance]] = None,
    reference_date: Optional[date] = None,
    save_traces: bool = True,
) -> PipelineResult:
    """
    Run the end-to-end GhostWatch audit pipeline over all registered assets.
    """
    logger.info("================ Starting GhostWatch Agent Pipeline ================")
    start_time = time.perf_counter()

    # Load data if not provided
    if assets is None:
        assets, _ = load_asset_registry()
    if grievances is None:
        grievances = load_grievances()

    # Initialize RAG store with loaded grievances
    rag_store = get_rag_store()
    rag_store.initialize(grievances)

    reports: list[FlagReport] = []
    escalations: list[EscalationNotice] = []
    traces: dict[str, dict] = {}

    for asset in assets:
        report, esc, trace = evaluate_asset(
            asset=asset,
            reference_date=reference_date,
            save_log=save_traces,
        )
        reports.append(report)
        if esc:
            escalations.append(esc)
        traces[asset.asset_id] = trace

    total_time = round(time.perf_counter() - start_time, 2)

    # Compute high-level summary metrics
    total_assets = len(assets)
    silence_flags = sum(1 for r in reports if r.silence_flag)
    complaint_matches = sum(1 for r in reports if len(r.matched_complaints) > 0)
    both_signals = sum(1 for r in reports if r.silence_flag and len(r.matched_complaints) > 0)
    high_conf = sum(1 for r in reports if r.confidence_score >= 0.75)
    warranty_active_flags = sum(1 for r in reports if r.warranty_active and (r.silence_flag or r.confidence_score >= 0.5))

    summary = {
        "total_assets": total_assets,
        "total_grievances": len(grievances),
        "silence_flags": silence_flags,
        "complaint_matches": complaint_matches,
        "both_signals": both_signals,
        "high_confidence_flags": high_conf,
        "warranty_active_flags": warranty_active_flags,
        "escalations_count": len(escalations),
        "total_runtime_seconds": total_time,
    }

    logger.info(
        "GhostWatch Completed: %d assets evaluated in %.2fs. Flags: %d, Escalations: %d",
        total_assets,
        total_time,
        high_conf,
        len(escalations),
    )

    return PipelineResult(
        assets=assets,
        grievances=grievances,
        reports=reports,
        escalations=escalations,
        traces=traces,
        summary=summary,
    )
