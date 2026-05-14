import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import '../styles/cockpit.css';

const DEMOS = [
  { id: 'incident_storm', name: 'Incident Storm', desc: 'Enterprise alert flood — classify on Xeon 6, deep analysis on Gaudi', phases: ['Alert Triage (Xeon 6)', 'Knowledge Search (Xeon 6)', 'Deep Analysis (Gaudi)', 'Batch Reporting (Gaudi)'] },
  { id: 'dashboard_storm', name: 'Dashboard Storm', desc: 'Operational screenshots — classify on Xeon 6, interpret on Gaudi', phases: ['Screenshot Classify (Xeon 6)', 'Chart Interpret (Gaudi)', 'Summary Generation (Gaudi)', 'Incident Synthesis (Gaudi)'] },
  { id: 'token_cannon_multimodal', name: 'Token Cannon', desc: 'Maximum multimodal generation — stress Gaudi throughput', phases: ['Heavy Generation (Gaudi)', 'Document Distill (Gaudi)', 'Batch Report (Gaudi)'] },
  { id: 'image_to_manual', name: 'Image to Manual', desc: 'Equipment photos → installation guides on Gaudi', phases: ['Image Identify (Xeon 6)', 'Manual Generate (Gaudi)', 'Doc Summary (Gaudi)'] },
  { id: 'model_race', name: 'Model Race', desc: 'Same tasks across all hardware — compare Xeon 6 vs Gaudi', phases: ['Small Tasks (Xeon Eco)', 'Mid Tasks (Xeon Perf)', 'Large Tasks (Gaudi)'] },
  { id: 'visual_rag_barrage', name: 'Visual RAG', desc: 'Multimodal knowledge base — embed on Xeon 6, answer on Gaudi', phases: ['Visual Index (Xeon 6)', 'Layout Extract (Xeon 6)', 'Visual Answer (Gaudi)'] },
];

const MODEL_COLORS: Record<string, string> = { 'granite-4-0-h-tiny': '#00c853', 'codellama-7b-instruct': '#0071c5', 'llama-scout-17b': '#ff6d00' };
const MODEL_HW: Record<string, string> = { 'granite-4-0-h-tiny': 'Xeon 6 Eco', 'codellama-7b-instruct': 'Xeon 6 + AMX', 'llama-scout-17b': 'Gaudi' };

interface Snapshot {
  t: number;
  completed: number;
  eco: number;
  perf: number;
  gaudi: number;
  tokens: number;
  images: number;
}

