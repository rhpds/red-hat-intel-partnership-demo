import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import '../styles/cockpit.css';

const DEMOS = [
  { id: 'incident_storm', name: 'Incident Storm', desc: 'Enterprise alert flood — classification on Xeon 6, RCA on Gaudi', hero: 'throughput', hw: 'Xeon 6 classifies, Gaudi analyzes', mode: 'drive' },
  { id: 'dashboard_storm', name: 'Dashboard Storm', desc: 'Operational screenshots — Xeon 6 classifies, Gaudi interprets charts', hero: 'images', hw: 'Multimodal: screenshots + charts', mode: 'drive' },
  { id: 'token_cannon_multimodal', name: 'Token Cannon', desc: 'Maximum multimodal generation — stress test Gaudi throughput', hero: 'tokens', hw: 'Heavy Gaudi generation', mode: 'drive' },
  { id: 'image_to_manual', name: 'Image to Manual', desc: 'Equipment photos → installation guides on Gaudi', hero: 'images', hw: 'Vision-language on Gaudi', mode: 'drive' },
  { id: 'model_race', name: 'Model Race', desc: 'Same tasks across all hardware — compare Xeon 6 vs Gaudi', hero: 'latency', hw: 'Cross-hardware comparison', mode: 'drive' },
  { id: 'visual_rag_barrage', name: 'Visual RAG', desc: 'Multimodal knowledge base — embed on Xeon 6, answer on Gaudi', hero: 'throughput', hw: 'Retrieval + generation', mode: 'drive' },
];

interface PlatformData {
  active_runs: Array<{ type: string; run_id: string; profile?: string; mode?: string; completed?: number; total?: number }>;
  latest_completed: Record<string, unknown> | null;
  live_progress: { completed: number; total: number; pct: number } | null;
  model_telemetry: Record<string, { count: number; avg_latency_ms: number; total_input_tokens: number; total_output_tokens: number; tokens_per_sec: number; tasks: Record<string, number> }>;
  task_telemetry: Record<string, { count: number; avg_latency_ms: number; lanes: Record<string, number> }>;
  aggregate: { mode: string; requests_per_second: number; estimated_tokens_per_second: number; p95_latency_ms: number; route_counts: Record<string, number>; total_images: number; total_documents: number };
}

// Lane colors used in _renderLanes
const MODEL_COLORS: Record<string, string> = { 'granite-4-0-h-tiny': '#00c853', 'codellama-7b-instruct': '#0071c5', 'llama-scout-17b': '#ff6d00' };
const MODEL_HW: Record<string, string> = { 'granite-4-0-h-tiny': 'Xeon 6 Eco', 'codellama-7b-instruct': 'Xeon 6 + AMX', 'llama-scout-17b': 'Gaudi' };

