import React from 'react';
import { Shield, AlertTriangle, Activity, Clock, Trash2 } from 'lucide-react';

export default function RiskDashboard({ stats }) {
  const {
    totalObjects = 16,
    activeEvents = 0,
    lowRisk = 0,
    mediumRisk = 0,
    highRisk = 0,
    avgLeadTime = 42.8, // in hours
    falsePositiveRate = 12.5 // in percent
  } = stats;

  return (
    <div className="metrics-dashboard">
      {/* Metric Card: Total Tracked */}
      <div className="metric-card">
        <div className="metric-icon cyan">
          <Activity size={16} />
        </div>
        <div className="metric-content">
          <span className="metric-label">Objects Tracked</span>
          <span className="metric-value text-glow-cyan">{totalObjects}</span>
        </div>
      </div>

      {/* Metric Card: Active Conjunctions */}
      <div className={`metric-card ${activeEvents > 0 ? 'warning-card' : ''}`}>
        <div className="metric-icon amber">
          <AlertTriangle size={16} />
        </div>
        <div className="metric-content">
          <span className="metric-label">Active Events</span>
          <span className="metric-value text-glow-amber">{activeEvents}</span>
        </div>
      </div>

      {/* Metric Card: Risk Tiers */}
      <div className={`metric-card ${highRisk > 0 ? 'danger-card' : mediumRisk > 0 ? 'warning-card' : ''}`}>
        <div className="metric-icon">
          <Shield size={16} color="var(--c-nominal)" />
        </div>
        <div className="metric-content">
          <span className="metric-label">Events by Tier</span>
          <div className="risk-tiers-split">
            <span className="risk-badge low" title="Low Risk">{lowRisk} L</span>
            <span className="risk-badge med" title="Medium Risk">{mediumRisk} M</span>
            <span className="risk-badge high" title="High Risk">{highRisk} H</span>
          </div>
        </div>
      </div>

      {/* Metric Card: Lead Time */}
      <div className="metric-card">
        <div className="metric-icon info">
          <Clock size={16} color="var(--c-nominal)" />
        </div>
        <div className="metric-content">
          <span className="metric-label">Avg Lead Time</span>
          <span className="metric-value">{avgLeadTime.toFixed(1)}h</span>
        </div>
      </div>

      {/* Metric Card: False Positive Rate */}
      <div className="metric-card">
        <div className="metric-icon dismiss">
          <Trash2 size={16} color="var(--t-secondary)" />
        </div>
        <div className="metric-content">
          <span className="metric-label">FP Dismiss Rate</span>
          <span className="metric-value">{falsePositiveRate.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
