import React, { useState } from 'react';
import { Radio, Satellite, AlertTriangle, ChevronDown, ChevronRight, Activity } from 'lucide-react';

/**
 * SatelliteInventory — permanent always-visible tracked objects panel.
 * Shows all satellites with their real-time threat status and orbital info.
 */
export default function SatelliteInventory({
  satellites = [],
  events = [],
  selectedSatId,
  onSelectSat,
}) {
  const [filter, setFilter] = useState('all');   // 'all' | 'threatened' | 'satellite' | 'debris'
  const [expanded, setExpanded] = useState(null); // satId of expanded card

  // Build threat map: satId -> { risk, count }
  const threatMap = {};
  for (const evt of events) {
    const ids = [evt.primaryObject.id, evt.secondaryObject.id];
    for (const id of ids) {
      if (!threatMap[id]) threatMap[id] = { risk: 'NOMINAL', count: 0 };
      threatMap[id].count += 1;
      const weights = { HIGH: 3, MEDIUM: 2, LOW: 1, NOMINAL: 0 };
      if (weights[evt.riskClassification] > weights[threatMap[id].risk]) {
        threatMap[id].risk = evt.riskClassification;
      }
    }
  }

  const RISK_COLOR = {
    HIGH:    'var(--c-critical)',
    MEDIUM:  'var(--c-warn)',
    LOW:     'var(--c-nominal)',
    NOMINAL: 'var(--border-bright)',
  };

  const RISK_LABEL = {
    HIGH:    '⚠ HIGH THREAT',
    MEDIUM:  '▲ MED THREAT',
    LOW:     '◆ LOW THREAT',
    NOMINAL: '● NOMINAL',
  };

  // Filter list
  const filtered = satellites.filter(sat => {
    if (filter === 'threatened') return threatMap[sat.id]?.count > 0;
    if (filter === 'satellite')  return sat.type === 'satellite';
    if (filter === 'debris')     return sat.type === 'debris';
    return true;
  });

  // Sort: threatened first, then by name
  const sorted = [...filtered].sort((a, b) => {
    const wa = { HIGH: 3, MEDIUM: 2, LOW: 1, NOMINAL: 0 }[threatMap[a.id]?.risk || 'NOMINAL'];
    const wb = { HIGH: 3, MEDIUM: 2, LOW: 1, NOMINAL: 0 }[threatMap[b.id]?.risk || 'NOMINAL'];
    return wb - wa || a.name.localeCompare(b.name);
  });

  const counts = {
    all:        satellites.length,
    threatened: satellites.filter(s => threatMap[s.id]?.count > 0).length,
    satellite:  satellites.filter(s => s.type === 'satellite').length,
    debris:     satellites.filter(s => s.type === 'debris').length,
  };

  return (
    <div className="panel sat-inventory-panel">
      {/* Header */}
      <div className="panel-header" style={{ flexShrink: 0 }}>
        <h2>
          <Satellite size={14} color="var(--c-nominal)" />
          Tracked Objects Catalogue
        </h2>
        <span className="panel-badge">{satellites.length} OBJ</span>
      </div>

      {/* Filter chips */}
      <div className="sat-filter-row">
        {[
          { key: 'all',        label: `All (${counts.all})` },
          { key: 'threatened', label: `⚠ Threats (${counts.threatened})` },
          { key: 'satellite',  label: `Satellites (${counts.satellite})` },
          { key: 'debris',     label: `Debris (${counts.debris})` },
        ].map(chip => (
          <button
            key={chip.key}
            className={`sat-chip ${filter === chip.key ? 'active' : ''}`}
            onClick={() => setFilter(chip.key)}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Scrollable list */}
      <div className="sat-catalogue-list scrolling-list">
        {sorted.length === 0 ? (
          <div className="feed-empty-state">No objects match the current filter.</div>
        ) : (
          sorted.map(sat => {
            const threat = threatMap[sat.id] || { risk: 'NOMINAL', count: 0 };
            const riskColor = RISK_COLOR[threat.risk];
            const isSelected = selectedSatId === sat.id;
            const isExpanded = expanded === sat.id;
            const conjEvents = events.filter(
              e => e.primaryObject.id === sat.id || e.secondaryObject.id === sat.id
            );

            return (
              <div
                key={sat.id}
                className={`sat-cat-card ${isSelected ? 'selected' : ''} ${threat.risk.toLowerCase()}`}
                onClick={() => {
                  onSelectSat(sat.id);
                  setExpanded(isExpanded ? null : sat.id);
                }}
              >
                {/* Left risk stripe */}
                <div className="sat-risk-stripe" style={{ background: riskColor }} />

                <div className="sat-cat-body">
                  {/* Row 1: NORAD + risk badge + expand */}
                  <div className="sat-cat-row-top">
                    <span className="sat-norad">#{sat.id}</span>
                    <span className="sat-risk-chip" style={{ color: riskColor, borderColor: riskColor }}>
                      {RISK_LABEL[threat.risk]}
                    </span>
                    <span className="sat-expand-btn">
                      {isExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                    </span>
                  </div>

                  {/* Row 2: Name + pulse icon */}
                  <div className="sat-cat-row-name">
                    {threat.risk !== 'NOMINAL' ? (
                      <AlertTriangle
                        size={11}
                        className="sat-pulse-icon"
                        style={{ color: riskColor, flexShrink: 0 }}
                      />
                    ) : (
                      <Radio
                        size={11}
                        style={{ color: 'var(--t-secondary)', flexShrink: 0 }}
                      />
                    )}
                    <strong className="sat-cat-name">{sat.name}</strong>
                  </div>

                  {/* Row 3: type + conjunction count */}
                  <div className="sat-cat-row-meta">
                    <span className="sat-type-tag">{sat.type.toUpperCase()}</span>
                    {threat.count > 0 && (
                      <span className="sat-conj-count" style={{ color: riskColor }}>
                        <Activity size={9} /> {threat.count} active conjunction{threat.count > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>

                  {/* Expanded: show each conjunction */}
                  {isExpanded && conjEvents.length > 0 && (
                    <div className="sat-conj-details">
                      {conjEvents.map(ev => {
                        const partner = ev.primaryObject.id === sat.id
                          ? ev.secondaryObject
                          : ev.primaryObject;
                        return (
                          <div key={ev.id} className="sat-conj-row">
                            <span className="conj-partner">↔ {partner.name}</span>
                            <span className="conj-miss">{ev.missDistanceKm.toFixed(2)} km</span>
                            <span className="conj-tca">{ev.timeToTcaHours.toFixed(1)}h</span>
                            <span className="conj-prob" style={{ color: RISK_COLOR[ev.riskClassification] }}>
                              {(ev.predictedProbabilityOfCollision * 100).toFixed(4)}%
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
