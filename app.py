"""
GhostWatch — Silent Failure Detection in Public Sustainability Infrastructure
=============================================================================
Streamlit Dashboard for 1M1B AI for Sustainability Virtual Internship
IBM SkillsBuild & AICTE
"""

from __future__ import annotations

import json
from datetime import date
from typing import Optional

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

from src.config import (
    CROSS_REF_THRESHOLD,
    DEMO_MODE,
    ESCALATION_THRESHOLD,
    IBM_CREDENTIALS_AVAILABLE,
)
from src.data_loader import load_asset_registry, load_grievances
from src.orchestrator import PipelineResult, run_pipeline
from src.utils import ASSET_TYPE_DISPLAY

# ── Streamlit Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="GhostWatch — Silent Failure Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Modern, Executive Aesthetics ──────────────────────
st.markdown(
    """
    <style>
    /* Global styling */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Container */
    .gw-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    
    .gw-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    
    .gw-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 12px;
    }

    /* Badges */
    .gw-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-sdg {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .badge-ibm {
        background-color: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    .badge-mode {
        background-color: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: left;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Section Boxes */
    .gw-box {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Status Pills */
    .status-healthy { color: #34d399; font-weight: 600; }
    .status-silence { color: #fbbf24; font-weight: 600; }
    .status-escalate { color: #f87171; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Pipeline Caching ─────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_pipeline_data() -> PipelineResult:
    """Run GhostWatch agent pipeline once and cache results in memory."""
    assets, _ = load_asset_registry()
    grievances = load_grievances()
    return run_pipeline(assets=assets, grievances=grievances, save_traces=True)


# ── Load Data ────────────────────────────────────────────────────────
with st.spinner("🤖 Initializing GhostWatch Agentic RAG Pipeline..."):
    result: PipelineResult = get_pipeline_data()

# ── Sidebar Controls ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ **GhostWatch Control Hub**")
    st.caption("AI-Powered Public Infrastructure Auditing")

    st.markdown("---")
    st.markdown("#### ⚙️ **System Architecture**")
    if IBM_CREDENTIALS_AVAILABLE:
        st.success("🟢 IBM watsonx & Granite Active")
    else:
        st.info("🟡 Demo / Resilient Local Mode")
    st.caption("• Agent: LangGraph State Pipeline\n• Vector Store: Cosine / Chroma\n• Guardrails: Granite Guardian / Regex")

    st.markdown("---")
    st.markdown("#### 🔍 **Audit Filters**")

    # Filter: Asset Type
    all_types = list({a.asset_type for a in result.assets})
    type_display_map = {t: ASSET_TYPE_DISPLAY.get(t, t) for t in all_types}
    selected_types = st.multiselect(
        "Asset Category",
        options=all_types,
        default=all_types,
        format_func=lambda x: type_display_map.get(x, x),
    )

    # Filter: Ward
    all_wards = sorted(list({a.location_name.split(",")[0].strip() for a in result.assets}))
    selected_wards = st.multiselect(
        "Municipal Ward",
        options=all_wards,
        default=all_wards,
    )

    # Filter: Status / Severity
    status_filter = st.selectbox(
        "Filter by Risk Profile",
        options=[
            "All Assets",
            "High Priority (Escalate)",
            "Silence Warning (Overdue Check)",
            "Active / Healthy",
        ],
        index=0,
    )

    # Filter: Confidence Slider
    min_confidence = st.slider(
        "Confidence Cutoff",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
    )

    st.markdown("---")
    if st.button("🔄 Force Re-run Agent Pipeline", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("1M1B AI for Sustainability Virtual Internship — IBM SkillsBuild & AICTE")


# ── Filter Assets ────────────────────────────────────────────────────
reports_by_id = {r.asset_id: r for r in result.reports}
filtered_assets = []

for a in result.assets:
    rep = reports_by_id.get(a.asset_id)
    if not rep:
        continue

    # Asset type filter
    if a.asset_type not in selected_types:
        continue

    # Ward filter
    ward = a.location_name.split(",")[0].strip()
    if ward not in selected_wards:
        continue

    # Confidence filter
    if rep.confidence_score < min_confidence:
        continue

    # Status filter
    if status_filter == "High Priority (Escalate)" and rep.recommended_action != "escalate":
        continue
    elif status_filter == "Silence Warning (Overdue Check)" and not (rep.silence_flag and len(rep.matched_complaints) == 0):
        continue
    elif status_filter == "Active / Healthy" and (rep.silence_flag or len(rep.matched_complaints) > 0):
        continue

    filtered_assets.append(a)


# ── Header Banner ────────────────────────────────────────────────────
st.markdown(
    """
    <div class="gw-header">
        <div class="gw-title">GhostWatch 🛡️</div>
        <div class="gw-subtitle">Agentic AI for Detecting Silent Failures in Public Sustainability Infrastructure</div>
        <div>
            <span class="gw-badge badge-sdg">UN SDG 11: Sustainable Cities</span>
            <span class="gw-badge badge-sdg">UN SDG 9: Infrastructure</span>
            <span class="gw-badge badge-ibm">IBM SkillsBuild & AICTE</span>
            <span class="gw-badge badge-mode">IBM Granite Ready</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Top KPI Metric Cards ─────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{result.summary['total_assets']}</div>
            <div class="metric-label">Registered Assets</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #fbbf24;">{result.summary['silence_flags']}</div>
            <div class="metric-label">Maintenance Overdue</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #38bdf8;">{result.summary['complaint_matches']}</div>
            <div class="metric-label">Citizen Complaints</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #f87171;">{result.summary['high_confidence_flags']}</div>
            <div class="metric-label">High-Priority Flags</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #34d399;">{result.summary['warranty_active_flags']}</div>
            <div class="metric-label">Active Warranties</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# ── Main Tabs ────────────────────────────────────────────────────────
tab_map, tab_table, tab_evidence, tab_escalation, tab_safety = st.tabs([
    "Overview & Map",
    "Asset Registry & Flags",
    "Evidence Trail & Agent Trace",
    "Escalation Notices",
    "Responsible AI & Architecture",
])


# ══════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW & MAP
# ══════════════════════════════════════════════════════════════════════
with tab_map:
    st.markdown("### 📍 **Geographic Risk Distribution**")
    st.caption(
        "Interactive geospatial intelligence map showing asset operating health. "
        "🟢 Healthy | 🟡 Maintenance Overdue (Silent Risk) | 🔴 Corroborated Failure (High Priority)"
    )

    if filtered_assets:
        # Compute center coordinates
        center_lat = sum(a.latitude for a in filtered_assets) / len(filtered_assets)
        center_lon = sum(a.longitude for a in filtered_assets) / len(filtered_assets)

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles="CartoDB dark_matter",
        )

        for asset in filtered_assets:
            rep = reports_by_id[asset.asset_id]
            display_type = ASSET_TYPE_DISPLAY.get(asset.asset_type, asset.asset_type)

            # Determine color & icon
            if rep.confidence_score >= ESCALATION_THRESHOLD or (rep.silence_flag and len(rep.matched_complaints) > 0):
                color = "red"
                icon = "exclamation-triangle"
                status_desc = "🔴 High-Priority Silent Failure"
            elif rep.silence_flag:
                color = "orange"
                icon = "clock-o"
                status_desc = "🟡 Maintenance Overdue (Silence Only)"
            else:
                color = "green"
                icon = "check-circle"
                status_desc = "🟢 Operational / Up to Date"

            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 180px;">
                <h4 style="margin: 0 0 6px 0; color: #1e293b;">{asset.asset_id}</h4>
                <b>Type:</b> {display_type}<br/>
                <b>Location:</b> {asset.location_name}<br/>
                <b>Status:</b> {status_desc}<br/>
                <b>Confidence:</b> {int(rep.confidence_score * 100)}%<br/>
                <b>Action:</b> {rep.recommended_action.upper()}<br/>
                <b>Warranty:</b> {'Active' if rep.warranty_active else 'Expired'}
            </div>
            """

            folium.Marker(
                location=[asset.latitude, asset.longitude],
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{asset.asset_id} — {display_type} ({int(rep.confidence_score * 100)}% risk)",
                icon=folium.Icon(color=color, icon=icon, prefix="fa"),
            ).add_to(m)

        folium_static(m, width=1100, height=520)
    else:
        st.info("No assets match the currently selected filter criteria.")

    st.markdown("---")
    # Quick Summary Breakdown by Type
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### **Risk Breakdown by Asset Category**")
        cat_stats = []
        for atype in all_types:
            type_assets = [a for a in result.assets if a.asset_type == atype]
            type_reps = [reports_by_id[a.asset_id] for a in type_assets]
            cat_stats.append({
                "Category": ASSET_TYPE_DISPLAY.get(atype, atype),
                "Total Registered": len(type_assets),
                "Maintenance Overdue": sum(1 for r in type_reps if r.silence_flag),
                "Escalated (>= 75%)": sum(1 for r in type_reps if r.confidence_score >= 0.75),
            })
        st.dataframe(pd.DataFrame(cat_stats), use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### **Ward-Level Risk Concentration**")
        ward_stats = []
        for ward in all_wards:
            w_assets = [a for a in result.assets if ward in a.location_name]
            w_reps = [reports_by_id[a.asset_id] for a in w_assets]
            if w_assets:
                ward_stats.append({
                    "Ward": ward,
                    "Assets": len(w_assets),
                    "Overdue": sum(1 for r in w_reps if r.silence_flag),
                    "Escalations": sum(1 for r in w_reps if r.confidence_score >= 0.75),
                })
        st.dataframe(pd.DataFrame(ward_stats), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 2: ASSET REGISTRY & FLAGS TABLE
# ══════════════════════════════════════════════════════════════════════
with tab_table:
    st.markdown("### 📋 **Asset Audit Registry**")
    st.caption(f"Displaying {len(filtered_assets)} of {len(result.assets)} assets based on current filters.")

    table_data = []
    for a in filtered_assets:
        rep = reports_by_id[a.asset_id]
        display_type = ASSET_TYPE_DISPLAY.get(a.asset_type, a.asset_type)

        if rep.recommended_action == "escalate":
            status_icon = "🚨 ESCALATE"
        elif rep.recommended_action == "inspect":
            status_icon = "⚠️ INSPECT"
        else:
            status_icon = "✅ MONITOR"

        table_data.append({
            "Action": status_icon,
            "Asset ID": a.asset_id,
            "Category": display_type,
            "Ward & Location": a.location_name,
            "Confidence": f"{int(rep.confidence_score * 100)}%",
            "Overdue (Months)": rep.silence_details.get("months_overdue", 0.0),
            "Grievances": len(rep.matched_complaints),
            "Warranty": "Active" if rep.warranty_active else "Expired",
            "Contractor": a.contractor_name,
            "Hedge Check": "PASSED" if rep.output_language_hedge_check else "PENDING",
        })

    df_display = pd.DataFrame(table_data)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Export CSV Button
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Filtered Audit Report (CSV)",
        data=csv,
        file_name=f"ghostwatch_audit_{date.today().isoformat()}.csv",
        mime="text/csv",
    )


# ══════════════════════════════════════════════════════════════════════
# TAB 3: DEEP EVIDENCE DRILL-DOWN & TRACE
# ══════════════════════════════════════════════════════════════════════
with tab_evidence:
    st.markdown("### 🔬 **Evidence Trail & Agent Audit Trail**")
    st.caption("Drill down into any individual asset to verify the exact signals and reasoning steps.")

    asset_options = {a.asset_id: f"{a.asset_id} — {ASSET_TYPE_DISPLAY.get(a.asset_type, a.asset_type)} ({a.location_name})" for a in filtered_assets}

    if asset_options:
        selected_id = st.selectbox(
            "Select an asset to audit:",
            options=list(asset_options.keys()),
            format_func=lambda x: asset_options[x],
        )

        selected_asset = next(a for a in result.assets if a.asset_id == selected_id)
        selected_rep = reports_by_id[selected_id]
        selected_trace = result.traces.get(selected_id, {})

        st.markdown("---")

        # 4 Quadrants
        col_meta, col_silence = st.columns(2)

        with col_meta:
            st.markdown("#### 📌 **1. Asset Specifications**")
            st.markdown(
                f"""
                <div class="gw-box">
                    <b>Asset ID:</b> <code>{selected_asset.asset_id}</code><br/>
                    <b>Asset Category:</b> {ASSET_TYPE_DISPLAY.get(selected_asset.asset_type, selected_asset.asset_type)}<br/>
                    <b>Location:</b> {selected_asset.location_name}<br/>
                    <b>Coordinates:</b> {selected_asset.latitude}, {selected_asset.longitude}<br/>
                    <b>Install Date:</b> {selected_asset.install_date}<br/>
                    <b>Contractor:</b> {selected_asset.contractor_name}<br/>
                    <b>Warranty Expiry:</b> {selected_asset.warranty_end_date} 
                    ({'<span style="color:#34d399;">Active</span>' if selected_rep.warranty_active else '<span style="color:#f87171;">Expired</span>'})
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_silence:
            st.markdown("#### ⏳ **2. Maintenance Silence Telemetry**")
            sil = selected_rep.silence_details or {}
            overdue_val = sil.get("months_overdue", 0.0)
            score_val = sil.get("silence_score", 0.0)
            st.markdown(
                f"""
                <div class="gw-box">
                    <b>Expected Service Check:</b> Every {selected_asset.expected_service_interval_months} months<br/>
                    <b>Last Recorded Activity:</b> {selected_asset.last_maintenance_log_date or 'None logged since installation'}<br/>
                    <b>Months Without Service:</b> {sil.get('months_since_last_activity', 0.0)} months<br/>
                    <b>Months Overdue:</b> <span style="color: {'#f87171' if overdue_val > 0 else '#34d399'}; font-weight:700;">{overdue_val} months</span><br/>
                    <b>Normalized Silence Score:</b> {score_val} / 1.0<br/>
                    <b>Silence Flag Raised:</b> {'🚨 TRUE' if selected_rep.silence_flag else '✅ FALSE'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        col_comp, col_report = st.columns(2)

        with col_comp:
            st.markdown("#### 🗣️ **3. Corroborating Citizen Grievances**")
            cross_details = selected_rep.cross_ref_details or []
            if cross_details:
                for c in cross_details:
                    sim_pct = int(c.get("similarity", 0.0) * 100)
                    st.markdown(
                        f"""
                        <div class="gw-box" style="margin-bottom: 8px;">
                            <div style="display:flex; justify-content:space-between;">
                                <b>Complaint ID:</b> <code>{c.get('complaint_id')}</code>
                                <span style="color:#38bdf8; font-weight:700;">{sim_pct}% Match</span>
                            </div>
                            <p style="margin: 6px 0; font-style: italic; color: #cbd5e1;">"{c.get('text')}"</p>
                            <small style="color: #94a3b8;">Reported: {c.get('date_reported') or 'N/A'} | Semantic: {c.get('semantic_similarity', 0)} | Location: {c.get('location_match', 0)} | Category: {c.get('type_match', 0)}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No citizen complaints matched this specific location or asset type.")

        with col_report:
            st.markdown("#### 📝 **4. Synthesized Evidence Summary**")
            st.markdown(
                f"""
                <div class="gw-box">
                    <p style="font-size: 0.95rem; line-height: 1.5; color: #e2e8f0;">{selected_rep.evidence_summary}</p>
                    <hr style="border-color: rgba(148, 163, 184, 0.2);"/>
                    <b>Overall Confidence:</b> <span style="font-size: 1.1rem; color: #38bdf8; font-weight:700;">{int(selected_rep.confidence_score * 100)}%</span><br/>
                    <b>Recommended Action:</b> <span style="font-weight:700;">{selected_rep.recommended_action.upper()}</span><br/>
                    <b>Hedged Language Screen:</b> {'✅ PASSED (No unhedged failure assertions)' if selected_rep.output_language_hedge_check else '❌ FAILED'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Full Agent Reasoning Step Trace
        st.markdown("---")
        st.markdown("#### 🧠 **Step-by-Step Agentic Reasoning Trace**")
        st.caption("Complete, transparent execution trace from the LangGraph agent orchestrator.")

        if selected_trace and "steps" in selected_trace:
            for s in selected_trace["steps"]:
                with st.expander(f"Step {s['step']}: {s['name']} ({s.get('duration_ms', 0)} ms)"):
                    st.write(s.get("description", ""))
                    st.json(s)
        else:
            st.caption("No trace logged for this asset.")

    else:
        st.info("No assets match the filter.")


# ══════════════════════════════════════════════════════════════════════
# TAB 4: ESCALATION NOTICES
# ══════════════════════════════════════════════════════════════════════
with tab_escalation:
    st.markdown("### 🚨 **High-Priority Escalation Notices**")
    st.caption(
        "Formal inspection recommendation notices generated automatically by GhostWatch "
        f"for assets with confidence ≥ {int(ESCALATION_THRESHOLD * 100)}%."
    )

    if result.escalations:
        st.success(f"Total of {len(result.escalations)} assets flagged for immediate municipal inspection dispatch.")

        for idx, esc in enumerate(result.escalations):
            rep = reports_by_id[esc.asset_id]
            display_type = ASSET_TYPE_DISPLAY.get(esc.asset_type, esc.asset_type)

            with st.expander(f"📌 {esc.asset_id} — {display_type} ({esc.location}) — Confidence: {int(esc.confidence_score * 100)}%"):
                c_party, c_status = st.columns(2)
                with c_party:
                    st.markdown(f"**Responsible Entity:**\n`{esc.responsible_party}`")
                with c_status:
                    st.markdown(f"**Liability & Warranty:**\n`{esc.warranty_status}`")

                st.markdown("**Evidence Trail:**")
                st.info(esc.evidence_summary)

                st.markdown("**Mandated Field Inspection Procedures:**")
                st.code(esc.suggested_inspection, language="markdown")

                st.markdown("**Complete Formatted Notice Document:**")
                st.text_area(
                    f"Notice Body #{idx}",
                    value=esc.notice_text,
                    height=240,
                    key=f"notice_{esc.asset_id}",
                )

                st.download_button(
                    label=f"📥 Download Notice for {esc.asset_id}",
                    data=esc.notice_text,
                    file_name=f"ESCALATION_NOTICE_{esc.asset_id}.txt",
                    mime="text/plain",
                    key=f"btn_dl_{esc.asset_id}",
                )
    else:
        st.info("No assets currently exceed the escalation confidence threshold.")


# ══════════════════════════════════════════════════════════════════════
# TAB 5: RESPONSIBLE AI & ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════
with tab_safety:
    st.markdown("### ⚖️ **Responsible AI & Sustainable Architecture**")
    st.caption("How GhostWatch embodies the Core Principles of Ethical, Fair, and Auditable AI.")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown(
            """
            <div class="gw-box">
                <h4 style="color:#38bdf8; margin-top:0;">1. Fairness & Equity by Design</h4>
                <p>
                <b>The Problem:</b> Wealthier or technologically connected wards submit far more grievance tickets. 
                Relying purely on complaint counts biases repairs toward high-reporting neighborhoods.
                </p>
                <p>
                <b>GhostWatch Solution:</b> The <code>silence_scorer</code> computes an asset's risk score 
                <b>solely from calendar maintenance gaps</b>, completely isolated from complaint counts. 
                An asset in an underserved ward with 0 complaints is still surfaced for inspection if overdue.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="gw-box">
                <h4 style="color:#fbbf24; margin-top:0;">2. Strictly Hedged Output Language</h4>
                <p>
                <b>The Problem:</b> AI hallucination or premature definitive claims (e.g., "Asset is broken") 
                can damage contractor reputations and trigger premature warranty claims.
                </p>
                <p>
                <b>GhostWatch Solution:</b> The <code>guardrails</code> layer and Granite Guardian verify that all 
                output summaries use probabilistic phrasing such as <i>"exhibits indications of probable failure"</i> 
                and explicitly cite verifiable complaint IDs.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_p2:
        st.markdown(
            """
            <div class="gw-box">
                <h4 style="color:#34d399; margin-top:0;">3. Privacy Preservation & PII Redaction</h4>
                <p>
                <b>The Problem:</b> Citizen grievances often contain personal identifiers (names, phone numbers, emails, Aadhaar numbers).
                </p>
                <p>
                <b>GhostWatch Solution:</b> Automated regex-based scrubbing runs at the initial ingestion stage 
                (<code>data_loader.py</code>) before data is stored or embedded in RAG vector indexes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="gw-box">
                <h4 style="color:#c084fc; margin-top:0;">4. Transparency & Auditable Traces</h4>
                <p>
                <b>The Problem:</b> Black-box AI decisions cannot be audited by municipal engineers or procurement authorities.
                </p>
                <p>
                <b>GhostWatch Solution:</b> Every step taken by the agentic pipeline—retrieval, silence scoring, 
                cross-referencing, and guardrails—is logged into structured JSON traces saved in <code>logs/</code>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### 📐 **System Pipeline Architecture**")
    st.code(
        """
        ┌─────────────────────────────────────────────────────────────────┐
        │                      Streamlit Dashboard                        │
        │         (Map view · Flag list · Evidence drill-down)            │
        └───────────────────────────┬───────────────────────────────────┘
                                     │
        ┌───────────────────────────▼───────────────────────────────────┐
        │                     Agent Orchestrator                          │
        │              (watsonx.ai Agent Lab / LangGraph)                 │
        │                                                                   │
        │  load_asset_registry → retrieve_signals → silence_scorer →      │
        │  cross_reference_classifier → generate_flag_report → escalate   │
        └───────┬───────────────┬──────────────┬───────────────┬─────────┘
                │               │              │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼───────┐
        │ Asset        │ │ RAG /       │ │ Granite    │ │ Granite      │
        │ Registry DB  │ │ Vector      │ │ Instruct   │ │ Guardian     │
        │ (CSV/JSON)   │ │ Store       │ │ Model      │ │ (safety)     │
        └──────────────┘ └─────────────┘ └────────────┘ └──────────────┘
        """,
        language="text",
    )
