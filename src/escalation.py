"""
GhostWatch Escalation Module
=============================
Generates formal inspection recommendation notices for high-confidence flags (>= 0.75).
Cross-references warranty status to assign responsibility to contractor or municipality.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.config import ESCALATION_THRESHOLD
from src.models import Asset, EscalationNotice, FlagReport
from src.utils import ASSET_TYPE_DISPLAY, logger

# Suggested inspection checklists per asset type
INSPECTION_CHECKLISTS: dict[str, str] = {
    "solar_streetlight": (
        "1. Inspect solar PV panel for physical damage or heavy particulate fouling.\n"
        "2. Test LiFePO4 battery terminal voltage and charge controller cycle history.\n"
        "3. Audit dusk-to-dawn dusk sensor and LED luminaire driver output."
    ),
    "water_atm": (
        "1. Test RO/UV filtration membrane pressure differential and TDS levels.\n"
        "2. Inspect solenoid dispensing valves and coin/RFID/smartcard reader.\n"
        "3. Verify flow sensor telemetry and chilled water compressor operation."
    ),
    "ev_charger": (
        "1. Check Type-2 / CCS2 gun contact pins for thermal discoloration or wear.\n"
        "2. Perform Residual Current Device (RCD) trip and ground continuity test.\n"
        "3. Verify OCPP gateway 4G connection and payment gateway status."
    ),
    "rainwater_unit": (
        "1. Check roof catchment inlet filter and first-flush diverter mechanism.\n"
        "2. Inspect secondary wire-mesh debris screen for leaf or silt blockage.\n"
        "3. Audit storage tank overflow drain and sub-surface recharge pit."
    ),
}


def escalate(
    report: FlagReport,
    asset: Asset,
    threshold: float = ESCALATION_THRESHOLD,
    reference_date: date | None = None,
) -> Optional[EscalationNotice]:
    """
    Generate an official Escalation Notice if report confidence meets or exceeds threshold.

    Parameters
    ----------
    report : FlagReport
        Evaluated flag report.
    asset : Asset
        Corresponding asset registry record.
    threshold : float
        Minimum confidence required (default 0.75).
    reference_date : date, optional
        Current date for warranty validation.

    Returns
    -------
    Optional[EscalationNotice]
        Populated notice if confidence >= threshold, else None.
    """
    if report.confidence_score < threshold:
        logger.info(
            "Escalation SKIPPED for %s (confidence %.2f < %.2f)",
            report.asset_id,
            report.confidence_score,
            threshold,
        )
        return None

    today = reference_date or date.today()
    display_type = ASSET_TYPE_DISPLAY.get(asset.asset_type, asset.asset_type)
    warranty_active = today <= asset.warranty_end_date

    # Determine responsible party and warranty status text
    if warranty_active:
        responsible_party = f"Contractor: {asset.contractor_name} (Under AMC/Warranty)"
        warranty_status = (
            f"Active warranty until {asset.warranty_end_date} (Contractor {asset.contractor_name} liable for repair)"
        )
        liability_note = (
            f"Per municipal procurement agreement, contractor {asset.contractor_name} is obligated "
            f"to service this infrastructure under active warranty terms at zero additional cost."
        )
    else:
        responsible_party = "Municipal Maintenance & Public Works Department"
        warranty_status = (
            f"Warranty expired on {asset.warranty_end_date} (Municipal direct maintenance liability)"
        )
        liability_note = (
            "Asset warranty has lapsed. Inspection and repair requisition must be routed through the "
            "Ward Junior Engineer and municipal maintenance schedule."
        )

    checklist = INSPECTION_CHECKLISTS.get(
        asset.asset_type,
        "1. Conduct comprehensive on-site physical and electrical audit.",
    )

    silence_info = (
        f"Maintenance overdue by {report.silence_details.get('months_overdue', 0)} months "
        f"(silence score: {report.silence_details.get('silence_score', 0)}). "
        f"Last activity recorded: {asset.last_maintenance_log_date or 'None since installation'}."
    )

    # Formal draft notice body
    notice_text = (
        f"================================================================================\n"
        f"MUNICIPAL INFRASTRUCTURE AUDIT NOTICE — ACTION REQUIRED\n"
        f"GHOSTWATCH SILENT FAILURE DETECTION SYSTEM\n"
        f"================================================================================\n\n"
        f"DATE:             {today.isoformat()}\n"
        f"ASSET ID:         {asset.asset_id}\n"
        f"ASSET TYPE:       {display_type}\n"
        f"LOCATION:         {asset.location_name} (Lat: {asset.latitude}, Lon: {asset.longitude})\n"
        f"CONFIDENCE:       {int(report.confidence_score * 100)}% (High Priority Flag)\n\n"
        f"1. RESPONSIBLE ENTITY:\n"
        f"   {responsible_party}\n\n"
        f"2. WARRANTY & LIABILITY STATUS:\n"
        f"   {warranty_status}\n"
        f"   {liability_note}\n\n"
        f"3. EVIDENCE SUMMARY:\n"
        f"   {report.evidence_summary}\n\n"
        f"4. MAINTENANCE SILENCE TELEMETRY:\n"
        f"   {silence_info}\n\n"
        f"5. CORROBORATING GRIEVANCES:\n"
        f"   Cited Complaints: {', '.join(report.matched_complaints) if report.matched_complaints else 'None'}\n\n"
        f"6. MANDATED FIELD AUDIT PROCEDURES:\n"
        f"{checklist}\n\n"
        f"================================================================================\n"
        f"NOTE: Generated by GhostWatch AI under Responsible AI Guardrails.\n"
        f"This notice represents an evidence-backed inspection dispatch recommendation.\n"
        f"================================================================================"
    )

    notice = EscalationNotice(
        asset_id=asset.asset_id,
        location=asset.location_name,
        asset_type=asset.asset_type,
        evidence_summary=report.evidence_summary,
        silence_info=silence_info,
        warranty_status=warranty_status,
        suggested_inspection=checklist,
        responsible_party=responsible_party,
        confidence_score=report.confidence_score,
        notice_text=notice_text,
    )

    logger.info("Escalation CREATED for %s (party: %s)", asset.asset_id, responsible_party)
    return notice
