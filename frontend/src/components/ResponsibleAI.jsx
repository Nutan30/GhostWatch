import React from 'react';

export default function ResponsibleAI() {
  return (
    <div>
      <div className="panel" style={{ marginBottom: '16px' }}>
        <h3 className="panel-heading">Responsible AI and Sustainable Architecture</h3>
        <p className="panel-description" style={{ marginBottom: 0 }}>
          Principles governing the GhostWatch evaluation engine for municipal sustainability assets.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.95rem', color: 'var(--accent)' }}>
            1. Fairness and Equity by Design
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '8px' }}>
            <b>Problem:</b> Wealthier or digitally connected wards report significantly higher complaint volumes. Evaluating assets solely by complaint count directs municipal repairs toward high-reporting neighborhoods.
          </p>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
            <b>Methodology:</b> The silence scorer calculates risk solely from calendar maintenance gaps, isolated from complaint counts. Assets in low-reporting wards are surfaced for inspection when maintenance intervals lapse.
          </p>
        </div>

        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.95rem', color: 'var(--status-warning-text)' }}>
            2. Strictly Hedged Output Language
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '8px' }}>
            <b>Problem:</b> Unhedged assertions declaring an asset broken before physical inspection risk premature contractor penalties and legal disputes.
          </p>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
            <b>Methodology:</b> Automated safety guardrails verify that all outputs use probabilistic framing, such as probable operational failure, and cite specific complaint records.
          </p>
        </div>

        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.95rem', color: 'var(--status-normal-text)' }}>
            3. Privacy Preservation and PII Redaction
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '8px' }}>
            <b>Problem:</b> Public grievance descriptions often include citizen telephone numbers, personal names, email addresses, and identification numbers.
          </p>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
            <b>Methodology:</b> Automated pattern filters sanitize text during initial CSV ingestion before data enters the vector store or reasoning pipeline.
          </p>
        </div>

        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>
            4. Transparency and Auditable Traces
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '8px' }}>
            <b>Problem:</b> Unexplained algorithmic flags cannot be verified during public procurement audits.
          </p>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
            <b>Methodology:</b> Every step taken by the agent orchestrator is recorded as a structured JSON trace in application logs for engineering verification.
          </p>
        </div>
      </div>

      <div className="panel">
        <h4 className="panel-heading">System Pipeline Architecture</h4>
        <p className="panel-description">
          Data flow from ingestion and silence scoring through safety screening and dispatch notice drafting.
        </p>
        <pre className="terminal-block">
{`+-----------------------------------------------------------------+
|                       React SPA Frontend                        |
|        (Geographic Map, Audit Table, Evidence Drill-Down)       |
+--------------------------------+--------------------------------+
                                 | REST JSON API
+--------------------------------v--------------------------------+
|                     FastAPI Server (api.py)                     |
|                   (In-Memory Pipeline Cache)                    |
+--------------------------------+--------------------------------+
                                 |
+--------------------------------v--------------------------------+
|                       Agent Orchestrator                        |
|                    (LangGraph State Machine)                    |
|                                                                 |
| load_asset_registry -> retrieve_signals -> silence_scorer ->    |
| cross_reference_classifier -> generate_flag_report ->           |
| guardrails (hedge and PII check) -> escalate                    |
+--------+---------------+---------------+----------------+-------+
         |               |               |                |
+--------v-------+ +-----v---------+ +---v----------+ +---v-------+
| Asset Registry | | RAG Vector    | | IBM Granite  | | Granite   |
| Database (CSV) | | Store (Cosine)| | Instruct LLM | | Guardian  |
+----------------+ +---------------+ +--------------+ +-----------+`}
        </pre>
      </div>
    </div>
  );
}
