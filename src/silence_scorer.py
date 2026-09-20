"""
GhostWatch Silence Scorer
==========================
Flags assets whose maintenance is overdue based purely on time gaps —
independent of complaint volume (fairness requirement, §9 of PRD).
"""

from __future__ import annotations

from datetime import date

from src.models import Asset, SilenceResult
from src.utils import logger, months_between


def silence_scorer(asset: Asset, reference_date: date | None = None) -> SilenceResult:
    """
    Calculate silence score for a single asset.

    Returns
    -------
    SilenceResult
        silence_flag  : True when overdue
        months_overdue: how many months past the expected interval
        silence_score : 0-1 normalised (12+ months overdue → 1.0)
    """
    today = reference_date or date.today()

    # Pick the most-recent activity date
    if asset.last_maintenance_log_date:
        last_activity = asset.last_maintenance_log_date
        ref_type = "last_maintenance"
    else:
        last_activity = asset.install_date
        ref_type = "install_date"

    months_since = months_between(last_activity, today)
    months_overdue = months_since - asset.expected_service_interval_months

    silence_flag = months_overdue > 0

    # Normalise: 12 months overdue → 1.0 (ceiling)
    silence_score = min(1.0, max(0.0, months_overdue / 12.0)) if silence_flag else 0.0

    result = SilenceResult(
        silence_flag=silence_flag,
        months_overdue=round(max(0.0, months_overdue), 1),
        silence_score=round(silence_score, 3),
        months_since_last_activity=round(months_since, 1),
        reference_date=ref_type,
    )

    logger.info(
        "Silence  %-14s  flag=%s  overdue=%.1f mo  score=%.3f",
        asset.asset_id, result.silence_flag, result.months_overdue, result.silence_score,
    )
    return result
