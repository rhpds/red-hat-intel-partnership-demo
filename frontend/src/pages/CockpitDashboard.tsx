import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import '../styles/cockpit.css';

const DEMOS = [
  { id: 'incident_storm', name: 'Incident Storm', desc: 'Enterprise alert flood — classify on Xeon 6, deep analysis on Gaudi.', phases: ['Alert Triage (Xeon 6)', 'Knowledge Search (Xeon 6)', 'Deep Analysis (Gaudi)', 'Batch Reporting (Gaudi)'] },
  { id: 'dashboard_storm', name: 'Dashboard Storm', desc: 'Operational screenshots — classify on Xeon 6, interpret on Gaudi.', phases: ['Screenshot Classify (Xeon 6)', 'Chart Interpret (Gaudi)', 'Summary Generation (Gaudi)', 'Incident Synthesis (Gaudi)'] },
  { id: 'model_race', name: 'Model Race', desc: 'Same tasks across all hardware — compare Xeon 6 vs Gaudi live.', phases: ['Small Tasks (Xeon Eco)', 'Mid Tasks (Xeon Perf)', 'Large Tasks (Gaudi)'] },
];

const SCALES = [
  { id: 'quick', label: 'Quick', mode: 'standby', count: 5, time: '~5s', locked: false },
  { id: 'standard', label: 'Standard', mode: 'drive', count: 25, time: '~20s', locked: false },
  { id: 'extended', label: 'Extended', mode: 'boost', count: 250, time: '~3 min', locked: true },
];

const MODEL_COLORS: Record<string, string> = { 'granite-4-0-h-tiny': '#3e8635', 'codellama-7b-instruct': '#0068b5', 'llama-scout-17b': '#e67e22' };
const MODEL_HW: Record<string, string> = { 'granite-4-0-h-tiny': 'Intel Xeon 6 · Eco', 'codellama-7b-instruct': 'Intel Xeon 6 + AMX', 'llama-scout-17b': 'Intel Gaudi' };

interface Snapshot { t: number; completed: number; eco: number; perf: number; gaudi: number; images: number; }

type DemoState = 'idle' | 'running' | 'done';

