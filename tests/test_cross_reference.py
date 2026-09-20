"""
Unit tests for GhostWatch Cross-Reference Classifier (§5.4 of Tech-Req).
Verifies semantic and metadata matching, threshold filtering, and ranking.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.cross_reference import cross_reference_classifier
from src.models import Asset


@pytest.fixture
def sample_asset():
    return Asset(
        asset_id="SL-2023-114",
        asset_type="solar_streetlight",
        location_name="Ward 7, Market Road",
        latitude=19.0760,
        longitude=72.8777,
        install_date=date(2023, 2, 15),
        expected_service_interval_months=6,
        warranty_end_date=date(2026, 2, 15),
        contractor_name="ABC Solar Pvt Ltd",
        last_maintenance_log_date=None,
    )


def test_cross_reference_matching_candidate(sample_asset):
    """Signals matching both location (Ward 7) and domain (streetlight/dark) must pass threshold."""
    retrieved_signals = [
        {
            "complaint_id": "C-4471",
            "similarity": 0.85,
            "document": "Streetlight near market has been dark for weeks. Very unsafe.",
            "metadata": {
                "complaint_id": "C-4471",
                "approx_location": "Ward 7",
                "category_tag": "lighting",
                "complaint_text": "Streetlight near market has been dark for weeks. Very unsafe.",
                "date_reported": "2026-08-01",
            },
        },
        {
            "complaint_id": "C-9999",
            "similarity": 0.20,
            "document": "Pothole on highway near Ward 2.",
            "metadata": {
                "complaint_id": "C-9999",
                "approx_location": "Ward 2",
                "category_tag": "roads",
                "complaint_text": "Pothole on highway near Ward 2.",
                "date_reported": "2026-08-10",
            },
        },
    ]

    matches = cross_reference_classifier(sample_asset, retrieved_signals, threshold=0.70)

    assert len(matches) == 1
    assert matches[0].complaint_id == "C-4471"
    assert matches[0].similarity >= 0.70
    assert matches[0].location_match >= 0.8
    assert matches[0].type_match >= 0.8


def test_cross_reference_threshold_filtering(sample_asset):
    """Low-similarity noise must be excluded below threshold."""
    noise_signals = [
        {
            "complaint_id": "C-NOISE-1",
            "similarity": 0.35,
            "document": "Garbage dump overflowing in Ward 12.",
            "metadata": {
                "complaint_id": "C-NOISE-1",
                "approx_location": "Ward 12",
                "category_tag": "sanitation",
                "complaint_text": "Garbage dump overflowing in Ward 12.",
                "date_reported": "2026-08-05",
            },
        }
    ]

    matches = cross_reference_classifier(sample_asset, noise_signals, threshold=0.70)
    assert len(matches) == 0


def test_cross_reference_ranking_order(sample_asset):
    """Higher-matching complaints must appear first."""
    signals = [
        {
            "complaint_id": "C-MID",
            "similarity": 0.72,
            "document": "Dim light somewhere in Ward 7.",
            "metadata": {
                "complaint_id": "C-MID",
                "approx_location": "Ward 7",
                "category_tag": "lighting",
                "complaint_text": "Dim light somewhere in Ward 7.",
                "date_reported": "2026-08-02",
            },
        },
        {
            "complaint_id": "C-HIGH",
            "similarity": 0.95,
            "document": "Solar streetlight at Market Road Ward 7 completely dark.",
            "metadata": {
                "complaint_id": "C-HIGH",
                "approx_location": "Ward 7, Market Road",
                "category_tag": "lighting",
                "complaint_text": "Solar streetlight at Market Road Ward 7 completely dark.",
                "date_reported": "2026-08-03",
            },
        },
    ]

    matches = cross_reference_classifier(sample_asset, signals, threshold=0.70)
    assert len(matches) == 2
    assert matches[0].complaint_id == "C-HIGH"
    assert matches[1].complaint_id == "C-MID"
    assert matches[0].similarity > matches[1].similarity
