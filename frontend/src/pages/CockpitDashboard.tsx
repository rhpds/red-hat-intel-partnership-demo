import { useState, useEffect } from 'react';
import '../styles/cockpit.css';

const MODES = ['STANDBY', 'DRIVE', 'BOOST', 'OVERDRIVE', 'MAX_Q', 'COOLDOWN'] as const;
type Mode = typeof MODES[number];

interface Metrics {
  mode: Mode;
  rps: number;
  tps: number;
  p95: number;
  queue: number;
  ecoUtil: number;
  perfUtil: number;
  gaudiUtil: number;
  ecoCount: number;
  perfCount: number;
  gaudiCount: number;
  totalReqs: number;
  imgPerSec: number;
  docPerSec: number;
  trainingActive: boolean;
  trainLoss: number;
  baseScore: number;
  tunedScore: number;
  events: Array<{ time: string; msg: string; color: string }>;
}

const MODE_METRICS: Record<Mode, Partial<Metrics>> = {
  STANDBY: { rps: 0, tps: 0, p95: 0, queue: 0, ecoUtil: 0, perfUtil: 0, gaudiUtil: 0, ecoCount: 0, perfCount: 0, gaudiCount: 0, totalReqs: 0, imgPerSec: 0, docPerSec: 0 },
  DRIVE: { rps: 12, tps: 4200, p95: 85, queue: 2, ecoUtil: 28, perfUtil: 35, gaudiUtil: 15, ecoCount: 8, perfCount: 10, gaudiCount: 7, totalReqs: 25, imgPerSec: 0.5, docPerSec: 0.2 },
  BOOST: { rps: 48, tps: 18500, p95: 220, queue: 12, ecoUtil: 52, perfUtil: 68, gaudiUtil: 45, ecoCount: 80, perfCount: 100, gaudiCount: 70, totalReqs: 250, imgPerSec: 3.2, docPerSec: 1.1 },
  OVERDRIVE: { rps: 85, tps: 42000, p95: 680, queue: 35, ecoUtil: 72, perfUtil: 85, gaudiUtil: 78, ecoCount: 300, perfCount: 400, gaudiCount: 300, totalReqs: 1000, imgPerSec: 8.5, docPerSec: 3.4 },
  MAX_Q: { rps: 120, tps: 65000, p95: 1200, queue: 85, ecoUtil: 88, perfUtil: 95, gaudiUtil: 92, ecoCount: 1500, perfCount: 2000, gaudiCount: 1500, totalReqs: 5000, imgPerSec: 15, docPerSec: 6 },
  COOLDOWN: { rps: 3, tps: 800, p95: 45, queue: 0, ecoUtil: 5, perfUtil: 8, gaudiUtil: 2, ecoCount: 2, perfCount: 2, gaudiCount: 1, totalReqs: 5, imgPerSec: 0, docPerSec: 0 },
};

function useMetrics(mode: Mode): Metrics {
  const [metrics, setMetrics] = useState<Metrics>({
    mode, rps: 0, tps: 0, p95: 0, queue: 0, ecoUtil: 0, perfUtil: 0, gaudiUtil: 0,
    ecoCount: 0, perfCount: 0, gaudiCount: 0, totalReqs: 0, imgPerSec: 0, docPerSec: 0,
    trainingActive: false, trainLoss: 0, baseScore: 0, tunedScore: 0, events: [],
  });

  useEffect(() => {
    const target = MODE_METRICS[mode] || {};
    const events: Array<{ time: string; msg: string; color: string }> = [
      { time: new Date().toISOString().slice(11, 19), msg: `Mode → ${mode}`, color: mode === 'OVERDRIVE' ? '#ff6d00' : mode === 'MAX_Q' ? '#ee0000' : '#0071c5' },
    ];
    if (mode === 'OVERDRIVE') events.push({ time: new Date().toISOString().slice(11, 19), msg: 'Gaudi Overdrive engaged', color: '#ff6d00' });
    if (mode === 'COOLDOWN') events.push({ time: new Date().toISOString().slice(11, 19), msg: 'Cooldown — draining queue', color: '#00c853' });

    setMetrics(prev => ({
      ...prev, mode, ...target,
      trainingActive: false, trainLoss: 0, baseScore: 0, tunedScore: 0,
      events: [...events, ...prev.events].slice(0, 8),
    }));
  }, [mode]);

  return metrics;
}

function Gauge({ value, label, unit, color, active }: { value: number | string; label: string; unit?: string; color: string; active: boolean }) {
  return (
    <div className={`ck-gauge ${active ? 'active' : ''}`}>
      <div className="ck-gauge-value" style={{ color }}>{typeof value === 'number' ? value.toLocaleString() : value}</div>
      {unit && <div style={{ fontSize: '0.82rem', color: '#888', marginTop: '2px' }}>{unit}</div>}
      <div className="ck-gauge-label">{label}</div>
    </div>
  );
}

function LaneCard({ name, hw, color, util, count, active }: { name: string; hw: string; color: string; util: number; count: number; active: boolean }) {
  const laneClass = name.toLowerCase().includes('eco') ? 'eco' : name.toLowerCase().includes('perf') ? 'performance' : 'overdrive';
  return (
    <div className={`ck-lane ${laneClass} ${active ? 'active' : ''}`} style={{ color }}>
      <div className="ck-pulse" />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.92rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{name}</div>
          <div style={{ fontSize: '0.72rem', color: '#888' }}>{hw}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace' }}>{util}%</div>
          <div style={{ fontSize: '0.7rem', color: '#888' }}>{count.toLocaleString()} reqs</div>
        </div>
      </div>
      <div className="ck-util-bar">
        <div className="ck-util-fill" style={{ width: `${util}%`, background: color }} />
      </div>
    </div>
  );
}

