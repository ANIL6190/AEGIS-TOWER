import React from 'react';
import { Command, Eye, Send, XCircle } from 'lucide-react';

export default function OperatorPanel({ activeEvent, onAction, actionLog }) {
  if (!activeEvent) {
    return (
      <div className="panel operator-panel">
        <div className="panel-header">
          <h2>
            <Command size={14} color="var(--c-nominal)" />
            Operator Action Deck
          </h2>
        </div>
        <div className="operator-empty-state">
          Select an active conjunction event from the feed to initiate operator actions.
        </div>
      </div>
    );
  }

  const isActionRequired = activeEvent.riskClassification === 'MEDIUM' || activeEvent.riskClassification === 'HIGH';

  return (
    <div className="panel operator-panel">
      <div className="panel-header">
        <h2>
          <Command size={14} color="var(--c-nominal)" />
          Operator Action Deck // {activeEvent.id}
        </h2>
        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--t-secondary)' }}>
          Risk: {activeEvent.riskClassification}
        </span>
      </div>

      <div className="operator-details-summary">
        <div className="summary-row">
          <span>Primary Object:</span>
          <strong>{activeEvent.primaryObject.name}</strong>
        </div>
        <div className="summary-row">
          <span>Secondary Object:</span>
          <strong>{activeEvent.secondaryObject.name}</strong>
        </div>
        <div className="summary-row">
          <span>Current Probability:</span>
          <strong style={{ color: activeEvent.riskClassification === 'HIGH' ? 'var(--c-critical)' : activeEvent.riskClassification === 'MEDIUM' ? 'var(--c-warn)' : 'var(--c-nominal)' }}>
            {(activeEvent.predictedProbabilityOfCollision * 100).toFixed(5)}%
          </strong>
        </div>
      </div>

      {isActionRequired ? (
        <div className="operator-controls">
          <div className="operator-actions-prompt">
            <span style={{ color: 'var(--c-warn)', fontWeight: 'bold' }}>⚠️ ESCALATION DECK ACTIVE:</span> Confirm operational command for this threat.
          </div>
          <div className="operator-buttons">
            {/* Action 1: Monitor */}
            <button 
              className="btn btn-monitor" 
              onClick={() => onAction(activeEvent.id, 'monitor', 'Continue Monitoring')}
            >
              <Eye size={13} />
              Continue Monitoring
            </button>

            {/* Action 2: Escalate */}
            <button 
              className="btn btn-escalate" 
              onClick={() => onAction(activeEvent.id, 'escalate', 'Escalate to Maneuver Planning')}
            >
              <Send size={13} />
              Escalate to Maneuver Planning
            </button>

            {/* Action 3: Dismiss */}
            <button 
              className="btn btn-dismiss" 
              onClick={() => onAction(activeEvent.id, 'dismiss', 'Dismiss as False Positive')}
            >
              <XCircle size={13} />
              Dismiss as False Positive
            </button>
          </div>
        </div>
      ) : (
        <div className="operator-nominal-state">
          <span style={{ color: 'var(--c-success)' }}>✓ NOMINAL TRACKING:</span> Conjunction risk is below action threshold. Continue routine monitoring.
        </div>
      )}

      {/* Operator Action Console Log */}
      <div className="action-console">
        <div className="console-title">OPERATOR DECISION LOG</div>
        <div className="console-lines">
          {actionLog.length === 0 ? (
            <div className="console-empty">No console entries recorded for this session.</div>
          ) : (
            actionLog.slice().reverse().map((log, index) => (
              <div key={index} className="console-line">
                <span className="console-timestamp">[{log.time}]</span>{' '}
                <span className="console-event-id">{log.eventId}:</span>{' '}
                <span className={`console-action-text ${log.type}`}>{log.actionText}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
