import React, { useState, useEffect, useMemo } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import KPICards from './components/KPICards';
import MapView from './components/MapView';
import AssetTable from './components/AssetTable';
import EvidenceDrilldown from './components/EvidenceDrilldown';
import EscalationCenter from './components/EscalationCenter';
import ResponsibleAI from './components/ResponsibleAI';
import LegalModal from './components/LegalModal';

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRerunning, setIsRerunning] = useState(false);

  // Tab State
  const [activeTab, setActiveTab] = useState('map');

  // Filter States
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedWards, setSelectedWards] = useState([]);
  const [statusFilter, setStatusFilter] = useState('All Assets');
  const [minConfidence, setMinConfidence] = useState(0.0);

  // Selected Asset for Evidence Drilldown
  const [selectedAssetId, setSelectedAssetId] = useState(null);

  // Legal Modal State
  const [legalModalType, setLegalModalType] = useState(null);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/audit');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const json = await res.json();
      setData(json);

      const types = Array.from(new Set(json.assets.map((a) => a.asset_type)));
      setSelectedTypes(types);

      const wards = Array.from(new Set(json.assets.map((a) => a.location_name.split(',')[0].trim()))).sort();
      setSelectedWards(wards);

      if (json.assets.length > 0 && !selectedAssetId) {
        setSelectedAssetId(json.assets[0].asset_id);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load audit data:', err);
      setError('Unable to connect to the GhostWatch API. Verify that api.py is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  const handleRerun = async () => {
    try {
      setIsRerunning(true);
      const res = await fetch('/api/rerun', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      await fetchAuditData();
    } catch (err) {
      console.error('Failed to rerun pipeline:', err);
      alert('Failed to rerun pipeline: ' + err.message);
    } finally {
      setIsRerunning(false);
    }
  };

  const reportsById = useMemo(() => {
    if (!data?.reports) return {};
    return data.reports.reduce((acc, r) => {
      acc[r.asset_id] = r;
      return acc;
    }, {});
  }, [data?.reports]);

  const tracesById = useMemo(() => {
    return data?.traces || {};
  }, [data?.traces]);

  const allTypes = useMemo(() => {
    if (!data?.assets) return [];
    return Array.from(new Set(data.assets.map((a) => a.asset_type)));
  }, [data?.assets]);

  const allWards = useMemo(() => {
    if (!data?.assets) return [];
    return Array.from(new Set(data.assets.map((a) => a.location_name.split(',')[0].trim()))).sort();
  }, [data?.assets]);

  const typeDisplayMap = data?.type_display_map || {};

  const filteredAssets = useMemo(() => {
    if (!data?.assets) return [];

    return data.assets.filter((asset) => {
      const rep = reportsById[asset.asset_id];
      if (!rep) return false;

      if (selectedTypes.length > 0 && !selectedTypes.includes(asset.asset_type)) {
        return false;
      }

      const ward = asset.location_name.split(',')[0].trim();
      if (selectedWards.length > 0 && !selectedWards.includes(ward)) {
        return false;
      }

      if (rep.confidence_score < minConfidence) {
        return false;
      }

      if (statusFilter === 'High Priority (Escalate)' && rep.recommended_action !== 'escalate') {
        return false;
      }
      if (
        statusFilter === 'Silence Warning (Overdue Check)' &&
        !(rep.silence_flag && (!rep.matched_complaints || rep.matched_complaints.length === 0))
      ) {
        return false;
      }
      if (
        statusFilter === 'Active / Healthy' &&
        (rep.silence_flag || (rep.matched_complaints && rep.matched_complaints.length > 0))
      ) {
        return false;
      }

      return true;
    });
  }, [data?.assets, reportsById, selectedTypes, selectedWards, statusFilter, minConfidence]);

  const handleSelectAssetFromTable = (assetId) => {
    setSelectedAssetId(assetId);
    setActiveTab('evidence');
  };

  if (loading && !data) {
    return (
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-canvas)', padding: '24px' }}>
        <div style={{ width: '100%', maxWidth: '480px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '4px', padding: '24px' }}>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            Loading GhostWatch Audit Data
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', marginBottom: '16px' }}>
            Evaluating municipal asset maintenance records and citizen grievance signals.
          </p>
          <div style={{ height: '4px', width: '100%', background: 'var(--bg-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '45%', background: 'var(--accent)' }} />
          </div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-canvas)', padding: '24px' }}>
        <div className="panel" style={{ maxWidth: '480px', borderLeft: '4px solid #b91c1c' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#b91c1c', marginBottom: '6px' }}>
            Connection Required
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', marginBottom: '16px' }}>
            {error}
          </p>
          <button type="button" className="btn btn-accent" onClick={fetchAuditData}>
            Retry Request
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar
        allTypes={allTypes}
        typeDisplayMap={typeDisplayMap}
        selectedTypes={selectedTypes}
        setSelectedTypes={setSelectedTypes}
        allWards={allWards}
        selectedWards={selectedWards}
        setSelectedWards={setSelectedWards}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        minConfidence={minConfidence}
        setMinConfidence={setMinConfidence}
        onRerun={handleRerun}
        isRerunning={isRerunning}
        meta={data?.meta}
      />

      <main className="main-content">
        <Header meta={data?.meta} />

        <KPICards summary={data?.summary} />

        {/* Tab Navigation */}
        <nav className="tab-navigation" aria-label="Dashboard sections">
          <button
            type="button"
            className={`tab-link ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            Overview and Map
          </button>

          <button
            type="button"
            className={`tab-link ${activeTab === 'table' ? 'active' : ''}`}
            onClick={() => setActiveTab('table')}
          >
            Asset Registry ({filteredAssets.length})
          </button>

          <button
            type="button"
            className={`tab-link ${activeTab === 'evidence' ? 'active' : ''}`}
            onClick={() => setActiveTab('evidence')}
          >
            Evidence Trail
          </button>

          <button
            type="button"
            className={`tab-link ${activeTab === 'escalation' ? 'active' : ''}`}
            onClick={() => setActiveTab('escalation')}
          >
            Escalation Notices ({data?.escalations?.length || 0})
          </button>

          <button
            type="button"
            className={`tab-link ${activeTab === 'safety' ? 'active' : ''}`}
            onClick={() => setActiveTab('safety')}
          >
            Responsible AI and Methodology
          </button>
        </nav>

        {/* Tab Content */}
        {activeTab === 'map' && (
          <MapView
            filteredAssets={filteredAssets}
            reportsById={reportsById}
            typeDisplayMap={typeDisplayMap}
            allTypes={allTypes}
            allWards={allWards}
          />
        )}

        {activeTab === 'table' && (
          <AssetTable
            filteredAssets={filteredAssets}
            reportsById={reportsById}
            typeDisplayMap={typeDisplayMap}
            onSelectAsset={handleSelectAssetFromTable}
          />
        )}

        {activeTab === 'evidence' && (
          <EvidenceDrilldown
            assets={data?.assets || []}
            reportsById={reportsById}
            tracesById={tracesById}
            typeDisplayMap={typeDisplayMap}
            selectedAssetId={selectedAssetId}
            setSelectedAssetId={setSelectedAssetId}
          />
        )}

        {activeTab === 'escalation' && (
          <EscalationCenter
            escalations={data?.escalations || []}
            typeDisplayMap={typeDisplayMap}
          />
        )}

        {activeTab === 'safety' && <ResponsibleAI />}

        {/* Legal Footer */}
        <footer className="legal-footer">
          <div>
            GhostWatch Municipal Infrastructure Screening Engine. Synthetic evaluation dataset.
          </div>
          <div className="legal-links">
            <button
              type="button"
              className="legal-link-btn"
              onClick={() => setLegalModalType('terms')}
            >
              Terms of Service
            </button>
            <button
              type="button"
              className="legal-link-btn"
              onClick={() => setLegalModalType('privacy')}
            >
              Privacy Policy
            </button>
          </div>
        </footer>

        {/* Legal Modal */}
        <LegalModal
          type={legalModalType}
          onClose={() => setLegalModalType(null)}
        />
      </main>
    </div>
  );
}
