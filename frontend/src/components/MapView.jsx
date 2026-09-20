import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

export default function MapView({ filteredAssets, reportsById, typeDisplayMap, allTypes, allWards }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [19.0760, 72.8777],
        zoom: 11,
      });

      // CartoDB Positron light neutral tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

      markersLayerRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    markersLayer.clearLayers();

    if (filteredAssets.length > 0) {
      const bounds = [];

      filteredAssets.forEach((asset) => {
        const rep = reportsById[asset.asset_id];
        if (!rep) return;

        const isEscalate = rep.confidence_score >= 0.75 || (rep.silence_flag && rep.matched_complaints?.length > 0);
        const isSilenceOnly = rep.silence_flag && (!rep.matched_complaints || rep.matched_complaints.length === 0);

        let color = '#15803d'; // green
        let statusLabel = 'Operational';

        if (isEscalate) {
          color = '#b91c1c'; // red
          statusLabel = 'Escalation Recommended';
        } else if (isSilenceOnly) {
          color = '#d97706'; // amber
          statusLabel = 'Maintenance Overdue';
        }

        const marker = L.circleMarker([asset.latitude, asset.longitude], {
          radius: isEscalate ? 8 : 6,
          fillColor: color,
          color: '#ffffff',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.9,
        });

        const displayType = typeDisplayMap[asset.asset_type] || asset.asset_type;
        const popupHtml = `
          <div style="font-family: inherit; font-size: 13px; min-width: 190px; color: #18181b;">
            <div style="font-weight: 700; margin-bottom: 4px; border-bottom: 1px solid #e4e2dd; padding-bottom: 4px;">
              ${asset.asset_id}
            </div>
            <div style="margin-bottom: 2px;"><b>Type:</b> ${displayType}</div>
            <div style="margin-bottom: 4px;"><b>Location:</b> ${asset.location_name}</div>
            <div style="margin-bottom: 2px;"><b>Status:</b> ${statusLabel}</div>
            <div style="margin-bottom: 2px;"><b>Confidence:</b> ${Math.round(rep.confidence_score * 100)}%</div>
            <div style="margin-bottom: 2px;"><b>Action:</b> ${(rep.recommended_action || '').toUpperCase()}</div>
            <div><b>Warranty:</b> ${rep.warranty_active ? 'Active' : 'Expired'}</div>
          </div>
        `;

        marker.bindPopup(popupHtml);
        marker.addTo(markersLayer);
        bounds.push([asset.latitude, asset.longitude]);
      });

      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
    }
  }, [filteredAssets, reportsById, typeDisplayMap]);

  return (
    <div>
      <div className="panel">
        <h3 className="panel-heading">Geographic Asset Distribution</h3>
        <p className="panel-description">
          Spatial distribution of audited public sustainability assets across wards. Marker color indicates operational health.
          Green: Operational | Amber: Maintenance Overdue | Red: Corroborated Failure Flag.
        </p>
        <div ref={mapContainerRef} className="map-container" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.95rem' }}>
            Category Risk Summary
          </h4>
          <div className="table-wrapper">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Total</th>
                  <th>Overdue</th>
                  <th>High Priority</th>
                </tr>
              </thead>
              <tbody>
                {allTypes.map((t) => {
                  const typeAssets = filteredAssets.filter((a) => a.asset_type === t);
                  const typeReps = typeAssets.map((a) => reportsById[a.asset_id]).filter(Boolean);
                  return (
                    <tr key={t}>
                      <td style={{ fontWeight: 600 }}>{typeDisplayMap[t] || t}</td>
                      <td>{typeAssets.length}</td>
                      <td>{typeReps.filter((r) => r.silence_flag).length}</td>
                      <td style={{ fontWeight: 600 }}>
                        {typeReps.filter((r) => r.confidence_score >= 0.75).length}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <h4 className="panel-heading" style={{ fontSize: '0.95rem' }}>
            Ward Concentration
          </h4>
          <div className="table-wrapper" style={{ maxHeight: '220px', overflowY: 'auto' }}>
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Ward</th>
                  <th>Assets</th>
                  <th>Overdue</th>
                  <th>High Priority</th>
                </tr>
              </thead>
              <tbody>
                {allWards.map((w) => {
                  const wardAssets = filteredAssets.filter((a) => a.location_name.includes(w));
                  const wardReps = wardAssets.map((a) => reportsById[a.asset_id]).filter(Boolean);
                  if (wardAssets.length === 0) return null;
                  return (
                    <tr key={w}>
                      <td style={{ fontWeight: 600 }}>{w}</td>
                      <td>{wardAssets.length}</td>
                      <td>{wardReps.filter((r) => r.silence_flag).length}</td>
                      <td style={{ fontWeight: 600 }}>
                        {wardReps.filter((r) => r.confidence_score >= 0.75).length}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
