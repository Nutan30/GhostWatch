import React from 'react';

export default function KPICards({ summary }) {
  if (!summary) return null;

  return (
    <div className="metrics-row" aria-label="Audit summary metrics">
      <div className="metric-box">
        <div className="metric-number">{summary.total_assets || 0}</div>
        <div className="metric-label">Registered Assets</div>
        <div className="metric-note">Across 10 municipal wards</div>
      </div>

      <div className="metric-box">
        <div className="metric-number" style={{ color: 'var(--status-warning-text)' }}>
          {summary.silence_flags || 0}
        </div>
        <div className="metric-label">Maintenance Overdue</div>
        <div className="metric-note">Exceeding service schedule</div>
      </div>

      <div className="metric-box">
        <div className="metric-number" style={{ color: 'var(--accent)' }}>
          {summary.complaint_matches || 0}
        </div>
        <div className="metric-label">Citizen Complaints</div>
        <div className="metric-note">Corroborated via RAG matching</div>
      </div>

      <div className="metric-box">
        <div className="metric-number" style={{ color: 'var(--status-alert-text)' }}>
          {summary.high_confidence_flags || 0}
        </div>
        <div className="metric-label">High-Priority Flags</div>
        <div className="metric-note">Confidence 75% or higher</div>
      </div>

      <div className="metric-box">
        <div className="metric-number" style={{ color: 'var(--status-normal-text)' }}>
          {summary.warranty_active_flags || 0}
        </div>
        <div className="metric-label">Active Warranties</div>
        <div className="metric-note">Contractor AMC liability applies</div>
      </div>
    </div>
  );
}
