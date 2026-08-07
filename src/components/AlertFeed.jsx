import React from 'react';
import { ShieldAlert, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

export default function AlertFeed({ 
  events, 
  selectedEventId, 
  onSelectEvent
}) {
  // Sort events: High risk at the top, then Medium, then Low
  const sortedEvents = [...events].sort((a, b) => {
    const riskWeight = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    if (riskWeight[a.riskClassification] !== riskWeight[b.riskClassification]) {
      return riskWeight[b.riskClassification] - riskWeight[a.riskClassification];
    }
    return b.predictedProbabilityOfCollision - a.predictedProbabilityOfCollision;
  });

  const getTrendIcon = (trend) => {
    switch (trend?.toLowerCase()) {
      case 'increasing':
      case 'rising':
        return <ArrowUpRight size={14} className="trend-icon rising" />;
      case 'decreasing':
      case 'falling':
        return <ArrowDownRight size={14} className="trend-icon falling" />;
      case 'stable':
      default:
        return <Minus size={14} className="trend-icon stable" />;
    }
  };

  const getRiskColor = (risk) => {
    switch (risk?.toUpperCase()) {
      case 'HIGH': return 'var(--c-critical)';
      case 'MEDIUM': return 'var(--c-warn)';
      case 'LOW':
      default:
        return 'var(--c-nominal)';
    }
  };

  return (
    <div className="panel alert-feed-panel">
      {/* Panel Header */}
      <div className="panel-header" style={{ flexShrink: 0 }}>
        <h2>
          <ShieldAlert size={14} color="var(--c-critical)" />
          Conjunction Threat Stream
        </h2>
        <span className="panel-badge">{events.length} ACTIVE</span>
      </div>

      <div className="event-list scrolling-list">
        {events.length === 0 ? (
          <div className="feed-empty-state">
            Scanning orbital sectors. No conjunctions currently registered.
          </div>
        ) : (
          sortedEvents.map((evt) => {
            const isSelected = selectedEventId === evt.id;
            const riskColor = getRiskColor(evt.riskClassification);

            return (
              <div
                key={evt.id}
                className={`event-card risk-${evt.riskClassification.toLowerCase()} ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectEvent(evt.id)}
              >
                {/* Status Bar Indicator */}
                <div className="event-status-bar" style={{ background: riskColor }} />

                <div className="event-card-body">
                  <div className="event-row-top">
                    <span className="event-id-tag">{evt.id}</span>
                    <span className="event-risk-badge" style={{ color: riskColor, borderColor: riskColor }}>
                      {evt.riskClassification} RISK
                    </span>
                  </div>

                  <div className="event-objects-names">
                    <div className="obj-name primary-obj">
                      <span className="obj-label">Primary</span>
                      <strong>{evt.primaryObject.name}</strong>
                    </div>
                    <div className="obj-divider">↔</div>
                    <div className="obj-name secondary-obj">
                      <span className="obj-label">Secondary</span>
                      <strong>{evt.secondaryObject.name}</strong>
                    </div>
                  </div>

                  <div className="event-stats-grid">
                    <div className="evt-stat">
                      <span className="stat-label">TCA Countdown</span>
                      <span className="stat-value">{evt.timeToTcaHours.toFixed(1)}h</span>
                    </div>
                    <div className="evt-stat">
                      <span className="stat-label">Miss Distance</span>
                      <span className="stat-value">{evt.missDistanceKm.toFixed(2)} km</span>
                    </div>
                    <div className="evt-stat">
                      <span className="stat-label">Rel Velocity</span>
                      <span className="stat-value">{evt.relativeVelocityKmS.toFixed(1)} km/s</span>
                    </div>
                    <div className="evt-stat">
                      <span className="stat-label">Collision Prob</span>
                      <span className="stat-value text-glow" style={{ color: riskColor }}>
                        {(evt.predictedProbabilityOfCollision * 100).toFixed(4)}%
                      </span>
                    </div>
                  </div>

                  <div className="event-row-bottom">
                    <div className="trend-block">
                      <span className="trend-lbl">Trend</span>
                      <span className="trend-wrapper">
                        {getTrendIcon(evt.trend)}
                        <span className={`trend-text ${evt.trend}`}>{evt.trend}</span>
                      </span>
                    </div>
                    <div className="confidence-block">
                      <span className="confidence-lbl">AI Confidence</span>
                      <span className="confidence-val">{(evt.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
