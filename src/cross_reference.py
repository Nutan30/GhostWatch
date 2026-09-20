"""
GhostWatch Cross-Reference Classifier
=====================================
Matches retrieved grievances to a specific asset record using semantic
similarity, ward/location matching, and asset-type keyword alignment.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.config import CROSS_REF_THRESHOLD
from src.models import Asset, CrossRefMatch
from src.utils import ASSET_TYPE_KEYWORDS, logger


def _compute_location_match(asset_loc: str, comp_loc: str, comp_text: str) -> float:
    """Check how well the complaint location matches the asset location."""
    asset_loc_lower = asset_loc.lower()
    comp_loc_lower = comp_loc.lower()
    comp_text_lower = comp_text.lower()

    import re
    # Extract ward if present (e.g., "ward 7")
    words = [w.strip() for w in asset_loc_lower.split(",")]
    ward = next((w for w in words if "ward" in w), "")

    ward_matched = False
    if ward:
        ward_pattern = rf"\b{re.escape(ward)}\b"
        if re.search(ward_pattern, comp_loc_lower) or re.search(ward_pattern, comp_text_lower):
            ward_matched = True

    if ward_matched:
        # Full or partial street match in addition to ward?
        other_tokens = [w for w in words if w != ward and len(w) > 2]
        if any(tok in comp_text_lower or tok in comp_loc_lower for tok in other_tokens):
            return 1.0
        return 0.85

    # Check if exact location name is in text
    if asset_loc_lower in comp_text_lower or asset_loc_lower in comp_loc_lower:
        return 1.0

    # Token overlap
    tokens = [w for w in words if len(w) > 2]
    matched = sum(1 for tok in tokens if tok in comp_text_lower or tok in comp_loc_lower)
    if matched > 0:
        return min(1.0, 0.4 + 0.3 * matched)

    return 0.2


def _compute_type_match(asset_type: str, comp_text: str, category_tag: Optional[str] = None) -> float:
    """Check if complaint text contains domain keywords matching the asset type."""
    keywords = ASSET_TYPE_KEYWORDS.get(asset_type, [])
    comp_text_lower = comp_text.lower()

    # Check category tag first
    if category_tag:
        cat_lower = category_tag.lower()
        if any(kw in cat_lower for kw in keywords):
            return 1.0

    # Count keyword matches
    hits = sum(1 for kw in keywords if kw in comp_text_lower)
    if hits >= 2:
        return 1.0
    elif hits == 1:
        return 0.8
    return 0.2


def cross_reference_classifier(
    asset: Asset,
    retrieved_signals: list[dict],
    threshold: float = CROSS_REF_THRESHOLD,
) -> list[CrossRefMatch]:
    """
    Cross-reference retrieved grievance signals against a specific asset.

    Parameters
    ----------
    asset : Asset
        The asset record under evaluation.
    retrieved_signals : list[dict]
        Output list from `RAGStore.retrieve_signals()`.
    threshold : float
        Minimum composite similarity to qualify as a match (default 0.70).

    Returns
    -------
    list[CrossRefMatch]
        Matched complaints sorted by composite similarity descending.
    """
    matches: list[CrossRefMatch] = []

    for sig in retrieved_signals:
        complaint_id = sig.get("complaint_id", "")
        semantic_sim = float(sig.get("similarity", 0.0))
        meta = sig.get("metadata", {})

        comp_text = meta.get("complaint_text") or sig.get("document", "")
        approx_loc = meta.get("approx_location", "")
        cat_tag = meta.get("category_tag", "")
        raw_date = meta.get("date_reported")

        date_reported: Optional[date] = None
        if raw_date:
            try:
                date_reported = date.fromisoformat(str(raw_date))
            except Exception:
                pass

        # Compute sub-scores
        loc_score = _compute_location_match(asset.location_name, approx_loc, comp_text)
        type_score = _compute_type_match(asset.asset_type, comp_text, cat_tag)

        # Composite score weighting: 50% semantic, 30% location, 20% type match
        composite_score = round(
            0.50 * semantic_sim + 0.30 * loc_score + 0.20 * type_score,
            4,
        )

        if composite_score >= threshold:
            matches.append(
                CrossRefMatch(
                    complaint_id=complaint_id,
                    similarity=composite_score,
                    complaint_text=comp_text,
                    date_reported=date_reported,
                    semantic_similarity=round(semantic_sim, 4),
                    location_match=round(loc_score, 4),
                    type_match=round(type_score, 4),
                )
            )

    # Sort descending by composite similarity
    matches.sort(key=lambda m: m.similarity, reverse=True)

    logger.info(
        "CrossRef %-14s: %d matches above threshold %.2f (out of %d candidates)",
        asset.asset_id,
        len(matches),
        threshold,
        len(retrieved_signals),
    )
    return matches