export default function CockpitDashboard() {
  const [mode, setMode] = useState<Mode>('STANDBY');
  const m = useMetrics(mode);
  const active = mode !== 'STANDBY' && mode !== 'COOLDOWN';

  return (
    <div className="cockpit" style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '0.05em' }}>
            INFERENCE <span style={{ color: '#ee0000' }}>OVERDRIVE</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#888' }}>Intel Xeon 6 + Gaudi — Performance Cockpit</div>
        </div>
        <div style={{
          padding: '10px 24px', borderRadius: '6px', fontWeight: 700, fontSize: '1.1rem',
          letterSpacing: '0.1em', fontFamily: 'Red Hat Mono, monospace',
          background: mode === 'OVERDRIVE' ? '#ff6d00' : mode === 'MAX_Q' ? '#ee0000' : mode === 'STANDBY' ? '#2a2a2a' : '#0071c5',
          color: '#fff', border: '1px solid rgba(255,255,255,0.1)',
        }}>
          {mode.replace('_', ' ')}
        </div>
      </div>

      {/* Mode Controls */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {MODES.map(m => (
          <button key={m} className={`ck-mode-btn ${mode === m ? 'active' : ''}`} onClick={() => setMode(m)}>
            {m.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Main Gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        <Gauge value={m.rps} label="Requests / sec" color={active ? '#0071c5' : '#555'} active={active} />
        <Gauge value={m.tps} label="Tokens / sec" color={active ? '#00c853' : '#555'} active={active} />
        <Gauge value={m.p95} label="p95 Latency" unit="ms" color={m.p95 > 500 ? '#ff6d00' : active ? '#0071c5' : '#555'} active={active} />
        <Gauge value={m.queue} label="Queue Depth" color={m.queue > 50 ? '#ee0000' : active ? '#0071c5' : '#555'} active={active} />
      </div>

      {/* Hardware Lanes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
        <LaneCard name="XEON ECO" hw="Intel Xeon 6 • Granite Tiny" color="#00c853" util={m.ecoUtil} count={m.ecoCount} active={m.ecoUtil > 5} />
        <LaneCard name="XEON PERFORMANCE" hw="Intel Xeon 6 + AMX • CodeLlama 7B" color="#0071c5" util={m.perfUtil} count={m.perfCount} active={m.perfUtil > 5} />
        <LaneCard name="GAUDI OVERDRIVE" hw="Intel Gaudi • Llama Scout 17B" color="#ff6d00" util={m.gaudiUtil} count={m.gaudiCount} active={m.gaudiUtil > 5} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px', marginBottom: '20px' }}>
        {/* Route Distribution */}
        <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '16px' }}>
          <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#888', marginBottom: '10px' }}>Route Distribution</div>
          {m.totalReqs > 0 ? (
            <>
              <div style={{ display: 'flex', height: '24px', borderRadius: '4px', overflow: 'hidden', marginBottom: '8px' }}>
                {m.ecoCount > 0 && <div style={{ width: `${(m.ecoCount / m.totalReqs) * 100}%`, background: '#00c853', minWidth: '20px' }} />}
                {m.perfCount > 0 && <div style={{ width: `${(m.perfCount / m.totalReqs) * 100}%`, background: '#0071c5', minWidth: '20px' }} />}
                {m.gaudiCount > 0 && <div style={{ width: `${(m.gaudiCount / m.totalReqs) * 100}%`, background: '#ff6d00', minWidth: '20px' }} />}
              </div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem' }}>
                <span><span style={{ color: '#00c853' }}>●</span> Eco: {m.ecoCount}</span>
                <span><span style={{ color: '#0071c5' }}>●</span> Perf: {m.perfCount}</span>
                <span><span style={{ color: '#ff6d00' }}>●</span> Gaudi: {m.gaudiCount}</span>
                <span style={{ color: '#888', marginLeft: 'auto' }}>Total: {m.totalReqs.toLocaleString()}</span>
              </div>
            </>
          ) : (
            <div style={{ color: '#555', fontSize: '0.85rem' }}>Waiting for workload...</div>
          )}

          {/* Multimodal metrics */}
          {(m.imgPerSec > 0 || m.docPerSec > 0) && (
            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #2a2a2a' }}>
              <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#888', marginBottom: '6px' }}>Multimodal</div>
              <div style={{ display: 'flex', gap: '20px', fontSize: '0.85rem' }}>
                <div><span style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace' }}>{m.imgPerSec.toFixed(1)}</span> <span style={{ color: '#888' }}>img/s</span></div>
                <div><span style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace' }}>{m.docPerSec.toFixed(1)}</span> <span style={{ color: '#888' }}>doc/s</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Event Feed */}
        <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '12px' }}>
          <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#888', marginBottom: '8px' }}>Live Events</div>
          {m.events.length === 0 ? (
            <div style={{ color: '#555', fontSize: '0.82rem' }}>No events</div>
          ) : (
            m.events.map((e, i) => (
              <div key={i} className="ck-event">
                <div className="ck-event-dot" style={{ background: e.color }} />
                <span style={{ color: '#888', fontFamily: 'Red Hat Mono, monospace', fontSize: '0.72rem' }}>{e.time}</span>
                <span>{e.msg}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#555', padding: '8px 0' }}>
        <span>Intel Xeon 6 + Gaudi — Red Hat OpenShift AI Platform</span>
        <span>Mock Telemetry • Deterministic Simulation</span>
      </div>
    </div>
  );
}
