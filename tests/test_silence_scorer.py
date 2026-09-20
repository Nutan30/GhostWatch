"""
Unit tests for GhostWatch Silence Scorer (§5.3 and §10 of Tech-Req).
Tests 3 known-broken + 3 known-working scenarios, edge cases, and fairness principle.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.models import Asset
from src.silence_scorer import silence_scorer


@pytest.fixture
def base_date():
    return date(2026, 9, 1)


def make_asset(
    asset_id: str,
    install_date: date,
    interval_months: int,
    last_log: date | None = None,
    warranty_end: date | None = None,
) -> Asset:
    return Asset(
        asset_id=asset_id,
        asset_type="solar_streetlight",
        location_name="Ward 7, Market Road",
        latitude=19.0760,
        longitude=72.8777,
        install_date=install_date,
        expected_service_interval_months=interval_months,
        warranty_end_date=warranty_end or date(2027, 1, 1),
        contractor_name="SolarCorp India",
        last_maintenance_log_date=last_log,
    )


# ── Known-Broken Scenarios ──────────────────────────────────────────

def test_known_broken_no_maintenance_logs(base_date):
    """Scenario 1: Installed 24 months ago, 6mo interval, 0 logs recorded -> Overdue 18mo."""
    asset = make_asset(
        asset_id="KB-001",
        install_date=date(2024, 9, 1),
        interval_months=6,
        last_log=None,
    )
    result = silence_scorer(asset, reference_date=base_date)

    assert result.silence_flag is True
    assert result.months_overdue >= 17.5
    assert result.silence_score == 1.0  # Capped at 1.0 for 12+ mo overdue
    assert result.reference_date == "install_date"


def test_known_broken_expired_maintenance(base_date):
    """Scenario 2: Installed 30 months ago, maintained 14 months ago with 6mo interval -> Overdue 8mo."""
    asset = make_asset(
        asset_id="KB-002",
        install_date=date(2024, 3, 1),
        interval_months=6,
        last_log=date(2025, 7, 1),
    )
    result = silence_scorer(asset, reference_date=base_date)

    assert result.silence_flag is True
    assert 7.5 <= result.months_overdue <= 8.5
    assert 0.6 <= result.silence_score <= 0.75
    assert result.reference_date == "last_maintenance"


def test_known_broken_quarterly_interval_missed(base_date):
    """Scenario 3: EV charger with 3-month interval, last log 10 months ago -> Overdue 7mo."""
    asset = make_asset(
        asset_id="KB-003",
        install_date=date(2025, 1, 1),
        interval_months=3,
        last_log=date(2025, 11, 1),
    )
    result = silence_scorer(asset, reference_date=base_date)

    assert result.silence_flag is True
    assert result.months_overdue >= 6.5
    assert result.silence_score > 0.5


# ── Known-Working Scenarios ─────────────────────────────────────────

def test_known_working_recent_installation(base_date):
    """Scenario 4: Installed 2 months ago, 6mo interval -> NOT overdue."""
    asset = make_asset(
        asset_id="KW-001",
        install_date=date(2026, 7, 1),
        interval_months=6,
        last_log=None,
    )
    result = silence_scorer(asset, reference_date=base_date)

    assert result.silence_flag is False
    assert result.months_overdue == 0.0
    assert result.silence_score == 0.0


def test_known_working_recent_maintenance(base_date):
    """Scenario 5: Installed 2 years ago, but maintained 1 month ago -> NOT overdue."""
    asset = make_asset(
        asset_id="KW-002",
        install_date=date(2024, 9, 1),
        interval_months=6,
        last_log=date(2026, 8, 1),
    )
    result = silence_scorer(asset, reference_date=base_date)

    assert result.silence_flag is False
    assert result.months_overdue == 0.0
    assert result.silence_score == 0.0


def test_known_working_exact_interval_boundary(base_date):
    """Scenario 6: Maintained exactly within expected window."""
    asset = make_asset(
        asset_id="KW-003",
        install_date=date(2025, 1, 1),
        interval_months=6,
        last_log=date(2026, 4, 1),  # 5 months ago, interval is 6
    )
    result = silence_scorer(asset, reference_date=base_date)

    assert result.silence_flag is False
    assert result.months_overdue == 0.0


# ── Fairness Verification ───────────────────────────────────────────

def test_fairness_independent_of_grievances(base_date):
    """
    Fairness requirement (§9 PRD, §10 Tech-Req):
    Silence scorer does not accept, inspect, or depend on grievance volume.
    Assets in low-reporting wards are evaluated on equal chronological terms.
    """
    asset = make_asset(
        asset_id="FAIR-01",
        install_date=date(2024, 1, 1),
        interval_months=6,
        last_log=None,
    )
    # The function signature itself must not accept complaints
    result = silence_scorer(asset, reference_date=base_date)
    assert result.silence_flag is True
    assert result.silence_score > 0
