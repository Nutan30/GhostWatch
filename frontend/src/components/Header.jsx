import React from 'react';

export default function Header({ meta }) {
  return (
    <header className="page-header">
      <div className="brand-row">
        <h1 className="brand-title">
          <span style={{ color: 'var(--accent)' }}>Ghost</span>Watch
        </h1>
        <span className="brand-subtitle">
          Public Sustainability Infrastructure Failure Detection
        </span>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginTop: '2px' }}>
        Cross-referencing municipal asset maintenance calendars with citizen grievance reports to identify silent outages.
      </p>
      {/* <div className="context-row">
        <span className="tag">UN SDG 11: Sustainable Cities</span>
        <span className="tag">UN SDG 9: Industry and Infrastructure</span>
        <span className="tag">IBM SkillsBuild and AICTE</span>
        <span className="tag accent">
          {meta?.ibm_credentials_available ? "IBM Granite Active" : "IBM Granite Ready (Local Engine)"}
        </span>
      </div> */}
    </header>
  );
}
