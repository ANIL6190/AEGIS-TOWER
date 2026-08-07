import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Shield, Play, Pause, Zap, RotateCcw } from 'lucide-react';
import OrbitScene from './components/OrbitScene';
import AlertFeed from './components/AlertFeed';
import DetailPanel from './components/DetailPanel';
import OperatorPanel from './components/OperatorPanel';
import RiskDashboard from './components/RiskDashboard';
import ModelConfidence from './components/ModelConfidence';
import SatelliteInventory from './components/SatelliteInventory';
import { TLE_DATA } from './data/satellites';
import './App.css';

// Pre-defined pairings for close approach simulation
const SIMULATED_CONJUNCTION_PAIRS = [
  { pId: "58214", sId: "49271", pBase: 0.00035, pathTrend: 'increasing' }, // SENTINEL-DEMO-SAT-1 and DEBRIS FRAGMENT-B
  { pId: "35421", sId: "35422", pBase: 0.00002, pathTrend: 'decreasing' }, // AEROSAT-9 and DEBRIS-C (METEOR)
  { pId: "25544", sId: "36123", pBase: 0.000004, pathTrend: 'stable' },    // ISS and COSMOS DEBRIS
  { pId: "48274", sId: "34124", pBase: 0.00007, pathTrend: 'increasing' },  // TIANGONG STATION and IRIDIUM DEBRIS
  { pId: "40697", sId: "27386", pBase: 0.00001, pathTrend: 'decreasing' }  // SENTINEL-2A and ENVISAT DEBRIS
];

