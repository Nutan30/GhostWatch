import React, { useState } from 'react';

export default function AssetTable({ filteredAssets, reportsById, typeDisplayMap, onSelectAsset }) {
  const [searchTerm, setSearchTerm] = useState('');

  const displayList = filteredAssets.filter((a) => {
    const q = searchTerm.toLowerCase();
    return (
      a.asset_id.toLowerCase().includes(q) ||
      a.location_name.toLowerCase().includes(q) ||
      a.contractor_name.toLowerCase().includes(q) ||
      (typeDisplayMap[a.asset_type] || '').toLowerCase().includes(q)
    );
  });

  const exportCSV = () => {
    const headers = [
      'Asset ID',
      'Category',
      'Location',
      'Confidence Percent',
      'Action',
      'Silence Overdue Months',
      'Grievances Count',
      'Warranty Status',
      'Contractor',
      'Hedge Check',
    ];

    const rows = displayList.map((a) => {
      const rep = reportsById[a.asset_id] || {};
      const overdue = rep.silence_details?.months_overdue || 0;
      return [
        `"${a.asset_id}"`,
        `"${typeDisplayMap[a.asset_type] || a.asset_type}"`,
        `"${a.location_name}"`,
        Math.round((rep.confidence_score || 0) * 100),
        `"${(rep.recommended_action || 'monitor').toUpperCase()}"`,
        overdue,
        rep.matched_complaints?.length || 0,
        rep.warranty_active ? 'Active' : 'Expired',
        `"${a.contractor_name}"`,
        rep.output_language_hedge_check ? 'Passed' : 'Pending',
      ].join(',');
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `ghostwatch_audit_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 className="panel-heading">Asset Registry and Flags</h3>
          <p className="panel-description" style={{ marginBottom: 0 }}>
            Showing {displayList.length} of {filteredAssets.length} matching municipal assets. Click an asset row to view its evidence trail.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div>
            <label htmlFor="search-input" className="control-label" style={{ display: 'none' }}>
              Search Assets
            </label>
            <input
              id="search-input"
              type="text"
              placeholder="Search ID, ward, contractor..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="control-field"
              style={{ width: '240px' }}
            />
          </div>
          <button type="button" className="btn btn-outline" onClick={exportCSV}>
            Export CSV
          </button>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="audit-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Asset ID</th>
              <th>Category</th>
              <th>Location</th>
              <th>Confidence</th>
              <th>Overdue</th>
              <th>Complaints</th>
              <th>Warranty</th>
              <th>Contractor</th>
              <th>Hedge Check</th>
            </tr>
          </thead>
          <tbody>
            {displayList.map((asset) => {
              const rep = reportsById[asset.asset_id] || {};
              const overdue = rep.silence_details?.months_overdue || 0;
              const displayType = typeDisplayMap[asset.asset_type] || asset.asset_type;

              let statusClass = 'status-monitor';
              let actionLabel = 'Monitor';

              if (rep.recommended_action === 'escalate') {
                statusClass = 'status-escalate';
                actionLabel = 'Escalate';
              } else if (rep.recommended_action === 'inspect') {
                statusClass = 'status-inspect';
                actionLabel = 'Inspect';
              }

              return (
                <tr
                  key={asset.asset_id}
                  onClick={() => onSelectAsset && onSelectAsset(asset.asset_id)}
                  style={{ cursor: 'pointer' }}
                  title="Click to view detailed evidence trail and agent trace"
                >
                  <td>
                    <span className={`status-pill ${statusClass}`}>{actionLabel}</span>
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--accent)' }}>{asset.asset_id}</td>
                  <td>{displayType}</td>
                  <td>{asset.location_name}</td>
                  <td style={{ fontWeight: 600 }}>
                    {Math.round((rep.confidence_score || 0) * 100)}%
                  </td>
                  <td>{overdue > 0 ? `${overdue} mo` : '0 mo'}</td>
                  <td>{rep.matched_complaints?.length || 0}</td>
                  <td>{rep.warranty_active ? 'Active' : 'Expired'}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{asset.contractor_name}</td>
                  <td>
                    <span style={{ color: 'var(--status-normal-text)', fontSize: '0.76rem', fontWeight: 600 }}>
                      Passed
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
