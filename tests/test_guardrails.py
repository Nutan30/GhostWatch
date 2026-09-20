"""
Unit tests for GhostWatch Guardrails & Responsible AI Layer (§6 & §10 of Tech-Req).
Verifies:
1. No unhedged failure claims (enforces probabilistic language).
2. Evidence hallucination prevention (only valid retrieved IDs allowed).
3. PII redaction (phones, emails, Aadhaar, names).
"""

from __future__ import annotations

import pytest

from src.guardrails import (
    apply_guardrails,
    check_hedged_language,
    validate_evidence_ids,
)
from src.models import FlagReport
from src.utils import strip_pii


# ── Hedged Language Tests ───────────────────────────────────────────

def test_unhedged_failure_claims_are_hedged():
    """Definitive claims like 'is broken' or 'has failed' must be sanitized."""
    asserted_text = "Streetlight SL-101 is broken and has failed completely."
    passed, sanitized = check_hedged_language(asserted_text)

    assert passed is True
    assert "is broken" not in sanitized.lower()
    assert "has failed" not in sanitized.lower()
    assert "probable operational failure" in sanitized.lower() or "likely non-functional" in sanitized.lower()


def test_hedged_claims_remain_intact():
    """Already hedged language passes without unwanted mutation."""
    good_text = "Asset SL-101 exhibits indications of probable operational failure based on telemetry."
    passed, sanitized = check_hedged_language(good_text)

    assert passed is True
    assert "probable operational failure" in sanitized


# ── PII Redaction Tests ─────────────────────────────────────────────

def test_pii_phone_number_redaction():
    text = "Citizen reported issue. Call Mr. Sharma at 9876543210 immediately."
    clean = strip_pii(text)
    assert "9876543210" not in clean
    assert "[REDACTED_PHONE]" in clean


def test_pii_email_redaction():
    text = "Contact officer via complaint.officer@mumbai.gov.in regarding the broken pump."
    clean = strip_pii(text)
    assert "complaint.officer@mumbai.gov.in" not in clean
    assert "[REDACTED_EMAIL]" in clean


def test_pii_aadhaar_redaction():
    text = "Resident ID 1234-5678-9012 lodged this complaint."
    clean = strip_pii(text)
    assert "1234-5678-9012" not in clean
    assert "[REDACTED_AADHAAR]" in clean


# ── Evidence Hallucination Defense ──────────────────────────────────

def test_hallucinated_evidence_rejection():
    """IDs cited in report that are not in retrieval signals must be stripped/rejected."""
    report = FlagReport(
        asset_id="SL-101",
        confidence_score=0.80,
        silence_flag=True,
        matched_complaints=["C-REAL-1", "C-HALLUCINATED-99"],
        evidence_summary="Streetlight exhibits indications of probable failure.",
        recommended_action="escalate",
    )
    retrieved_signals = [
        {"complaint_id": "C-REAL-1"},
        {"complaint_id": "C-OTHER-2"},
    ]

    valid, invalid = validate_evidence_ids(report, retrieved_signals)
    assert valid is False
    assert "C-HALLUCINATED-99" in invalid

    # apply_guardrails cleans hallucinated IDs
    guarded = apply_guardrails(report, retrieved_signals)
    assert "C-HALLUCINATED-99" not in guarded.matched_complaints
    assert "C-REAL-1" in guarded.matched_complaints
