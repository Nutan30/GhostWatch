import React from 'react';

export default function LegalModal({ type, onClose }) {
  if (!type) return null;

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
            {type === 'terms' ? 'Terms of Service' : 'Privacy Policy'}
          </h3>
          <button className="btn btn-outline btn-small" onClick={onClose} aria-label="Close modal">
            Close
          </button>
        </div>

        <div className="modal-body">
          <p style={{ color: 'var(--status-warning-text)', background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-border)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.8rem', marginBottom: '14px' }}>
            Draft for municipal review. This document summarizes the operational parameters of the GhostWatch demonstration system.
          </p>

          {type === 'terms' ? (
            <>
              <h4>1. Scope of Application</h4>
              <p>
                GhostWatch provides algorithmic screening of public sustainability infrastructure assets to assist municipal maintenance scheduling. All outputs, including confidence scores and inspection notices, represent advisory recommendations and not verified physical findings.
              </p>

              <h4>2. Physical Verification Requirement</h4>
              <p>
                Municipal engineering staff must physically inspect flagged infrastructure assets before issuing contractual default notices or financial penalties against installation contractors.
              </p>

              <h4>3. Data Attribution</h4>
              <p>
                Demonstration datasets and maintenance intervals are synthetic or modeled from municipal guidelines. In production deployments, accuracy depends on the fidelity of ingested municipal asset registries and grievance records.
              </p>

              <h4>4. Liability Limitations</h4>
              <p>
                The GhostWatch prototype is provided on an evaluation basis without warranties of uninterrupted service or absolute detection completeness.
              </p>
            </>
          ) : (
            <>
              <h4>1. Citizen Privacy by Design</h4>
              <p>
                GhostWatch processes public grievance ticket descriptions solely to identify operational failure patterns. The system does not profile individual citizens or retain personal identity records.
              </p>

              <h4>2. Automated PII Redaction</h4>
              <p>
                Incoming grievance text is scanned at ingestion. Phone numbers, email addresses, national identification numbers, and names are stripped or redacted prior to vector indexing or model evaluation.
              </p>

              <h4>3. Data Storage and Retention</h4>
              <p>
                Audit traces and evaluation metrics are retained locally in application logs for municipal accountability. Data is not shared with commercial third parties.
              </p>

              <h4>4. Municipal Inquiries</h4>
              <p>
                Questions regarding data handling practices may be directed to municipal public works project supervisors.
              </p>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
}
