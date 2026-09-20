"""
End-to-End Pipeline & Integration Tests (§10 of Tech-Req).
Tests full workflow from data ingestion to RAG retrieval, silence scoring,
cross-referencing, guardrail screening, and escalation.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.orchestrator import evaluate_asset, run_pipeline


def test_full_pipeline_run():
    """Verify entire pipeline executes cleanly over all dataset records."""
    result = run_pipeline(save_traces=False)

    assert len(result.assets) == 50
    assert len(result.grievances) >= 50
    assert len(result.reports) == 50
    assert result.summary["silence_flags"] > 0
    assert result.summary["high_confidence_flags"] > 0
    assert len(result.escalations) > 0

    # Every single report must have passed guardrails hedge check
    for rep in result.reports:
        assert rep.output_language_hedge_check is True, f"Failed hedge check for {rep.asset_id}"


def test_seeded_known_broken_assets():
    """Verify known-broken assets with matching grievances trigger high-confidence flags."""
    result = run_pipeline(save_traces=False)
    report_map = {r.asset_id: r for r in result.reports}

    # SL-2023-114: Installed Feb 2023, 0 logs, grievances C-4471 & C-4502 exist
    sl_114 = report_map.get("SL-2023-114")
    assert sl_114 is not None
    assert sl_114.silence_flag is True
    assert len(sl_114.matched_complaints) > 0
    assert sl_114.confidence_score >= 0.75
    assert sl_114.recommended_action == "escalate"

    # WA-2023-156: Installed 2023, 0 logs, water atm grievances match
    wa_156 = report_map.get("WA-2023-156")
    assert wa_156 is not None
    assert wa_156.silence_flag is True
    assert wa_156.confidence_score >= 0.70


def test_seeded_known_working_assets():
    """Verify known-working assets are not flagged or escalated."""
    result = run_pipeline(save_traces=False)
    report_map = {r.asset_id: r for r in result.reports}

    # SL-2026-001: Recent maintenance log, no issues
    sl_01 = report_map.get("SL-2026-001")
    assert sl_01 is not None
    assert sl_01.silence_flag is False
    assert sl_01.confidence_score < 0.40
    assert sl_01.recommended_action == "monitor"

    # WA-2025-045: Installed recently, maintained
    wa_45 = report_map.get("WA-2025-045")
    assert wa_45 is not None
    assert wa_45.silence_flag is False
    assert wa_45.confidence_score < 0.40


def test_escalation_liability_assignment():
    """Verify that escalations correctly distinguish between contractor warranty and municipal liability."""
    result = run_pipeline(save_traces=False)

    for esc in result.escalations:
        assert esc.confidence_score >= 0.75
        assert len(esc.notice_text) > 100
        # Responsible party must be assigned
        assert "Contractor" in esc.responsible_party or "Municipal" in esc.responsible_party
        assert "CHECKLIST" in esc.notice_text.upper() or "AUDIT" in esc.notice_text.upper()
