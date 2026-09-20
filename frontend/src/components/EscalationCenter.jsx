import React, { useState } from 'react';

export default function EscalationCenter({ escalations, typeDisplayMap }) {
  const [copiedId, setCopiedId] = useState(null);

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownload = (id, text) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ESCALATION_NOTICE_${id}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <div className="panel" style={{ marginBottom: '16px' }}>
        <h3 className="panel-heading">High-Priority Escalation Notices</h3>
        <p className="panel-description" style={{ marginBottom: 0 }}>
          Draft inspection dispatch notices generated for assets exceeding the 75% confidence threshold.
          Liability is assigned based on active warranty coverage.
        </p>
      </div>

      {escalations.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {escalations.map((esc) => {
            const displayType = typeDisplayMap[esc.asset_type] || esc.asset_type;
            const isContractor = esc.responsible_party.includes('Contractor');

            return (
              <div key={esc.asset_id} className="panel" style={{ borderLeft: '4px solid #b91c1c' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>
                      {esc.asset_id} ({displayType})
                    </h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                      Location: {esc.location}
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="status-pill status-escalate">
                      {Math.round(esc.confidence_score * 100)}% Confidence
                    </span>
                    <button
                      type="button"
                      className="btn btn-outline btn-small"
                      onClick={() => handleCopy(esc.asset_id, esc.notice_text)}
                    >
                      {copiedId === esc.asset_id ? 'Copied' : 'Copy Text'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline btn-small"
                      onClick={() => handleDownload(esc.asset_id, esc.notice_text)}
                    >
                      Download Notice (.txt)
                    </button>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px', marginBottom: '12px', fontSize: '0.82rem' }}>
                  <div style={{ background: 'var(--bg-subtle)', padding: '8px 10px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>
                      Responsible Entity
                    </div>
                    <div style={{ fontWeight: 600, color: isContractor ? 'var(--accent)' : 'var(--text-main)', marginTop: '2px' }}>
                      {esc.responsible_party}
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-subtle)', padding: '8px 10px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 600 }}>
                      Liability Status
                    </div>
                    <div style={{ fontWeight: 500, color: 'var(--text-main)', marginTop: '2px' }}>
                      {esc.warranty_status}
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '3px' }}>
                    Evidence Summary
                  </div>
                  <div style={{ background: 'var(--bg-canvas)', border: '1px solid var(--border)', borderRadius: '4px', padding: '8px 10px', fontSize: '0.82rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                    {esc.evidence_summary}
                  </div>
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '3px' }}>
                    Mandated Field Inspection Procedures
                  </div>
                  <pre className="terminal-block" style={{ fontSize: '0.78rem', background: 'var(--bg-subtle)', color: 'var(--text-main)', border: '1px solid var(--border)' }}>
                    {esc.suggested_inspection}
                  </pre>
                </div>

                <div>
                  <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '3px' }}>
                    Draft Municipal Inspection Notice Document
                  </div>
                  <textarea
                    readOnly
                    value={esc.notice_text}
                    className="control-field"
                    style={{ height: '130px', fontFamily: 'var(--font-mono)', fontSize: '0.76rem', lineHeight: '1.4' }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="panel">
          No assets currently meet the high-priority escalation confidence threshold (75% or higher).
        </div>
      )}
    </div>
  );
}
