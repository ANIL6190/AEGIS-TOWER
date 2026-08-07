import React, { useState, useEffect } from 'react';
import { ShieldCheck, Info, Activity, Target, TrendingUp, Database, RefreshCw } from 'lucide-react';

/**
 * ModelConfidence — displays live model accuracy metrics fetched from /api/status.
 * Falls back to static calibration info when backend is offline.
 */
export default function ModelConfidence() {
  const [metrics, setMetrics] = useState(null);
  const [status, setStatus]   = useState('loading'); // 'loading' | 'active' | 'offline'
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/status', { signal: AbortSignal.timeout(4000) });
      if (!res.ok) throw new Error('bad response');
      const data = await res.json();
      if (data.model_loaded && data.metrics) {
        setMetrics(data.metrics);
        setStatus('active');
        setLastRefresh(new Date());
      } else {
        setStatus('offline');
      }
    } catch {
      setStatus('offline');
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30 s
    return () => clearInterval(interval);
  }, []);

  const MetricRow = ({ icon: Icon, label, value, unit, color }) => (
    <div className="metric-row">
      <div className="metric-icon-wrap">
        <Icon size={11} color={color || 'var(--c-nominal)'} />
      </div>
      <span className="metric-label">{label}</span>
      <span className="metric-value" style={{ color: color || 'var(--t-bright)' }}>
        {value}<span className="metric-unit"> {unit}</span>
      </span>
    </div>
  );

  const R2Bar = ({ label, value }) => {
    const pct = Math.max(0, Math.min(100, (value * 100)));
    const color = pct >= 80 ? 'var(--c-nominal)' : pct >= 50 ? 'var(--c-warn)' : 'var(--c-critical)';
    return (
      <div className="r2-bar-row">
        <span className="r2-label">{label}</span>
        <div className="r2-track">
          <div className="r2-fill" style={{ width: `${pct}%`, background: color }} />
        </div>
        <span className="r2-val" style={{ color }}>{pct.toFixed(1)}%</span>
      </div>
    );
  };

  return (
    <div className="panel model-confidence-panel">
      <div className="panel-header" style={{ flexShrink: 0 }}>
        <h2>
          <ShieldCheck size={14} color="var(--c-nominal)" />
          ML Model Diagnostics
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            className="panel-badge"
            style={{
              background: status === 'active' ? 'rgba(0,229,255,0.12)' : 'rgba(255,23,68,0.12)',
              borderColor: status === 'active' ? 'var(--c-nominal)' : 'var(--c-critical)',
              color: status === 'active' ? 'var(--c-nominal)' : 'var(--c-critical)',
            }}
          >
            {status === 'loading' ? 'LOADING…' : status === 'active' ? '● LIVE' : '✕ OFFLINE'}
          </span>
          <button
            onClick={fetchStatus}
            title="Refresh metrics"
            style={{ background: 'none', border: 'none', color: 'var(--t-secondary)', cursor: 'pointer', padding: '2px' }}
          >
            <RefreshCw size={11} />
          </button>
        </div>
      </div>

      <div className="model-confidence-body">
        {status === 'active' && metrics ? (
          <>
            {/* Training info */}
            <div className="model-info-strip">
              <Database size={10} />
              <span>Trained on <strong>{metrics.num_samples}</strong> real SOCRATES conjunction records</span>
            </div>

            {/* R² Score Bars */}
            <div className="model-section-title">Model R² Scores (Higher = Better Fit)</div>
            <div className="r2-bars">
              <R2Bar label="Miss Distance" value={metrics.range_r2} />
              <R2Bar label="Rel. Velocity" value={metrics.speed_r2} />
              <R2Bar label="Collision Prob" value={metrics.prob_r2} />
            </div>

            {/* MAE metrics */}
            <div className="model-section-title" style={{ marginTop: '8px' }}>Mean Absolute Errors</div>
            <div className="metrics-grid">
              <MetricRow
                icon={Target}
                label="Miss Distance MAE"
                value={metrics.range_mae.toFixed(4)}
                unit="km"
                color="var(--c-nominal)"
              />
              <MetricRow
                icon={TrendingUp}
                label="Rel. Velocity MAE"
                value={metrics.speed_mae.toFixed(4)}
                unit="km/s"
                color="var(--c-warn)"
              />
              <MetricRow
                icon={Activity}
                label="Collision Prob MAE"
                value={metrics.prob_mae.toExponential(3)}
                unit=""
                color="var(--c-critical)"
              />
            </div>

            {/* Refresh time */}
            {lastRefresh && (
              <div className="calibration-note" style={{ marginTop: '6px' }}>
                <Info size={9} style={{ flexShrink: 0 }} />
                <span>Last refreshed: {lastRefresh.toLocaleTimeString()}</span>
              </div>
            )}
          </>
        ) : status === 'offline' ? (
          <>
            <p className="confidence-main">
              <strong>AEGIS-ML SGP4-Net v3.2.0:</strong> Backend offline — running in simulation mode.
              Start the Flask server to enable live ML predictions.
            </p>
            <div className="calibration-note">
              <Info size={11} style={{ flexShrink: 0, marginTop: '1px' }} />
              <span>Risk tiers are scaled to guarantee a minimum 24-hour lead time for any P(c) ≥ 10⁻⁵.</span>
            </div>
          </>
        ) : (
          <div className="feed-empty-state" style={{ padding: '12px 0' }}>Connecting to ML engine…</div>
        )}
      </div>
    </div>
  );
}