export default function CockpitDashboard() {
  const [data, setData] = useState<PlatformData | null>(null);
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [launching, setLaunching] = useState(false);
  const [showTelemetry, setShowTelemetry] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const d = await api.platformStatus() as unknown as PlatformData;
        setData(d);
        if (d.active_runs?.length > 0) {
          const wr = d.active_runs.find(r => r.type === 'workload');
          if (wr) setActiveDemo(wr.profile || null);
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
    setShowTelemetry(false);
    try { await api.workloadRun(profileId, 'drive', 42); } catch { /* ignore */ }
    setLaunching(false);
  };

  const isRunning = data?.active_runs?.some(r => r.type === 'workload') || false;
  const isComplete = !isRunning && data?.latest_completed != null;
  const lp = data?.live_progress;
  const agg = data?.aggregate;
  const rc = agg?.route_counts || {};
  const mt = data?.model_telemetry || {};
  const _tt = data?.task_telemetry || {}; void _tt;
  const demoMeta = DEMOS.find(d => d.id === activeDemo);
  const lcProfile = (data?.latest_completed as Record<string, unknown>)?.workload_profile as string;

  // Which state to show
  const showIdle = !isRunning && !isComplete;
  const showRunning = isRunning;
  const showComplete = isComplete;

  return (
    <div className="cockpit" style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>

      {/* Header — always visible */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, letterSpacing: '0.05em' }}>
            INFERENCE <span style={{ color: '#ee0000' }}>OVERDRIVE</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#888' }}>Intel Xeon 6 + Gaudi — Performance Cockpit</div>
        </div>
        {(showRunning || showComplete) && (
          <div style={{
            padding: '8px 20px', borderRadius: '6px', fontWeight: 700, fontSize: '0.88rem',
            letterSpacing: '0.08em', fontFamily: 'Red Hat Mono, monospace',
            background: isRunning ? '#0071c5' : '#00c853', color: '#fff',
          }}>
            {isRunning ? 'RUNNING' : 'COMPLETE'}
          </div>
        )}
      </div>

      {/* ===== IDLE STATE ===== */}
      {showIdle && (
        <>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#aaa', marginBottom: '8px' }}>SELECT A DEMO</div>
            <div style={{ fontSize: '0.82rem', color: '#666' }}>Each demo tells a different performance story across Intel hardware</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
            {DEMOS.map(demo => (
              <div key={demo.id} onClick={() => !launching && launchDemo(demo.id)} style={{
                background: '#141414', border: '1px solid #2a2a2a', borderRadius: '10px', padding: '16px',
                cursor: launching ? 'wait' : 'pointer', transition: 'border-color 0.2s, transform 0.15s',
              }}
                onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#0071c5'; (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#2a2a2a'; (e.currentTarget as HTMLDivElement).style.transform = 'none'; }}>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '4px' }}>{demo.name}</div>
                <div style={{ fontSize: '0.78rem', color: '#888', marginBottom: '8px' }}>{demo.desc}</div>
                <div style={{ fontSize: '0.72rem', color: '#555' }}>{demo.hw}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ===== RUNNING STATE ===== */}
      {showRunning && demoMeta && lp && (
        <>
          {/* Demo context */}
          <div style={{ background: '#141414', border: '1px solid #2a2a2a', borderRadius: '10px', padding: '20px', marginBottom: '16px' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '4px' }}>{demoMeta.name}</div>
            <div style={{ fontSize: '0.82rem', color: '#888', marginBottom: '12px' }}>{demoMeta.desc}</div>

            {/* Progress */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '6px' }}>
              <span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{lp.completed} / {lp.total} requests</span>
              <span style={{ color: '#0071c5', fontWeight: 700 }}>{lp.pct}%</span>
            </div>
            <div style={{ height: '8px', borderRadius: '4px', background: '#2a2a2a', overflow: 'hidden' }}>
              <div className="ck-smooth" style={{ height: '100%', width: `${lp.pct}%`, background: lp.pct < 100 ? '#0071c5' : '#00c853', borderRadius: '4px' }} />
            </div>
          </div>

          {/* Hero metric + secondary gauges */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div className="ck-gauge active" style={{ gridColumn: demoMeta.hero === 'images' ? 'auto' : 'auto' }}>
              <div className="ck-gauge-value" style={{ color: '#0071c5', fontSize: '2.5rem' }}>
                {demoMeta.hero === 'tokens' ? (agg?.estimated_tokens_per_second || 0).toLocaleString() :
                 demoMeta.hero === 'images' ? (agg?.total_images || 0) :
                 demoMeta.hero === 'latency' ? `${Math.round(agg?.p95_latency_ms || 0)}` :
                 Math.round(agg?.requests_per_second || 0)}
              </div>
              <div className="ck-gauge-label">
                {demoMeta.hero === 'tokens' ? 'TOKENS / SEC' :
                 demoMeta.hero === 'images' ? 'IMAGES PROCESSED' :
                 demoMeta.hero === 'latency' ? 'P95 LATENCY (MS)' : 'REQUESTS / SEC'}
              </div>
            </div>
            <div className="ck-gauge active">
              <div className="ck-gauge-value" style={{ color: '#00c853' }}>{Math.round(agg?.requests_per_second || 0)}</div>
              <div className="ck-gauge-label">REQ/S</div>
            </div>
            <div className="ck-gauge active">
              <div className="ck-gauge-value" style={{ color: agg && agg.p95_latency_ms > 500 ? '#ff6d00' : '#0071c5' }}>{Math.round(agg?.p95_latency_ms || 0)}</div>
              <div className="ck-gauge-label">P95 MS</div>
            </div>
          </div>

          {/* Lane cards */}
          {_renderLanes(rc)}
        </>
      )}

      {/* ===== COMPLETE STATE ===== */}
      {showComplete && (
        <>
          {/* Summary */}
          <div style={{ background: '#141414', border: '1px solid #00c853', borderRadius: '10px', padding: '20px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{(DEMOS.find(d => d.id === lcProfile) || { name: lcProfile }).name || 'Workload'}</div>
                <div style={{ fontSize: '0.82rem', color: '#888' }}>
                  {(data?.latest_completed as Record<string, unknown>)?.total_requests as number || 0} requests completed
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#00c853', fontFamily: 'Red Hat Mono, monospace' }}>
                  {Math.round(agg?.requests_per_second || 0)} req/s
                </div>
                <div style={{ fontSize: '0.78rem', color: '#888' }}>
                  {(agg?.estimated_tokens_per_second || 0).toLocaleString()} tok/s · p95 {Math.round(agg?.p95_latency_ms || 0)}ms
                </div>
              </div>
            </div>
          </div>

          {/* Lane cards */}
          {_renderLanes(rc)}

          {/* Multimodal */}
          {(agg?.total_images || 0) > 0 && (
            <div style={{ display: 'flex', gap: '20px', marginBottom: '16px', padding: '12px 16px', background: '#141414', border: '1px solid #2a2a2a', borderRadius: '8px' }}>
              <div><span style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace' }}>{agg?.total_images}</span> <span style={{ color: '#888', fontSize: '0.82rem' }}>images</span></div>
              <div><span style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace' }}>{agg?.total_documents}</span> <span style={{ color: '#888', fontSize: '0.82rem' }}>documents</span></div>
            </div>
          )}

          {/* Model telemetry */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#888', marginBottom: '8px', cursor: 'pointer' }}
              onClick={() => setShowTelemetry(!showTelemetry)}>
              {showTelemetry ? '▼' : '▶'} MODEL INFERENCE DETAIL
            </div>
            {showTelemetry && Object.keys(mt).length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
                {Object.entries(mt).map(([model, stats]) => (
                  <div key={model} style={{ background: '#141414', border: `1px solid ${MODEL_COLORS[model] || '#2a2a2a'}`, borderRadius: '8px', padding: '12px', borderLeft: `4px solid ${MODEL_COLORS[model] || '#555'}` }}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: MODEL_COLORS[model] || '#aaa' }}>{model}</div>
                    <div style={{ fontSize: '0.72rem', color: '#888', marginBottom: '6px' }}>{MODEL_HW[model] || ''}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px', fontSize: '0.78rem' }}>
                      <div><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{stats.count}</span> reqs</div>
                      <div><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{stats.avg_latency_ms.toFixed(0)}</span> ms</div>
                      <div><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{stats.total_input_tokens.toLocaleString()}</span> in</div>
                      <div><span style={{ fontFamily: 'Red Hat Mono, monospace', fontWeight: 700 }}>{stats.tokens_per_sec.toLocaleString()}</span> tok/s</div>
                    </div>
                    <div style={{ marginTop: '4px', display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
                      {Object.entries(stats.tasks).map(([t, c]) => (
                        <span key={t} style={{ fontSize: '0.65rem', padding: '1px 5px', borderRadius: '3px', background: '#2a2a2a', color: '#aaa' }}>{t}:{c}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="ck-mode-btn" onClick={() => lcProfile && launchDemo(lcProfile)}>Run Again</button>
            <button className="ck-mode-btn" onClick={() => { setActiveDemo(null); setData(prev => prev ? { ...prev, latest_completed: null } : null); }}>Try Another Demo</button>
          </div>
        </>
      )}

      {/* Footer */}
      <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#555' }}>
        <span>Intel Xeon 6 + Gaudi — Red Hat OpenShift AI</span>
        <span>{isRunning ? 'Live Telemetry' : showComplete ? 'Run Complete' : 'Ready'}</span>
      </div>
    </div>
  );
}

function _renderLanes(rc: Record<string, number>) {
  const total = Object.values(rc).reduce((a, b) => a + b, 0) || 1;
  const lanes = [
    { id: 'eco', name: 'XEON ECO', hw: 'Granite · Xeon 6', color: '#00c853' },
    { id: 'performance', name: 'XEON PERFORMANCE', hw: 'CodeLlama · Xeon 6 + AMX', color: '#0071c5' },
    { id: 'overdrive', name: 'GAUDI OVERDRIVE', hw: 'Llama Scout · Gaudi', color: '#ff6d00' },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '16px' }}>
      {lanes.map(lane => {
        const count = rc[lane.id] || 0;
        const pct = Math.round(count / total * 100);
        const active = count > 0;
        return (
          <div key={lane.id} className={`ck-lane ${lane.id === 'eco' ? 'eco' : lane.id === 'performance' ? 'performance' : 'overdrive'} ${active ? 'active' : ''}`} style={{ color: lane.color }}>
            <div className="ck-pulse" />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{lane.name}</div>
                <div style={{ fontSize: '0.68rem', color: '#888' }}>{lane.hw}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'Red Hat Mono, monospace' }}>{pct}%</div>
                <div style={{ fontSize: '0.68rem', color: '#888' }}>{count} reqs</div>
              </div>
            </div>
            <div className="ck-util-bar">
              <div className="ck-util-fill ck-smooth" style={{ width: `${pct}%`, background: lane.color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
