"""
GhostWatch Agent Tools
======================
Standardized tool wrappers matching the Technical Requirements Document (§5).
Can be called directly or integrated into LangGraph / Agent workflows.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.cross_reference import cross_reference_classifier
from src.data_loader import load_asset_registry, load_grievances
from src.escalation import escalate
from src.guardrails import apply_guardrails
from src.models import (
    Asset,
    CrossRefMatch,
    EscalationNotice,
    FlagReport,
    Grievance,
    SilenceResult,
)
from src.rag import get_rag_store
from src.report_generator import generate_flag_report
from src.silence_scorer import silence_scorer
from src.utils import logger


def tool_load_asset_registry() -> tuple[list[Asset], list[dict]]:
    """
    Tool 1: load_asset_registry (§5.1)
    Loads and validates asset records from data source.
    """
    logger.info("Tool: load_asset_registry invoked")
    return load_asset_registry()


def tool_load_grievances() -> list[Grievance]:
    """
    Loads and validates grievance records with automatic PII redaction.
    """
    logger.info("Tool: load_grievances invoked")
    return load_grievances()


def tool_retrieve_signals(
    asset_location: str,
    asset_type: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Tool 2: retrieve_signals (§5.2)
    RAG retrieval: queries vector store for citizen grievance signals.
    """
    logger.info("Tool: retrieve_signals invoked for %s (%s)", asset_location, asset_type)
    store = get_rag_store()
    return store.retrieve_signals(asset_location=asset_location, asset_type=asset_type, top_k=top_k)


def tool_silence_scorer(
    asset: Asset,
    reference_date: Optional[date] = None,
) -> SilenceResult:
    """
    Tool 3: silence_scorer (§5.3)
    Computes time-gap silence score independent of complaint volume.
    """
    logger.info("Tool: silence_scorer invoked for %s", asset.asset_id)
    return silence_scorer(asset, reference_date=reference_date)


def tool_cross_reference_classifier(
    asset: Asset,
    retrieved_signals: list[dict],
    threshold: float = 0.70,
) -> list[CrossRefMatch]:
    """
    Tool 4: cross_reference_classifier (§5.4)
    Matches retrieved grievances to specific asset using semantic and metadata similarity.
    """
    logger.info("Tool: cross_reference_classifier invoked for %s", asset.asset_id)
    return cross_reference_classifier(asset, retrieved_signals, threshold=threshold)


def tool_generate_flag_report(
    asset: Asset,
    silence_result: SilenceResult,
    matched_complaints: list[CrossRefMatch],
    reference_date: Optional[date] = None,
) -> FlagReport:
    """
    Tool 5: generate_flag_report (§5.5)
    Synthesizes evidence into structured report with hedged language.
    """
    logger.info("Tool: generate_flag_report invoked for %s", asset.asset_id)
    return generate_flag_report(asset, silence_result, matched_complaints, reference_date=reference_date)


def tool_guardrails(
    report: FlagReport,
    retrieved_signals: list[dict],
) -> FlagReport:
    """
    Tool: guardrails screen (§6)
    Verifies hedge constraints, PII redaction, and evidence ID authenticity.
    """
    logger.info("Tool: guardrails invoked for %s", report.asset_id)
    return apply_guardrails(report, retrieved_signals)


def tool_escalate(
    report: FlagReport,
    asset: Asset,
    threshold: float = 0.75,
    reference_date: Optional[date] = None,
) -> Optional[EscalationNotice]:
    """
    Tool 6: escalate (§5.6)
    Generates formal inspection recommendation for high-confidence flags.
    """
    logger.info("Tool: escalate invoked for %s (conf: %.2f)", report.asset_id, report.confidence_score)
    return escalate(report, asset, threshold=threshold, reference_date=reference_date)
