"""
GhostWatch Data Models
=======================
Dataclasses for assets, grievances, results, reports, and escalation notices.
Matches schemas from the Technical Requirements Document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Asset:
    """Public sustainability asset record (§4.1 of tech-req)."""
    asset_id: str
    asset_type: str                        # solar_streetlight | water_atm | ev_charger | rainwater_unit
    location_name: str                     # e.g. "Ward 7, Market Road"
    latitude: float
    longitude: float
    install_date: date
    expected_service_interval_months: int  # e.g. 6
    warranty_end_date: date
    contractor_name: str
    last_maintenance_log_date: Optional[date] = None


@dataclass
class Grievance:
    """Citizen grievance/complaint record (§4.2 of tech-req)."""
    complaint_id: str
    complaint_text: str
    approx_location: str
    date_reported: date
    category_tag: Optional[str] = None


@dataclass
class SilenceResult:
    """Output of the silence scorer."""
    silence_flag: bool
    months_overdue: float
    silence_score: float                   # 0-1 normalised
    months_since_last_activity: float
    reference_date: str                    # "last_maintenance" | "install_date"


@dataclass
class CrossRefMatch:
    """A single complaint↔asset match from the cross-reference classifier."""
    complaint_id: str
    similarity: float
    complaint_text: str
    date_reported: Optional[date] = None
    semantic_similarity: float = 0.0
    location_match: float = 0.0
    type_match: float = 0.0


@dataclass
class FlagReport:
    """Structured flag report (§4.3 of tech-req)."""
    asset_id: str
    confidence_score: float
    silence_flag: bool
    matched_complaints: list[str] = field(default_factory=list)
    evidence_summary: str = ""
    recommended_action: str = "monitor"    # monitor | inspect | escalate
    output_language_hedge_check: bool = False
    silence_details: Optional[dict] = None
    cross_ref_details: Optional[list] = None
    warranty_active: bool = False
    asset_type: str = ""
    location_name: str = ""


@dataclass
class EscalationNotice:
    """Draft inspection recommendation notice."""
    asset_id: str
    location: str
    asset_type: str
    evidence_summary: str
    silence_info: str
    warranty_status: str
    suggested_inspection: str
    responsible_party: str
    confidence_score: float
    notice_text: str