export default function CockpitDashboard() {
  const [demoState, setDemoState] = useState<DemoState>('idle');
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [launching, setLaunching] = useState(false);
  const [showTelemetry, setShowTelemetry] = useState(true);
  const [scale, setScale] = useState('standard');
  const [unlockCode, setUnlockCode] = useState('');
  const selectedScale = SCALES.find(s => s.id === scale) || SCALES[1];

  // Persistent metrics — survive state transitions
  const [completed, setCompleted] = useState(0);
  const [total, setTotal] = useState(0);
  const [routes, setRoutes] = useState<Record<string, number>>({});
  const [rps, setRps] = useState(0);
  const [tps, setTps] = useState(0);
  const [p95, setP95] = useState(0);
  const [images, setImages] = useState(0);
  const [history, setHistory] = useState<Snapshot[]>([]);
  const [models, setModels] = useState<Record<string, Record<string, unknown>>>({});

  const startTimeRef = useRef(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (demoState !== 'running') return;

    const poll = async () => {
      try {
        const d = await api.platformStatus() as Record<string, unknown>;
        const lp = d.live_progress as { completed: number; total: number; pct: number } | null;
        const agg = d.aggregate as Record<string, unknown> | undefined;
        const rc = (agg?.route_counts || {}) as Record<string, number>;
        const mt = (d.model_telemetry || {}) as Record<string, Record<string, unknown>>;
        const activeRuns = d.active_runs as Array<Record<string, unknown>> | undefined;
        const isActive = activeRuns && activeRuns.some(r => r.type === 'workload');

        // Update persistent metrics — only climb, never reset
        const newCompleted = lp?.completed ?? 0;
        const newTotal = lp?.total ?? 0;
        if (newCompleted > 0) setCompleted(prev => Math.max(prev, newCompleted));
        if (newTotal > 0) setTotal(prev => Math.max(prev, newTotal));
        if (Object.keys(rc).length > 0) setRoutes(prev => {
          const merged = { ...prev };
          for (const [k, v] of Object.entries(rc)) { merged[k] = Math.max(merged[k] || 0, v); }
          return merged;
        });
        if (agg?.requests_per_second) setRps(prev => Math.max(prev, Math.round(agg.requests_per_second as number)));
        if (agg?.estimated_tokens_per_second) setTps(prev => Math.max(prev, Math.round(agg.estimated_tokens_per_second as number)));
        if (agg?.p95_latency_ms) setP95(prev => Math.max(prev, Math.round(agg.p95_latency_ms as number)));
        const newImages = agg?.total_images as number || 0;
        if (newImages > 0) setImages(prev => Math.max(prev, newImages));
        if (Object.keys(mt).length > 0) setModels(mt);

        // Add to history if progress changed
        const snapCompleted = newCompleted > 0 ? newCompleted : (Object.values(rc).reduce((a, b) => a + b, 0) || 0);
        if (snapCompleted > 0) {
          const elapsed = startTimeRef.current > 0 ? Math.round((Date.now() - startTimeRef.current) / 1000) : 0;
          setHistory(prev => {
            const last = prev[prev.length - 1];
            if (last && last.completed >= snapCompleted) return prev;
            return [...prev, { t: elapsed, completed: snapCompleted, eco: rc.eco || 0, perf: rc.performance || 0, gaudi: rc.overdrive || 0, images: newImages }];
          });
        }

        // Transition to done — grab final metrics from latest_completed
        if (!isActive && snapCompleted > 0) {
          const lc = d.latest_completed as Record<string, unknown> | null;
          if (lc) {
            const lcRc = (lc.route_counts || {}) as Record<string, number>;
            if (Object.keys(lcRc).length > 0) setRoutes(lcRc);
            if (lc.total_requests) setCompleted(lc.total_requests as number);
            if (lc.requests_per_second) setRps(Math.round(lc.requests_per_second as number));
            if (lc.estimated_tokens_per_second) setTps(Math.round(lc.estimated_tokens_per_second as number));
            if (lc.p95_latency_ms) setP95(Math.round(lc.p95_latency_ms as number));
            const lcImgs = lc.total_images as number || 0;
            if (lcImgs > 0) setImages(lcImgs);
          }
          setDemoState('done');
          if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
        }
      } catch { /* ignore */ }
    };

    pollRef.current = setInterval(poll, 1200);
    poll();
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };
  }, [demoState]); // eslint-disable-line react-hooks/exhaustive-deps

  const launchDemo = async (profileId: string) => {
    setLaunching(true);
    setActiveDemo(profileId);
    setCompleted(0); setTotal(0); setRoutes({}); setRps(0); setTps(0); setP95(0); setImages(0);
    setHistory([]); setModels({}); setShowTelemetry(true);
    startTimeRef.current = Date.now();
    setDemoState('running');
    try { await api.workloadRun(profileId, selectedScale.mode, 42, true, selectedScale.locked ? unlockCode : ''); } catch { /* ignore */ }
    setLaunching(false);
  };

  const resetDemo = () => {
    setDemoState('idle');
    setActiveDemo(null);
    setCompleted(0); setTotal(0); setRoutes({}); setRps(0); setTps(0); setP95(0); setImages(0);
    setHistory([]); setModels({});
  };

  const demoMeta = DEMOS.find(d => d.id === activeDemo);
  const eco = routes.eco || 0;
  const perf = routes.performance || 0;
  const gaudi = routes.overdrive || 0;
  const totalReqs = eco + perf + gaudi;
  const pct = total > 0 ? Math.round(completed / total * 100) : 0;
  const isDone = demoState === 'done';
  const isActive = demoState === 'running' || demoState === 'done';

  return (
    <div className="cockpit" style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <img src="/intel-logo.svg" alt="Intel" style={{ height: '20px', opacity: 0.9 }} />
          <img src="/redhat-logo.svg" alt="Red Hat" style={{ height: '20px', opacity: 0.9 }} />
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '0.05em' }}>
              INFERENCE <span style={{ color: '#ee0000' }}>OVERDRIVE</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: '#666', letterSpacing: '0.04em' }}>INTEL XEON 6 + GAUDI · LIVE INFERENCE</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {isActive && (
            <div style={{ padding: '6px 16px', borderRadius: '4px', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.08em',
              background: isDone ? '#3e8635' : '#0068b5', color: '#fff', transition: 'background 0.5s' }}>
              {isDone ? 'COMPLETE' : 'LIVE'}
            </div>
          )}
          {isDone && (
            <button className="ck-mode-btn" onClick={resetDemo} style={{ fontSize: '0.72rem', padding: '5px 12px' }}>
              ← Back
            </button>
          )}
        </div>
      </div>

      {/* ===== IDLE ===== */}
      {demoState === 'idle' && (
        <>
          <div style={{ textAlign: 'center', margin: '32px 0 12px', color: '#ccc', fontSize: '0.95rem', fontWeight: 600 }}>Select a demo</div>

          {/* Scale selector */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '20px', alignItems: 'center' }}>
            <div style={{ fontSize: '0.68rem', color: '#666', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Scale:</div>
            <div className="ck-select">
              {SCALES.map(s => (
                <button key={s.id} className={scale === s.id ? 'active' : ''} onClick={() => setScale(s.id)}>
                  {s.label} ({s.count}) · {s.time}
                </button>
              ))}
            </div>
          </div>

          {/* Unlock code for extended */}
          {selectedScale.locked && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '12px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.68rem', color: '#666', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Unlock:</span>
              <input type="password" value={unlockCode} onChange={e => setUnlockCode(e.target.value)} placeholder="Required for extended"
                style={{ background: '#1e1e1e', border: '1px solid #333', borderRadius: '4px', padding: '4px 10px', color: '#ccc', fontSize: '0.78rem', width: '160px', fontFamily: 'RedHatMono, monospace' }} />
            </div>
          )}

          <div style={{ textAlign: 'center', marginBottom: '20px', fontSize: '0.7rem', color: '#555' }}>
            Live inference via LiteLLM · {selectedScale.count} requests · {selectedScale.time}
            {selectedScale.locked && !unlockCode && ' · unlock code required'}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '10px' }}>
            {DEMOS.map(d => (
              <div key={d.id} onClick={() => !launching && !(selectedScale.locked && !unlockCode) && launchDemo(d.id)} style={{
                background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '14px',
                cursor: (selectedScale.locked && !unlockCode) ? 'not-allowed' : 'pointer',
                opacity: (selectedScale.locked && !unlockCode) ? 0.5 : 1,
                transition: 'border-color 0.2s',
              }} onMouseEnter={e => { if (!(selectedScale.locked && !unlockCode)) e.currentTarget.style.borderColor = '#ee0000'; }}
                 onMouseLeave={e => (e.currentTarget.style.borderColor = '#2a2a2a')}>
                <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '4px' }}>{d.name}</div>
                <div style={{ fontSize: '0.75rem', color: '#888' }}>{d.desc}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ===== RUNNING + DONE (same layout, nothing disappears) ===== */}
      {isActive && demoMeta && (
        <>
          {/* Demo + Progress — persists through running → done */}
          <div style={{ background: '#141414', border: `1px solid ${isDone ? '#3e8635' : '#2a2a2a'}`, borderRadius: '8px', padding: '16px', marginBottom: '16px', transition: 'border-color 0.5s' }}>
            <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '2px' }}>{demoMeta.name}</div>
            <div style={{ fontSize: '0.78rem', color: '#888', marginBottom: '10px' }}>{demoMeta.desc}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
              <span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{completed} / {total || '...'}</span>
              <span style={{ color: isDone ? '#3e8635' : '#0068b5', fontWeight: 700 }}>{isDone ? 'DONE' : `${pct}%`}</span>
            </div>
            <div style={{ height: '6px', borderRadius: '3px', background: '#2a2a2a', overflow: 'hidden' }}>
              <div className="ck-smooth" style={{ height: '100%', width: `${pct}%`, background: isDone ? '#3e8635' : '#0068b5', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Phases — persist, advancing as completion grows */}
          <div style={{ marginBottom: '16px' }}>
            {demoMeta.phases.map((phase, i) => {
              const phaseThreshold = ((i + 1) / demoMeta.phases.length) * 100;
              const done = pct >= phaseThreshold;
              const active = !done && pct >= ((i) / demoMeta.phases.length) * 100;
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '5px 0', fontSize: '0.82rem' }}>
                  <div style={{ width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700,
                    background: done ? '#3e8635' : active ? '#0068b5' : '#2a2a2a', color: '#fff', flexShrink: 0, transition: 'background 0.3s' }}>
                    {done ? '✓' : active ? '▶' : '○'}
                  </div>
                  <span style={{ color: done ? '#3e8635' : active ? '#fff' : '#555', transition: 'color 0.3s' }}>{phase}</span>
                </div>
              );
            })}
          </div>

          {/* Timeline chart — builds during run, persists after */}
          {history.length > 0 && (
            <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#888', marginBottom: '8px' }}>
                {isDone ? 'Run Timeline' : 'Requests Over Time'}
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '60px' }}>
                {history.map((s, i) => {
                  const maxReqs = Math.max(...history.map(x => x.completed)) || 1;
                  return (
                    <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%' }}>
                      {s.gaudi > 0 && <div style={{ height: `${(s.gaudi / maxReqs) * 100}%`, background: '#e67e22', borderRadius: '1px 1px 0 0', minHeight: '2px' }} />}
                      {s.perf > 0 && <div style={{ height: `${(s.perf / maxReqs) * 100}%`, background: '#0068b5', minHeight: '2px' }} />}
                      {s.eco > 0 && <div style={{ height: `${(s.eco / maxReqs) * 100}%`, background: '#3e8635', borderRadius: '0 0 1px 1px', minHeight: '2px' }} />}
                    </div>
                  );
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#555', marginTop: '4px' }}>
                <span>0s</span>
                <span style={{ display: 'flex', gap: '10px' }}>
                  <span><span style={{ color: '#3e8635' }}>●</span> Eco</span>
                  <span><span style={{ color: '#0068b5' }}>●</span> Perf</span>
                  <span><span style={{ color: '#e67e22' }}>●</span> Gaudi</span>
                </span>
                <span>{history[history.length - 1]?.t || 0}s</span>
              </div>
            </div>
          )}

          {/* Lane totals — persist and climb */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
            {[
              { name: 'INTEL XEON ECO', hw: 'Granite · Xeon 6', count: eco, color: '#3e8635' },
              { name: 'INTEL XEON PERF', hw: 'CodeLlama · Xeon 6 + AMX', count: perf, color: '#0068b5' },
              { name: 'INTEL GAUDI', hw: 'Llama Scout 17B · Gaudi', count: gaudi, color: '#e67e22' },
            ].map(l => (
              <div key={l.name} style={{ background: '#141414', border: `1px solid ${l.count > 0 ? l.color : '#2a2a2a'}`, borderRadius: '6px', padding: '10px', borderLeft: `3px solid ${l.color}`, transition: 'border-color 0.3s' }}>
                <div style={{ fontWeight: 700, fontSize: '0.78rem', letterSpacing: '0.04em' }}>{l.name}</div>
                <div style={{ fontSize: '0.65rem', color: '#888' }}>{l.hw}</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace', color: l.color, marginTop: '4px' }}>
                  {l.count} <span style={{ fontSize: '0.72rem', color: '#888' }}>({totalReqs > 0 ? Math.round(l.count / totalReqs * 100) : 0}%)</span>
                </div>
              </div>
            ))}
          </div>

          {/* Summary stats — appear once we have data, persist */}
          {rps > 0 && (
            <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', fontSize: '0.82rem', flexWrap: 'wrap' }}>
              <span><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700, fontSize: '1rem' }}>{rps}</span> req/s</span>
              <span><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700, fontSize: '1rem' }}>{tps.toLocaleString()}</span> tok/s</span>
              <span><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700, fontSize: '1rem' }}>{p95}</span> ms p95</span>
              {images > 0 && <span><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700, fontSize: '1rem' }}>{images}</span> images</span>}
            </div>
          )}

          {/* Model telemetry — appears when data arrives, persists */}
          {Object.keys(models).length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#888', marginBottom: '8px', cursor: 'pointer' }}
                onClick={() => setShowTelemetry(!showTelemetry)}>
                {showTelemetry ? '▼' : '▶'} MODEL DETAIL
              </div>
              {showTelemetry && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
                  {Object.entries(models).map(([model, stats]) => (
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

          {/* Actions — only show when done */}
          {isDone && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="ck-mode-btn" onClick={() => activeDemo && launchDemo(activeDemo)}>Run Again</button>
              <button className="ck-mode-btn" onClick={resetDemo}>Try Another</button>
            </div>
          )}
        </>
      )}

      <div style={{ marginTop: '24px', fontSize: '0.65rem', color: '#444', textAlign: 'center' }}>
        Intel Xeon 6 + Gaudi — Red Hat OpenShift AI
      </div>
    </div>
  );
}
