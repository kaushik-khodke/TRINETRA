import React from 'react';
import { Terminal, CheckCircle2, Clock, Cpu } from 'lucide-react';

export default function TraceViewer({ trace }) {
  if (!trace) {
    return (
      <div className="panel trace-sidebar">
        <div className="panel-header">
          <span className="panel-title">
            <Terminal size={16} style={{ color: '#10B981' }} />
            Observable Execution Trace
          </span>
        </div>
        <div style={{ color: '#64748B', fontSize: '12px', textAlign: 'center', marginTop: '40px' }}>
          Telemetry stream standing by.
        </div>
      </div>
    );
  }

  const steps = trace.steps || [];

  return (
    <div className="panel trace-sidebar">
      <div className="panel-header">
        <span className="panel-title">
          <Terminal size={16} style={{ color: '#10B981' }} />
          Observable Execution Trace
        </span>
        <span className="mono" style={{ fontSize: '11px', color: '#10B981' }}>
          {trace.duration_ms ? `${trace.duration_ms} ms` : 'COMPLETED'}
        </span>
      </div>

      <div style={{ marginBottom: '12px', fontSize: '11px', color: '#94A3B8' }}>
        <div>
          <strong>ROUTED TASK:</strong>{' '}
          <span style={{ color: '#10B981' }}>{trace.detected_task?.toUpperCase()}</span>
        </div>
        <div style={{ marginTop: '2px' }}>
          <strong>INPUT CONFIG:</strong>{' '}
          <span className="mono">{trace.input_mode?.toUpperCase()}</span>
        </div>
      </div>

      <div className="trace-terminal">
        {steps.map((s, idx) => (
          <div key={idx} className="trace-step-row">
            <div className="trace-num">0{s.step_id}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="trace-stage">{s.stage}</span>
                {s.tool && (
                  <span style={{ color: '#10B981', fontSize: '10px' }}>[{s.tool}]</span>
                )}
              </div>
              <div className="trace-details">{s.details}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
