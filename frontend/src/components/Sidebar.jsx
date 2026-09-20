import React from 'react';

export default function Sidebar({
  allTypes,
  typeDisplayMap,
  selectedTypes,
  setSelectedTypes,
  allWards,
  selectedWards,
  setSelectedWards,
  statusFilter,
  setStatusFilter,
  minConfidence,
  setMinConfidence,
  onRerun,
  isRerunning,
  meta,
}) {
  const handleTypeToggle = (type) => {
    if (selectedTypes.includes(type)) {
      if (selectedTypes.length > 1) {
        setSelectedTypes(selectedTypes.filter((t) => t !== type));
      }
    } else {
      setSelectedTypes([...selectedTypes, type]);
    }
  };

  return (
    <aside className="sidebar" aria-label="Audit filters and settings">
      <div style={{ marginBottom: '18px' }}>
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Audit Controls
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: '2px' }}>
          Municipal filter parameters
        </p>
      </div>

      <div style={{ background: 'var(--bg-subtle)', padding: '10px 12px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '18px' }}>
        <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '2px' }}>
          {meta?.ibm_credentials_available ? 'IBM watsonx Active' : 'Resilient Prototype Engine'}
        </div>
        <div>LangGraph state orchestrator</div>
        <div>In-memory vector retrieval</div>
        <div>Deterministic safety guardrails</div>
      </div>

      {/* Filter: Asset Type */}
      <div className="control-group">
        <span className="control-label">Asset Categories</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {allTypes.map((type) => (
            <label key={type} className="checkbox-row">
              <input
                type="checkbox"
                checked={selectedTypes.includes(type)}
                onChange={() => handleTypeToggle(type)}
              />
              <span>{typeDisplayMap[type] || type}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Filter: Ward */}
      <div className="control-group">
        <label htmlFor="ward-select" className="control-label">
          Municipal Ward
        </label>
        <select
          id="ward-select"
          className="control-field"
          value={selectedWards[0] || 'ALL'}
          onChange={(e) => {
            const val = e.target.value;
            if (val === 'ALL') {
              setSelectedWards(allWards);
            } else {
              setSelectedWards([val]);
            }
          }}
        >
          <option value="ALL">All Wards ({allWards.length})</option>
          {allWards.map((w) => (
            <option key={w} value={w}>
              {w}
            </option>
          ))}
        </select>
      </div>

      {/* Filter: Risk Profile */}
      <div className="control-group">
        <label htmlFor="status-select" className="control-label">
          Risk Profile
        </label>
        <select
          id="status-select"
          className="control-field"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="All Assets">All Assets</option>
          <option value="High Priority (Escalate)">High Priority (Escalate)</option>
          <option value="Silence Warning (Overdue Check)">Silence Warning (Overdue Check)</option>
          <option value="Active / Healthy">Active / Healthy</option>
        </select>
      </div>

      {/* Filter: Confidence Slider */}
      <div className="control-group">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <label htmlFor="conf-slider" className="control-label" style={{ marginBottom: 0 }}>
            Confidence Cutoff
          </label>
          <span style={{ fontSize: '0.8rem', color: 'var(--accent)', fontWeight: 700 }}>
            {Math.round(minConfidence * 100)}%
          </span>
        </div>
        <input
          id="conf-slider"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={minConfidence}
          onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--accent)' }}
        />
      </div>

      <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
        <button
          type="button"
          className="btn btn-accent"
          style={{ width: '100%' }}
          onClick={onRerun}
          disabled={isRerunning}
        >
          {isRerunning ? 'Evaluating...' : 'Re-run Agent Audit'}
        </button>
        <div style={{ marginTop: '10px', textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Simulated dataset based on municipal infrastructure guidelines
        </div>
      </div>
    </aside>
  );
}
