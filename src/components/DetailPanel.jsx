import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { BarChart2, ShieldCheck, Radio, AlertTriangle } from 'lucide-react';

export default function DetailPanel({ activeEvent }) {
  if (!activeEvent) {
    return (
      <div className="panel detail-panel">
        <div className="panel-header">
          <h2>
            <BarChart2 size={14} color="var(--c-nominal)" />
            Conjunction Details & Dynamics
          </h2>
        </div>
        <div className="detail-empty-state">
          Select an active conjunction event from the feed to view refined trajectory and probability history.
        </div>
      </div>
    );
  }

  // Format history for charting
  const chartData = (activeEvent.history || []).map((prob, idx) => ({
    updateNum: `Obs #${idx + 1}`,
    probability: prob * 100 // convert to percentage
  }));

  const getRiskColor = (risk) => {
    switch (risk?.toUpperCase()) {
      case 'HIGH': return 'var(--c-critical)';
      case 'MEDIUM': return 'var(--c-warn)';
      case 'LOW':
      default:
        return 'var(--c-nominal)';
    }
  };

  const riskColor = getRiskColor(activeEvent.riskClassification);

  // Recommendations mapping
  const getActionRecommendation = (risk) => {
    switch (risk?.toUpperCase()) {
      case 'HIGH':
        return {
          title: 'IMMEDIATE MANEUVER PLANNING RECOMMENDED',
          description: 'Collision probability exceeds safety thresholds. Escalate to maneuver command for orbital trajectory recalculation and active collision avoidance execution planning.',
          alertType: 'critical'
        };
      case 'MEDIUM':
        return {
          title: 'ELEVATED MONITORING & SENSITIVITY TIER',
          description: 'Conjunction probability is hovering in the caution region. Ground sensor tracking should be scheduled for additional telemetry passes within 6 hours. Prepare maneuver plans.',
          alertType: 'warning'
        };
      case 'LOW':
      default:
        return {
          title: 'ROUTINE SPACE TRACKING PROPAGATION',
          description: 'Risk metrics remain below security thresholds. Object coordinates will continue to be propagated automatically by the SGP4 routine during standard passes.',
          alertType: 'nominal'
        };
    }
  };

  const rec = getActionRecommendation(activeEvent.riskClassification);

  return (
    <div className="panel detail-panel">
      <div className="panel-header">
        <h2>
          <BarChart2 size={14} color="var(--c-nominal)" />
          Conjunction Details & Dynamics // {activeEvent.id}
        </h2>
      </div>

      <div className="detail-meta-grid">
        <div className="meta-box">
          <span className="meta-lbl">Primary Object</span>
          <span className="meta-val">{activeEvent.primaryObject.name}</span>
          <span className="meta-sub">NORAD ID: {activeEvent.primaryObject.id}</span>
        </div>
        <div className="meta-box">
          <span className="meta-lbl">Secondary Object</span>
          <span className="meta-val">{activeEvent.secondaryObject.name}</span>
          <span className="meta-sub">NORAD ID: {activeEvent.secondaryObject.id}</span>
        </div>
      </div>

      {/* Recharts Area Chart */}
      <div className="detail-chart-wrapper">
        <div className="chart-title-bar">
          <span className="chart-lbl">Collision Probability Refinement History</span>
          <span className="chart-val-current" style={{ color: riskColor }}>
            Current: {(activeEvent.predictedProbabilityOfCollision * 100).toFixed(5)}%
          </span>
        </div>
        <div style={{ width: '100%', height: 160 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="probGlow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={riskColor} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={riskColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis 
                dataKey="updateNum" 
                tick={{ fill: 'var(--t-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }} 
                axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              />
              <YAxis 
                tick={{ fill: 'var(--t-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }} 
                axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
                tickFormatter={(v) => `${v.toFixed(3)}%`}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-mid)',
                  borderRadius: '4px',
                  color: 'var(--t-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10px'
                }}
                labelStyle={{ color: 'var(--t-secondary)', fontWeight: 'bold' }}
                formatter={(v) => [`${v.toFixed(5)}%`, 'Probability']}
              />
              <Area 
                type="monotone" 
                dataKey="probability" 
                stroke={riskColor} 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#probGlow)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Technical Readout */}
      <div className="technical-readout">
        <div className="readout-title">TELEMETRY DATA FIELD</div>
        <div className="readout-grid">
          <div className="readout-col">
            <div className="readout-item">
              <span className="lbl">Relative Velocity</span>
              <span className="val">{activeEvent.relativeVelocityKmS.toFixed(3)} km/s</span>
            </div>
            <div className="readout-item">
              <span className="lbl">Miss Distance</span>
              <span className="val">{activeEvent.missDistanceKm.toFixed(4)} km</span>
            </div>
          </div>
          <div className="readout-col">
            <div className="readout-item">
              <span className="lbl">Time to closest approach</span>
              <span className="val">{activeEvent.timeToTcaHours.toFixed(2)} hours</span>
            </div>
            <div className="readout-item">
              <span className="lbl">Tracking updates count</span>
              <span className="val">{activeEvent.history.length} refinements</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Recommendation Alert Block */}
      <div className={`recommendation-alert ${rec.alertType}`}>
        <div className="rec-header">
          {rec.alertType === 'critical' ? (
            <AlertTriangle size={14} className="rec-icon animate-pulse" />
          ) : rec.alertType === 'warning' ? (
            <Radio size={14} className="rec-icon" />
          ) : (
            <ShieldCheck size={14} className="rec-icon" />
          )}
          <span className="rec-title">{rec.title}</span>
        </div>
        <p className="rec-desc">{rec.description}</p>
      </div>
    </div>
  );
}
