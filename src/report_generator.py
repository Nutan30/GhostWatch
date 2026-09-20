"""
GhostWatch Flag Report Generator
================================
Produces structured FlagReports with strictly hedged, evidence-backed summaries.
- In Demo Mode: template-based synthesis guaranteed to follow hedging rules.
- In IBM Mode: calls IBM Granite Instruct model via watsonx.ai.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.config import (
    DEMO_MODE,
    ESCALATION_THRESHOLD,
    IBM_CREDENTIALS_AVAILABLE,
    IBM_LLM_MODEL,
    WATSONX_API_KEY,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
)
from src.models import Asset, CrossRefMatch, FlagReport, SilenceResult
from src.utils import ASSET_TYPE_DISPLAY, logger


def _calculate_confidence_score(
    silence_result: SilenceResult,
    matched_complaints: list[CrossRefMatch],
) -> float:
    """
    Compute unified confidence score (0.0 to 1.0).
    Combines silence evidence with citizen grievance matches.
    """
    has_silence = silence_result.silence_flag
    silence_s = silence_result.silence_score
    has_complaints = len(matched_complaints) > 0

    if has_silence and has_complaints:
        best_sim = max(m.similarity for m in matched_complaints)
        # Multi-complaint reinforcement boost (up to +0.05)
        count_boost = min(0.05, 0.02 * (len(matched_complaints) - 1))
        score = 0.40 * silence_s + 0.55 * best_sim + count_boost
        return min(0.98, max(0.1, round(score, 2)))

    elif has_silence and not has_complaints:
        # Silence alone (fairness: still flagged, but capped below auto-escalation)
        score = 0.35 + 0.35 * silence_s
        return round(min(0.70, score), 2)

    elif not has_silence and has_complaints:
        best_sim = max(m.similarity for m in matched_complaints)
        score = 0.45 * best_sim
        return round(min(0.65, score), 2)

    else:
        return 0.05


def _build_evidence_summary_template(
    asset: Asset,
    silence_result: SilenceResult,
    matched_complaints: list[CrossRefMatch],
    warranty_active: bool,
) -> str:
    """Generate deterministic, strictly hedged evidence summary for Demo Mode."""
    display_type = ASSET_TYPE_DISPLAY.get(asset.asset_type, asset.asset_type)
    lines: list[str] = []

    # Opening with hedged assertion
    lines.append(
        f"{display_type} ({asset.asset_id}) at {asset.location_name} exhibits indications of probable operational failure."
    )

    # Maintenance silence signal
    if silence_result.silence_flag:
        if asset.last_maintenance_log_date:
            lines.append(
                f"No maintenance recorded for {silence_result.months_since_last_activity:.1f} months "
                f"(last logged {asset.last_maintenance_log_date}), exceeding expected service interval by "
                f"{silence_result.months_overdue:.1f} months."
            )
        else:
            lines.append(
                f"Zero maintenance records logged since installation on {asset.install_date} "
                f"({silence_result.months_since_last_activity:.1f} months ago), "
                f"exceeding expected service interval by {silence_result.months_overdue:.1f} months."
            )
    else:
        lines.append(
            f"Routine maintenance is current (last active {silence_result.months_since_last_activity:.1f} months ago)."
        )

    # Corroborating grievance signals
    if matched_complaints:
        c_ids = [m.complaint_id for m in matched_complaints]
        sim_strs = [f"{m.complaint_id} ({int(m.similarity * 100)}% match)" for m in matched_complaints[:3]]
        lines.append(
            f"Corroborated by {len(matched_complaints)} citizen grievance signal(s): {', '.join(sim_strs)}."
        )
    else:
        lines.append("No active citizen complaints matched this specific location.")

    # Warranty and contractor status
    if warranty_active:
        lines.append(
            f"Asset warranty is active through {asset.warranty_end_date} under contractor {asset.contractor_name}."
        )
    else:
        lines.append(
            f"Asset warranty expired on {asset.warranty_end_date}. Contractor on record: {asset.contractor_name}."
        )

    return " ".join(lines)


def _generate_with_granite(
    asset: Asset,
    silence_result: SilenceResult,
    matched_complaints: list[CrossRefMatch],
    warranty_active: bool,
) -> Optional[str]:
    """Invoke IBM Granite instruct via watsonx.ai if configured."""
    if not IBM_CREDENTIALS_AVAILABLE:
        return None

    try:
        from ibm_watsonx_ai.foundation_models import Model
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

        parameters = {
            GenParams.MAX_NEW_TOKENS: 250,
            GenParams.TEMPERATURE: 0.2,
            GenParams.TOP_P: 0.9,
        }

        model = Model(
            model_id=IBM_LLM_MODEL,
            params=parameters,
            credentials={"apikey": WATSONX_API_KEY, "url": WATSONX_URL},
            project_id=WATSONX_PROJECT_ID,
        )

        display_type = ASSET_TYPE_DISPLAY.get(asset.asset_type, asset.asset_type)
        c_details = "; ".join(
            [f"ID {m.complaint_id}: '{m.complaint_text}' (sim: {m.similarity:.2f})" for m in matched_complaints]
        ) or "None"

        prompt = (
            f"You are the GhostWatch Municipal Infrastructure Analyst. "
            f"Write a concise, 2-3 sentence evidence summary for this public asset.\n"
            f"CRITICAL CONSTRAINT: Never assert that the asset is definitely broken or confirmed non-functional. "
            f"You MUST use hedged phrasing such as 'likely non-functional', 'probable operational failure', "
            f"or 'exhibits indications of failure'. Cite the exact asset ID and grievance IDs.\n\n"
            f"Asset Details:\n"
            f"- Asset ID: {asset.asset_id}\n"
            f"- Type: {display_type}\n"
            f"- Location: {asset.location_name}\n"
            f"- Silence Overdue: {silence_result.months_overdue} months\n"
            f"- Matched Citizen Grievances: {c_details}\n"
            f"- Warranty Active: {warranty_active} (Expires {asset.warranty_end_date})\n"
            f"- Contractor: {asset.contractor_name}\n\n"
            f"Summary:"
        )

        response = model.generate_text(prompt=prompt)
        if response and len(response.strip()) > 20:
            return response.strip()
    except Exception as exc:
        logger.warning("IBM Granite LLM invocation failed (falling back to template): %s", exc)

    return None


def generate_flag_report(
    asset: Asset,
    silence_result: SilenceResult,
    matched_complaints: list[CrossRefMatch],
    reference_date: date | None = None,
) -> FlagReport:
    """
    Generate structured FlagReport evaluating whether an asset should be flagged.
    """
    today = reference_date or date.today()
    warranty_active = today <= asset.warranty_end_date

    confidence = _calculate_confidence_score(silence_result, matched_complaints)

    # Determine recommended action
    if confidence >= ESCALATION_THRESHOLD:
        recommended_action = "escalate"
    elif confidence >= 0.40 or silence_result.silence_flag:
        recommended_action = "inspect"
    else:
        recommended_action = "monitor"

    # Generate summary: try IBM Granite if available, else template
    summary = None
    if not DEMO_MODE:
        summary = _generate_with_granite(asset, silence_result, matched_complaints, warranty_active)

    if not summary:
        summary = _build_evidence_summary_template(asset, silence_result, matched_complaints, warranty_active)

    report = FlagReport(
        asset_id=asset.asset_id,
        confidence_score=confidence,
        silence_flag=silence_result.silence_flag,
        matched_complaints=[m.complaint_id for m in matched_complaints],
        evidence_summary=summary,
        recommended_action=recommended_action,
        output_language_hedge_check=False,  # Will be verified by guardrails
        silence_details={
            "months_overdue": silence_result.months_overdue,
            "silence_score": silence_result.silence_score,
            "months_since_last_activity": silence_result.months_since_last_activity,
            "reference_date": silence_result.reference_date,
        },
        cross_ref_details=[
            {
                "complaint_id": m.complaint_id,
                "similarity": m.similarity,
                "text": m.complaint_text,
                "date_reported": str(m.date_reported) if m.date_reported else None,
                "semantic_similarity": m.semantic_similarity,
                "location_match": m.location_match,
                "type_match": m.type_match,
            }
            for m in matched_complaints
        ],
        warranty_active=warranty_active,
        asset_type=asset.asset_type,
        location_name=asset.location_name,
    )

    logger.info(
        "Report   %-14s: conf=%.2f action=%-8s matched_c=%d",
        asset.asset_id,
        report.confidence_score,
        report.recommended_action,
        len(report.matched_complaints),
    )
    return report