export default function App() {
  // ── Simulation clock / state ──────────────────────────────────────────
  const [simTime, setSimTime] = useState(() => new Date(2026, 7, 6, 12, 0, 0)); // Match current system date frame: Aug 6, 2026
  const [autoPlay, setAutoPlay] = useState(true);
  const [timeMultiplier, setTimeMultiplier] = useState(300); // 1 real second = 5 minutes of simulated orbit time

  // List of active conjunction alerts
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  
  // Selected satellite ID in the 3D scene
  const [selectedSatId, setSelectedSatId] = useState(null);

  // Operator choice logs
  const [actionLog, setActionLog] = useState([]);
  
  // General Stats
  const [dismissCount, setDismissCount] = useState(0);
  const [totalActioned, setTotalActioned] = useState(0);

  // Backend connection states
  const [backendActive, setBackendActive] = useState(false);
  const [satellites, setSatellites] = useState(TLE_DATA);
  const [showHighRiskPopup, setShowHighRiskPopup] = useState(false);
  const [highRiskConjunction, setHighRiskConjunction] = useState(null);
  // Use a ref (not state) to track acknowledged IDs so the polling interval
  // is not re-created every time the user acknowledges a conjunction.
  // This is what was causing the popup to appear/disappear like a blinking LED.
  const acknowledgedRef = useRef(new Set());
  const popupShownRef  = useRef(false); // True while a popup is visible

  // Map probability to Risk Tiers
  const getRiskTier = (p) => {
    if (p >= 0.001) return 'HIGH';      // >= 1 in 1000
    if (p >= 0.00005) return 'MEDIUM';  // 5 in 100,000
    return 'LOW';
  };

  // Poll backend for conjunction events.
  // The interval is created ONCE on mount and never recreated.
  // We use refs to avoid stale closures without triggering re-renders.
  useEffect(() => {
    const fetchConjunctions = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/conjunctions');
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        setEvents(data);
        setBackendActive(true);

        // Only trigger popup for the FIRST new HIGH-risk conjunction that hasn't
        // been acknowledged yet — and only if no popup is already visible.
        if (!popupShownRef.current) {
          const highRisk = data.find(
            e => e.riskClassification === 'HIGH' && !acknowledgedRef.current.has(e.id)
          );
          if (highRisk) {
            setHighRiskConjunction(highRisk);
            setShowHighRiskPopup(true);
            popupShownRef.current = true;
          }
        }
      } catch {
        // Backend offline — fallback simulation handles events
        setBackendActive(false);
      }
    };

    fetchConjunctions();
    const interval = setInterval(fetchConjunctions, 15000); // Poll every 15 seconds
    return () => clearInterval(interval);
  }, []); // Empty deps — interval is stable, refs carry the mutable state

  // Fetch satellites from backend
  useEffect(() => {
    if (backendActive) {
      fetch('http://localhost:5000/api/satellites')
        .then(res => res.json())
        .then(data => setSatellites(data))
        .catch(err => console.error("Error fetching satellites from backend:", err));
    } else {
      setSatellites(TLE_DATA);
    }
  }, [backendActive]);

  // Generate initial simulated events if backend is not active after 1.5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!backendActive && events.length === 0) {
        const initialEvents = SIMULATED_CONJUNCTION_PAIRS.map((pair, idx) => {
          const pObj = TLE_DATA.find(s => s.id === pair.pId);
          const sObj = TLE_DATA.find(s => s.id === pair.sId);
          const startTcaHours = 40.0 + idx * 8.0;
          const prob = pair.pBase;
          const risk = getRiskTier(prob);

          return {
            id: `CA-2026-08-06-000${idx + 1}`,
            primaryObject: { id: pObj.id, name: pObj.name },
            secondaryObject: { id: sObj.id, name: sObj.name },
            timeToTcaHours: startTcaHours,
            missDistanceKm: 0.8 + Math.random() * 6.0,
            relativeVelocityKmS: 6.5 + Math.random() * 8.0,
            predictedProbabilityOfCollision: prob,
            riskClassification: risk,
            trend: 'stable',
            confidence: 0.72 + Math.random() * 0.22,
            history: [prob * 0.6, prob * 0.8, prob],
            pathTrend: pair.pathTrend
          };
        });

        setEvents(initialEvents);
        if (initialEvents.length > 0) {
          setSelectedEventId(initialEvents[0].id);
        }
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [backendActive]);

  // Callback to select a satellite in the 3D scene
  const handleSelectSat = useCallback((satId) => {
    setSelectedSatId(satId);
    // Find if there's an active event involving this satellite
    const evt = events.find(e => e.primaryObject.id === satId || e.secondaryObject.id === satId);
    if (evt) {
      setSelectedEventId(evt.id);
    }
  }, [events]);

  // Synchronize 3D satellite click to details panel
  const handleSelectEvent = useCallback((eventId) => {
    setSelectedEventId(eventId);
    const evt = events.find(e => e.id === eventId);
    if (evt) {
      setSelectedSatId(evt.primaryObject.id);
    }
  }, [events]);

  // ── Step simulation logic ──────────────────────────────────────────────
  const tickSimulation = useCallback((secondsToAdvance) => {
    // 1. Update Clock
    setSimTime(prev => new Date(prev.getTime() + secondsToAdvance * 1000));

    // 2. Refine Conjunction Events
    setEvents(prevEvents => {
      const hoursToSubtract = secondsToAdvance / 3600.0;
      
      return prevEvents.map(evt => {
        // Subtract TCA countdown
        const nextTca = Math.max(0, evt.timeToTcaHours - hoursToSubtract);

        // If conjunction is in the past, resolve it safely
        if (nextTca <= 0) {
          // Resolve event
          return null;
        }

        // If backend is active, the backend controls predictions. We only advance TCA hours locally.
        if (backendActive) {
          return {
            ...evt,
            timeToTcaHours: nextTca
          };
        }

        // Random tracking updates refinement (every once in a while)
        const shouldRefine = Math.random() < 0.12; // ~12% chance per tick
        if (!shouldRefine) {
          return {
            ...evt,
            timeToTcaHours: nextTca
          };
        }

        // Calculate evolving probability
        let changeMultiplier = 1.0;
        if (evt.pathTrend === 'increasing') {
          changeMultiplier = 1.0 + Math.random() * 0.35;
        } else if (evt.pathTrend === 'decreasing') {
          changeMultiplier = 0.6 + Math.random() * 0.35;
        } else {
          changeMultiplier = 0.85 + Math.random() * 0.3;
        }

        // Apply new probability
        const newProb = Math.max(0.000001, Math.min(0.015, evt.predictedProbabilityOfCollision * changeMultiplier));
        const newRisk = getRiskTier(newProb);
        
        // Determine trend label
        let currentTrend = 'stable';
        if (newProb > evt.predictedProbabilityOfCollision * 1.05) currentTrend = 'increasing';
        else if (newProb < evt.predictedProbabilityOfCollision * 0.95) currentTrend = 'decreasing';

        // Add to history
        const updatedHistory = [...evt.history, newProb].slice(-10); // Keep last 10 points

        // Miss distance also refines slightly
        const newMissDistance = Math.max(0.05, evt.missDistanceKm + (Math.random() - 0.5) * 0.1);

        return {
          ...evt,
          timeToTcaHours: nextTca,
          missDistanceKm: newMissDistance,
          predictedProbabilityOfCollision: newProb,
          riskClassification: newRisk,
          trend: currentTrend,
          history: updatedHistory
        };
      }).filter(Boolean); // Clear completed events
    });
  }, [backendActive]);

  // ── Clock effect ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(() => {
      // Advance simulation clock by multiplier
      const secondsToAdvance = timeMultiplier / 5; // run 5 times a second for smoother clock ticks
      tickSimulation(secondsToAdvance);
    }, 200);

    return () => clearInterval(interval);
  }, [autoPlay, timeMultiplier, tickSimulation]);

  // ── Operator Actions ───────────────────────────────────────────────────
  const handleOperatorAction = useCallback((eventId, actionType, actionText) => {
    // Record log
    const timestampStr = new Date().toLocaleTimeString();
    
    setActionLog(prev => [
      ...prev,
      {
        time: timestampStr,
        eventId: eventId,
        type: actionType,
        actionText: actionText
      }
    ]);

    setTotalActioned(prev => prev + 1);
    if (actionType === 'dismiss') {
      setDismissCount(prev => prev + 1);
      // Remove alert from feed
      setEvents(prev => prev.filter(e => e.id !== eventId));
      setSelectedEventId(null);
    } else if (actionType === 'escalate') {
      // Alter the trajectory in-simulation (probability drops in future updates due to maneuver planning)
      setEvents(prev => prev.map(e => {
        if (e.id === eventId) {
          return {
            ...e,
            pathTrend: 'decreasing', // Will start trending down
            trend: 'decreasing'
          };
        }
        return e;
      }));
    }
  }, []);

  const handleResetSimulation = () => {
    // Reset clock and alerts
    setSimTime(new Date(2026, 7, 6, 12, 0, 0));
    setActionLog([]);
    setDismissCount(0);
    setTotalActioned(0);

    const resetEvents = SIMULATED_CONJUNCTION_PAIRS.map((pair, idx) => {
      const pObj = TLE_DATA.find(s => s.id === pair.pId);
      const sObj = TLE_DATA.find(s => s.id === pair.sId);
      return {
        id: `CA-2026-08-06-000${idx + 1}`,
        primaryObject: { id: pObj.id, name: pObj.name },
        secondaryObject: { id: sObj.id, name: sObj.name },
        timeToTcaHours: 40.0 + idx * 8.0,
        missDistanceKm: 0.8 + Math.random() * 6.0,
        relativeVelocityKmS: 6.5 + Math.random() * 8.0,
        predictedProbabilityOfCollision: pair.pBase,
        riskClassification: getRiskTier(pair.pBase),
        trend: 'stable',
        confidence: 0.72 + Math.random() * 0.22,
        history: [pair.pBase * 0.6, pair.pBase * 0.8, pair.pBase],
        pathTrend: pair.pathTrend
      };
    });

    setEvents(resetEvents);
    if (resetEvents.length > 0) {
      setSelectedEventId(resetEvents[0].id);
      setSelectedSatId(resetEvents[0].primaryObject.id);
    }
  };

  const activeEvent = events.find(e => e.id === selectedEventId);

  // Compute stats counters
  const lowCount = events.filter(e => e.riskClassification === 'LOW').length;
  const medCount = events.filter(e => e.riskClassification === 'MEDIUM').length;
  const highCount = events.filter(e => e.riskClassification === 'HIGH').length;

  const dashboardStats = {
    totalObjects: TLE_DATA.length,
    activeEvents: events.length,
    lowRisk: lowCount,
    mediumRisk: medCount,
    highRisk: highCount,
    avgLeadTime: events.length > 0 ? (events.reduce((sum, e) => sum + e.timeToTcaHours, 0) / events.length) : 0,
    falsePositiveRate: totalActioned > 0 ? (dismissCount / totalActioned * 100) : 0
  };

  return (
    <div className="app-container">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <header className="header">
        <div className="logo-section">
          <Shield size={18} color="var(--c-nominal)" className="animate-pulse" />
          <h1>AEGIS TOWER</h1>
          <span>AI-Powered Space Situational Awareness Console</span>
        </div>

        {/* Global Controls */}
        <div className="status-indicator">
          {/* Simulation multiplier */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginRight: '4px' }}>
            <span style={{ fontSize: '0.62rem', color: 'var(--t-secondary)' }}>TIME MULT:</span>
            <select
              value={timeMultiplier}
              onChange={e => setTimeMultiplier(Number(e.target.value))}
              className="status-select"
              title="Simulation speed multiplier"
            >
              <option value={60}>60x (1m/s)</option>
              <option value={300}>300x (5m/s)</option>
              <option value={900}>900x (15m/s)</option>
              <option value={1800}>1800x (30m/s)</option>
            </select>
          </div>

          {/* Toggle Auto-Play */}
          <button
            className={`btn ${autoPlay ? 'btn-danger' : 'btn-primary'}`}
            onClick={() => setAutoPlay(prev => !prev)}
            style={{ padding: '4px 8px' }}
          >
            {autoPlay ? <Pause size={11} /> : <Play size={11} />}
            {autoPlay ? 'Pause Sim' : 'Resume Sim'}
          </button>

          {/* Single Step */}
          <button
            className="btn"
            onClick={() => tickSimulation(300)}
            disabled={autoPlay}
            style={{ padding: '4px 8px' }}
          >
            <Zap size={11} />
            Step +5m
          </button>

          {/* Reset */}
          <button
            className="btn"
            onClick={handleResetSimulation}
            style={{ padding: '4px 8px' }}
          >
            <RotateCcw size={11} />
            Reset
          </button>

          <div style={{ width: '1px', height: '16px', background: 'var(--border-dim)', margin: '0 4px' }} />
          <div className="status-dot" />
          <span style={{ color: 'var(--t-bright)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
            {simTime.toLocaleDateString()} {simTime.toLocaleTimeString()}
          </span>
        </div>
      </header>

      {/* ── Main Content Area ────────────────────────────────────────── */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, padding: 'var(--gap)', overflow: 'hidden' }}>
        {/* Upper Dashboard Metrics */}
        <RiskDashboard stats={dashboardStats} />

        {/* Lower Console Layout */}
        <div className="main-content" style={{ flex: 1, padding: 0 }}>
          {/* Left panel: Alert Feed & Model Indicator */}
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--gap)' }}>
            <AlertFeed
              events={events}
              selectedEventId={selectedEventId}
              onSelectEvent={handleSelectEvent}
              satellites={satellites}
              selectedSatId={selectedSatId}
              onSelectSat={handleSelectSat}
            />
            <ModelConfidence />
          </div>

          {/* Center panel: 3D Visualization */}
          <div className="panel" style={{ height: '100%', position: 'relative', overflow: 'hidden', padding: 0 }}>
            <div style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 10, display: 'flex', alignItems: 'center', gap: '8px', pointerEvents: 'none' }}>
              <span style={{ fontSize: '0.68rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', fontFamily: 'var(--font-mono)', color: 'var(--t-secondary)' }}>
                Tactical 3D Conjunction Hologram
              </span>
              {backendActive && (
                <span className="live-badge animate-pulse" style={{ fontSize: '0.58rem', background: 'rgba(0,229,255,0.15)', border: '1px solid var(--c-nominal)', color: 'var(--c-nominal)', padding: '2px 6px', borderRadius: '2px', fontFamily: 'var(--font-mono)' }}>
                  LIVE ML PIPELINE
                </span>
              )}
            </div>
            <OrbitScene
              satellites={satellites}
              simTime={simTime}
              conjunctionEvents={events}
              selectedSatId={selectedSatId}
              onSelectSat={handleSelectSat}
            />
          </div>

          {/* Column 3: Dedicated Tracked Objects catalogue inventory list */}
          <SatelliteInventory
            satellites={satellites}
            events={events}
            selectedSatId={selectedSatId}
            onSelectSat={handleSelectSat}
          />

          {/* Column 4: Details & Action deck */}
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--gap)' }}>
            <DetailPanel activeEvent={activeEvent} />
            <OperatorPanel
              activeEvent={activeEvent}
              onAction={handleOperatorAction}
              actionLog={actionLog}
            />
          </div>
        </div>
      </div>

      {/* ── High Risk Conjunction Warning Modal ── */}
      {showHighRiskPopup && highRiskConjunction && (
        <div className="hud-modal-overlay">
          <div className="hud-modal danger-border">
            <div className="hud-modal-header">
              <span className="modal-title text-glow-red animate-pulse">⚠ CRITICAL CONJUNCTION DETECTED</span>
              <button className="close-btn" onClick={() => {
                acknowledgedRef.current.add(highRiskConjunction.id);
                popupShownRef.current = false;
                setShowHighRiskPopup(false);
              }}>×</button>
            </div>
            <div className="hud-modal-body">
              <p className="conjunction-warning-text">
                Imminent orbital intersection predicted between <strong>{highRiskConjunction.primaryObject.name}</strong> and <strong>{highRiskConjunction.secondaryObject.name}</strong>.
              </p>
              <div className="conjunction-stats">
                <div className="stat-box">
                  <span className="label">Collision Probability</span>
                  <span className="val text-glow-red">{(highRiskConjunction.predictedProbabilityOfCollision * 100).toFixed(4)}%</span>
                </div>
                <div className="stat-box">
                  <span className="label">TCA Countdown</span>
                  <span className="val">{highRiskConjunction.timeToTcaHours.toFixed(1)} hours</span>
                </div>
                <div className="stat-box">
                  <span className="label">Miss Distance</span>
                  <span className="val text-glow-cyan">{highRiskConjunction.missDistanceKm.toFixed(3)} km</span>
                </div>
              </div>
            </div>
            <div className="hud-modal-footer">
              <button className="btn btn-danger" onClick={() => {
                handleSelectEvent(highRiskConjunction.id);
                acknowledgedRef.current.add(highRiskConjunction.id);
                popupShownRef.current = false;
                setShowHighRiskPopup(false);
              }}>
                Analyze Trajectory
              </button>
              <button className="btn btn-secondary" onClick={() => {
                acknowledgedRef.current.add(highRiskConjunction.id);
                popupShownRef.current = false;
                setShowHighRiskPopup(false);
              }}>
                Acknowledge Threat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