export default function CockpitDashboard() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [launching, setLaunching] = useState(false);
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [history, setHistory] = useState<Snapshot[]>([]);
  const startTimeRef = useRef(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const d = await api.platformStatus();
        setData(d);
        const lp = d.live_progress as { completed: number; total: number } | null;
        const agg = d.aggregate as Record<string, unknown> | undefined;
        const rc = (agg?.route_counts || {}) as Record<string, number>;
        if (lp && lp.completed > 0) {
          const elapsed = startTimeRef.current > 0 ? (Date.now() - startTimeRef.current) / 1000 : 0;
          setHistory(prev => {
            const last = prev[prev.length - 1];
            if (last && last.completed === lp.completed) return prev;
            return [...prev, {
              t: Math.round(elapsed),
              completed: lp.completed,
              eco: rc.eco || 0,
              perf: rc.performance || 0,
              gaudi: rc.overdrive || 0,
              tokens: (agg?.estimated_tokens_per_second as number || 0) * elapsed,
              images: agg?.total_images as number || 0,
            }];
          });
        }
        if (d.active_runs && (d.active_runs as unknown[]).length > 0) {
          const wr = (d.active_runs as Array<Record<string, unknown>>).find(r => r.type === 'workload');
          if (wr && wr.profile) setActiveDemo(wr.profile as string);
        }
      } catch { /* ignore */ }
    };
    poll();
    pollRef.current = setInterval(poll, 1500);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const launchDemo = async (profileId: string) => {
    setLaunching(true);
    setActiveDemo(profileId);
    setHistory([]);
    setShowTelemetry(false);
    startTimeRef.current = Date.now();
    try { await api.workloadRun(profileId, 'drive', 42); } catch { /* ignore */ }
    setLaunching(false);
  };

  const isRunning = !!(data && Array.isArray(data.active_runs) && (data.active_runs as Array<Record<string, unknown>>).some(r => r.type === 'workload'));
  const isComplete = !isRunning && activeDemo != null && data?.latest_completed != null;
  const lp = data?.live_progress as { completed: number; total: number; pct: number } | null;
  const agg = data?.aggregate as Record<string, unknown> | undefined;
  const rc = (agg?.route_counts || {}) as Record<string, number>;
  const mt = (data?.model_telemetry || {}) as Record<string, Record<string, unknown>>;
  const demoMeta = DEMOS.find(d => d.id === activeDemo);
  const lcProfile = (data?.latest_completed as Record<string, unknown>)?.workload_profile as string;
  const lcMeta = DEMOS.find(d => d.id === lcProfile);

  const totalReqs = (rc.eco || 0) + (rc.performance || 0) + (rc.overdrive || 0);

  return (
    <div className="cockpit" style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '0.05em' }}>
            INFERENCE <span style={{ color: '#ee0000' }}>OVERDRIVE</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#666' }}>Intel Xeon 6 + Gaudi</div>
        </div>
        {(isRunning || isComplete) && (
          <div style={{ padding: '6px 16px', borderRadius: '4px', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.08em',
            background: isRunning ? '#0071c5' : '#00c853', color: '#fff' }}>
            {isRunning ? 'RUNNING' : 'COMPLETE'}
          </div>
        )}
      </div>

      {/* ===== IDLE ===== */}
      {!isRunning && !isComplete && (
        <>
          <div style={{ textAlign: 'center', margin: '40px 0 24px', color: '#888', fontSize: '0.95rem' }}>Select a demo to start</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '10px' }}>
            {DEMOS.map(d => (
              <div key={d.id} onClick={() => !launching && launchDemo(d.id)} style={{
                background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '14px', cursor: 'pointer', transition: 'border-color 0.2s',
              }} onMouseEnter={e => (e.currentTarget.style.borderColor = '#0071c5')} onMouseLeave={e => (e.currentTarget.style.borderColor = '#2a2a2a')}>
                <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '4px' }}>{d.name}</div>
                <div style={{ fontSize: '0.75rem', color: '#888' }}>{d.desc}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ===== RUNNING ===== */}
      {isRunning && demoMeta && lp && (
        <>
          {/* Demo + Progress */}
          <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '4px' }}>{demoMeta.name}</div>
            <div style={{ fontSize: '0.78rem', color: '#888', marginBottom: '12px' }}>{demoMeta.desc}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
              <span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{lp.completed} / {lp.total}</span>
              <span style={{ color: '#0071c5', fontWeight: 700 }}>{lp.pct}%</span>
            </div>
            <div style={{ height: '6px', borderRadius: '3px', background: '#2a2a2a', overflow: 'hidden' }}>
              <div className="ck-smooth" style={{ height: '100%', width: `${lp.pct}%`, background: '#0071c5', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Phases */}
          <div style={{ marginBottom: '16px' }}>
            {demoMeta.phases.map((phase, i) => {
              const done = totalReqs > 0 && i < Math.floor((lp.pct / 100) * demoMeta.phases.length);
              const active = totalReqs > 0 && i === Math.floor((lp.pct / 100) * demoMeta.phases.length);
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '6px 0', fontSize: '0.82rem' }}>
                  <div style={{ width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700,
                    background: done ? '#00c853' : active ? '#0071c5' : '#2a2a2a', color: '#fff', flexShrink: 0 }}>
                    {done ? '✓' : active ? '▶' : '○'}
                  </div>
                  <span style={{ color: done ? '#00c853' : active ? '#fff' : '#555' }}>{phase}</span>
                </div>
              );
            })}
          </div>

          {/* Cumulative chart */}
          {history.length > 1 && (
            <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#888', marginBottom: '8px' }}>Requests Over Time</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '60px' }}>
                {history.map((s, i) => {
                  const maxReqs = Math.max(...history.map(x => x.completed));
                  const ecoH = maxReqs > 0 ? (s.eco / maxReqs) * 100 : 0;
                  const gaudiH = maxReqs > 0 ? (s.gaudi / maxReqs) * 100 : 0;
                  return (
                    <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%' }}>
                      {s.gaudi > 0 && <div style={{ height: `${gaudiH}%`, background: '#ff6d00', borderRadius: '1px 1px 0 0', minHeight: s.gaudi > 0 ? '2px' : 0 }} />}
                      {s.perf > 0 && <div style={{ height: `${(s.perf / (maxReqs || 1)) * 100}%`, background: '#0071c5', minHeight: '2px' }} />}
                      {s.eco > 0 && <div style={{ height: `${ecoH}%`, background: '#00c853', borderRadius: '0 0 1px 1px', minHeight: '2px' }} />}
                    </div>
                  );
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#555', marginTop: '4px' }}>
                <span>0s</span>
                <span>{history[history.length - 1]?.t || 0}s</span>
              </div>
            </div>
          )}

          {/* Running totals */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
            {[
              { label: 'Xeon 6', value: (rc.eco || 0) + (rc.performance || 0), color: '#0071c5' },
              { label: 'Gaudi', value: rc.overdrive || 0, color: '#ff6d00' },
              { label: 'Total', value: totalReqs, color: '#fff' },
            ].map(m => (
              <div key={m.label} style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '6px', padding: '10px', textAlign: 'center' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace', color: m.color }}>{m.value}</div>
                <div style={{ fontSize: '0.68rem', color: '#888', textTransform: 'uppercase' }}>{m.label}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ===== COMPLETE ===== */}
      {isComplete && (
        <>
          <div style={{ background: '#141414', border: '1px solid #00c853', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1rem' }}>{lcMeta?.name || lcProfile}</div>
                <div style={{ fontSize: '0.78rem', color: '#888' }}>{totalReqs} requests completed</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#00c853', fontFamily: 'Red Hat Mono, monospace' }}>
                  {Math.round(agg?.requests_per_second as number || 0)} req/s
                </div>
                <div style={{ fontSize: '0.72rem', color: '#888' }}>
                  {(agg?.estimated_tokens_per_second as number || 0).toLocaleString()} tok/s · p95 {Math.round(agg?.p95_latency_ms as number || 0)}ms
                </div>
              </div>
            </div>
          </div>

          {/* Final chart */}
          {history.length > 1 && (
            <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#888', marginBottom: '8px' }}>Run Timeline</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '60px' }}>
                {history.map((s, i) => {
                  const maxReqs = Math.max(...history.map(h => h.completed));
                  return (
                    <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%' }}>
                      {s.gaudi > 0 && <div style={{ height: `${(s.gaudi / (maxReqs || 1)) * 100}%`, background: '#ff6d00', borderRadius: '1px 1px 0 0', minHeight: '2px' }} />}
                      {s.perf > 0 && <div style={{ height: `${(s.perf / (maxReqs || 1)) * 100}%`, background: '#0071c5', minHeight: '2px' }} />}
                      {s.eco > 0 && <div style={{ height: `${(s.eco / (maxReqs || 1)) * 100}%`, background: '#00c853', borderRadius: '0 0 1px 1px', minHeight: '2px' }} />}
                    </div>
                  );
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#555', marginTop: '4px' }}>
                <span>Start</span>
                <span style={{ display: 'flex', gap: '12px' }}>
                  <span><span style={{ color: '#00c853' }}>●</span> Eco</span>
                  <span><span style={{ color: '#0071c5' }}>●</span> Perf</span>
                  <span><span style={{ color: '#ff6d00' }}>●</span> Gaudi</span>
                </span>
                <span>{history[history.length - 1]?.t || 0}s</span>
              </div>
            </div>
          )}

          {/* Lane split */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
            {[
              { name: 'XEON ECO', hw: 'Xeon 6 · Granite', count: rc.eco || 0, color: '#00c853' },
              { name: 'XEON PERF', hw: 'Xeon 6 + AMX · CodeLlama', count: rc.performance || 0, color: '#0071c5' },
              { name: 'GAUDI', hw: 'Gaudi · Llama Scout', count: rc.overdrive || 0, color: '#ff6d00' },
            ].map(l => (
              <div key={l.name} style={{ background: '#141414', border: `1px solid ${l.count > 0 ? l.color : '#2a2a2a'}`, borderRadius: '6px', padding: '10px', borderLeft: `3px solid ${l.color}` }}>
                <div style={{ fontWeight: 700, fontSize: '0.78rem', letterSpacing: '0.04em' }}>{l.name}</div>
                <div style={{ fontSize: '0.65rem', color: '#888' }}>{l.hw}</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace', color: l.color, marginTop: '4px' }}>
                  {l.count} <span style={{ fontSize: '0.72rem', color: '#888' }}>({totalReqs > 0 ? Math.round(l.count / totalReqs * 100) : 0}%)</span>
                </div>
              </div>
            ))}
          </div>

          {/* Model telemetry */}
          {Object.keys(mt).length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#888', marginBottom: '8px', cursor: 'pointer' }}
                onClick={() => setShowTelemetry(!showTelemetry)}>
                {showTelemetry ? '▼' : '▶'} MODEL DETAIL
              </div>
              {showTelemetry && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
                  {Object.entries(mt).map(([model, stats]) => (
                    <div key={model} style={{ background: '#141414', border: `1px solid ${MODEL_COLORS[model] || '#2a2a2a'}`, borderRadius: '6px', padding: '10px', borderLeft: `3px solid ${MODEL_COLORS[model] || '#555'}` }}>
                      <div style={{ fontWeight: 700, fontSize: '0.78rem', color: MODEL_COLORS[model] }}>{model}</div>
                      <div style={{ fontSize: '0.65rem', color: '#888', marginBottom: '4px' }}>{MODEL_HW[model]}</div>
                      <div style={{ fontSize: '0.75rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px' }}>
                        <div><b>{stats.count as number}</b> reqs</div>
                        <div><b>{(stats.avg_latency_ms as number).toFixed(0)}</b> ms</div>
                        <div><b>{(stats.total_input_tokens as number).toLocaleString()}</b> in</div>
                        <div><b>{(stats.tokens_per_sec as number).toLocaleString()}</b> tok/s</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="ck-mode-btn" onClick={() => lcProfile && launchDemo(lcProfile)}>Run Again</button>
            <button className="ck-mode-btn" onClick={() => { setActiveDemo(null); setHistory([]); setData(prev => prev ? { ...prev, latest_completed: null, model_telemetry: {}, task_telemetry: {} } : null); }}>Try Another</button>
          </div>
        </>
      )}

      <div style={{ marginTop: '24px', fontSize: '0.65rem', color: '#444', textAlign: 'center' }}>
        Intel Xeon 6 + Gaudi — Red Hat OpenShift AI
      </div>
    </div>
  );
}
