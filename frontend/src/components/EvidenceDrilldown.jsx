import React, { useState } from 'react';

export default function EvidenceDrilldown({
  assets,
  reportsById,
  tracesById,
  typeDisplayMap,
  selectedAssetId,
  setSelectedAssetId,
}) {
  const [expandedSteps, setExpandedSteps] = useState({});

  const currentId = selectedAssetId || (assets[0] ? assets[0].asset_id : null);
  const selectedAsset = assets.find((a) => a.asset_id === currentId);
  const rep = selectedAsset ? reportsById[selectedAsset.asset_id] || {} : {};
  const trace = selectedAsset ? tracesById[selectedAsset.asset_id] || {} : {};
  const displayType = selectedAsset ? typeDisplayMap[selectedAsset.asset_type] || selectedAsset.asset_type : '';

  const toggleStep = (step) => {
    setExpandedSteps((prev) => ({ ...prev, [step]: !prev[step] }));
  };

  if (!selectedAsset) {
    return <div className="panel">No assets available to inspect.</div>;
  }

  const sil = rep.silence_details || {};
  const overdueVal = sil.months_overdue || 0;
  const crossDetails = rep.cross_ref_details || [];
  const steps = trace.steps || [];

  return (
    <div>
      <div className="panel" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 className="panel-heading">Evidence Trail and Agent Audit</h3>
            <p className="panel-description" style={{ marginBottom: 0 }}>
              Review physical telemetry, citizen complaints, and algorithmic reasoning for an individual infrastructure asset.
            </p>
          </div>

          <div style={{ minWidth: '320px' }}>
            <label htmlFor="asset-picker" className="control-label">
              Selected Asset
            </label>
            <select
              id="asset-picker"
              className="control-field"
              value={currentId}
              onChange={(e) => setSelectedAssetId(e.target.value)}
            >
              {assets.map((a) => (
                <option key={a.asset_id} value={a.asset_id}>
                  {a.asset_id} ({typeDisplayMap[a.asset_type] || a.asset_type}, {a.location_name})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 4 Quadrants */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        {/* Quadrant 1 */}
        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.92rem' }}>
            1. Asset Specifications
          </h4>
          <div style={{ fontSize: '0.84rem', lineHeight: '1.8', color: 'var(--text-main)', marginTop: '8px' }}>
            <div><b>Asset ID:</b> <code style={{ color: 'var(--accent)' }}>{selectedAsset.asset_id}</code></div>
            <div><b>Category:</b> {displayType}</div>
            <div><b>Location:</b> {selectedAsset.location_name}</div>
            <div><b>Coordinates:</b> {selectedAsset.latitude}, {selectedAsset.longitude}</div>
            <div><b>Installation Date:</b> {selectedAsset.install_date}</div>
            <div><b>Contractor on Record:</b> {selectedAsset.contractor_name}</div>
            <div>
              <b>Warranty Expiration:</b> {selectedAsset.warranty_end_date} ({rep.warranty_active ? 'Active' : 'Expired'})
            </div>
          </div>
        </div>

        {/* Quadrant 2 */}
        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.92rem' }}>
            2. Maintenance Silence Telemetry
          </h4>
          <div style={{ fontSize: '0.84rem', lineHeight: '1.8', color: 'var(--text-main)', marginTop: '8px' }}>
            <div><b>Required Service Interval:</b> Every {selectedAsset.expected_service_interval_months} months</div>
            <div><b>Last Service Record:</b> {selectedAsset.last_maintenance_log_date || 'No record logged since install'}</div>
            <div><b>Months Without Service:</b> {sil.months_since_last_activity || 0} months</div>
            <div>
              <b>Overdue Duration:</b>{' '}
              <span style={{ color: overdueVal > 0 ? 'var(--status-alert-text)' : 'var(--status-normal-text)', fontWeight: 600 }}>
                {overdueVal} months
              </span>
            </div>
            <div><b>Normalized Silence Score:</b> {sil.silence_score || 0} / 1.0</div>
            <div>
              <b>Silence Threshold:</b>{' '}
              <span style={{ color: rep.silence_flag ? 'var(--status-alert-text)' : 'var(--status-normal-text)', fontWeight: 600 }}>
                {rep.silence_flag ? 'Threshold Exceeded' : 'Within Schedule'}
              </span>
            </div>
          </div>
        </div>

        {/* Quadrant 3 */}
        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.92rem' }}>
            3. Corroborating Citizen Grievances ({crossDetails.length})
          </h4>
          {crossDetails.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px', maxHeight: '240px', overflowY: 'auto' }}>
              {crossDetails.map((c) => (
                <div
                  key={c.complaint_id}
                  style={{
                    background: 'var(--bg-subtle)',
                    padding: '8px 10px',
                    borderRadius: '4px',
                    border: '1px solid var(--border)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <code style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.complaint_id}</code>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent)' }}>
                      {Math.round((c.similarity || 0) * 100)}% Match
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    "{c.text}"
                  </p>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Reported: {c.date_reported || 'Not specified'} | Semantic similarity: {c.semantic_similarity}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginTop: '8px' }}>
              No public grievance records matched this specific asset location or equipment type.
            </p>
          )}
        </div>

        {/* Quadrant 4 */}
        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.92rem' }}>
            4. Synthesized Evidence Summary
          </h4>
          <p style={{ fontSize: '0.84rem', lineHeight: '1.6', color: 'var(--text-main)', marginTop: '8px', marginBottom: '12px' }}>
            {rep.evidence_summary}
          </p>
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px', fontSize: '0.84rem', lineHeight: '1.8' }}>
            <div>
              <b>Confidence Level:</b> {Math.round((rep.confidence_score || 0) * 100)}%
            </div>
            <div>
              <b>Action Determination:</b> {(rep.recommended_action || '').toUpperCase()}
            </div>
            <div>
              <b>Safety Screen:</b>{' '}
              <span style={{ color: 'var(--status-normal-text)', fontWeight: 600 }}>
                {rep.output_language_hedge_check ? 'Verified (Hedged Language Enforced)' : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Trace */}
      <div className="panel">
        <h4 className="panel-heading">Step-by-Step Agentic Reasoning Trace</h4>
        <p className="panel-description">
          Execution trail generated during evaluation of {selectedAsset.asset_id}.
        </p>

        {steps.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {steps.map((s) => {
              const isExpanded = expandedSteps[s.step];
              return (
                <div
                  key={s.step}
                  style={{
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    background: 'var(--bg-surface)',
                  }}
                >
                  <div
                    onClick={() => toggleStep(s.step)}
                    style={{
                      padding: '8px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      background: 'var(--bg-subtle)',
                      fontSize: '0.84rem',
                      fontWeight: 600,
                    }}
                  >
                    <span>
                      Step {s.step}: {s.name}
                    </span>
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                      {s.duration_ms} ms [{isExpanded ? 'Hide' : 'Show'}]
                    </span>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '12px', fontSize: '0.8rem' }}>
                      <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        {s.description}
                      </p>
                      <pre className="terminal-block">{JSON.stringify(s, null, 2)}</pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>No trace details available.</p>
        )}
      </div>
    </div>
  );
}
