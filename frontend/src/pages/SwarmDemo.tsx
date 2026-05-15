import { useState, useEffect, useRef } from 'react';
import { Button, Card, CardBody, Content, Label, PageSection, Spinner } from '@patternfly/react-core';
import { api } from '../api/client';

const HW_COLORS: Record<string, string> = { xeon_eco: '#3e8635', xeon_performance: '#0068b5', gaudi_overdrive: '#e67e22' };
const HW_LABELS: Record<string, { label: string; color: 'green' | 'blue' | 'orange' }> = {
  xeon_eco: { label: 'Xeon 6 Eco', color: 'green' }, xeon_performance: { label: 'Xeon 6 + AMX', color: 'blue' }, gaudi_overdrive: { label: 'Gaudi', color: 'orange' },
};

interface AgentResult { agent_id: string; name: string; role: string; hardware_lane: string; hw_label: string; model: string; status: string; output: string; latency_ms: number; wave: number; }

export default function SwarmDemo() {
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState<AgentResult[]>([]);
  const [currentWave, setCurrentWave] = useState(0);
  const [done, setDone] = useState(false);
  const [finalReport, setFinalReport] = useState('');
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const runSwarm = async () => {
    setLoading(true); setAgents([]); setCurrentWave(0); setDone(false); setFinalReport(''); setExpandedAgent(null);
    try {
      const resp = await api.swarmRun('incident', 42) as { run_id: string };
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.swarmStatus(resp.run_id) as Record<string, unknown>;
          setAgents((s.agent_results as AgentResult[]) || []);
          setCurrentWave(s.current_wave as number || 0);
          if (s.status === 'completed') {
            setDone(true); setFinalReport(s.final_report as string || '');
            setLoading(false);
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch { /* retry */ }
      }, 800);
    } catch { setLoading(false); }
  };

  const waves = [
    { num: 1, label: 'Wave 1: Parallel Investigation', desc: 'Triage + Log Analysis + Metrics — Xeon 6 and Gaudi simultaneously', agents: ['triage', 'log_analyst', 'metrics'] },
    { num: 2, label: 'Wave 2: Root Cause Analysis', desc: 'RCA Agent synthesizes all Wave 1 findings on Gaudi', agents: ['rca'] },
    { num: 3, label: 'Wave 3: Executive Report', desc: 'Reporter generates final incident summary on Gaudi', agents: ['reporter'] },
  ];

  const agentMap = Object.fromEntries(agents.map(a => [a.agent_id, a]));
  const isIdle = agents.length === 0 && !loading;

  return (
    <>
      <PageSection>
        <Content>
          <Content component="h1">Agent Swarm</Content>
          <Content component="p" style={{ maxWidth: '780px', fontSize: '1.05rem' }}>
            Five specialized AI agents investigate a production incident simultaneously across
            Intel Xeon 6 and Gaudi. Fast tasks run on Xeon 6. Heavy reasoning runs on Gaudi.
            The swarm completes in seconds what a single agent would take minutes to do.
          </Content>
        </Content>
      </PageSection>

      {/* Launch */}
      {isIdle && (
        <PageSection variant="secondary">
          <Card style={{ maxWidth: '600px' }}>
            <CardBody>
              <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '8px' }}>Incident Investigation Swarm</div>
              <Content component="p" style={{ marginBottom: '12px', color: 'var(--rh-color--text-secondary)' }}>
                A P1 incident has been triggered: checkout service degradation with Gaudi memory pressure.
                The swarm dispatches 5 agents in 3 waves to investigate, analyze, and report.
              </Content>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                {['Triage (Xeon 6)', 'Log Analyst (Xeon 6)', 'Metrics (Gaudi)', 'RCA (Gaudi)', 'Reporter (Gaudi)'].map(a => (
                  <Label key={a} isCompact color={a.includes('Gaudi') ? 'orange' : a.includes('AMX') ? 'blue' : 'green'}>{a}</Label>
                ))}
              </div>
              <Button variant="primary" onClick={runSwarm}>Launch Swarm</Button>
            </CardBody>
          </Card>
        </PageSection>
      )}

      {/* Wave visualization */}
      {(loading || done) && (
        <PageSection>
          {waves.map((wave, wi) => {
            const waveAgents = wave.agents.map(id => agentMap[id]).filter(Boolean);
            const waveComplete = waveAgents.length === wave.agents.length && waveAgents.every(a => a.status === 'done');
            const waveActive = currentWave === wave.num && !waveComplete;
            const wavePending = currentWave < wave.num;

            return (
              <div key={wi} style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.75rem', fontWeight: 700, color: '#fff',
                    background: waveComplete ? '#3e8635' : waveActive ? '#0068b5' : '#555',
                    transition: 'background 0.3s',
                  }}>
                    {waveComplete ? '✓' : wave.num}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.88rem', color: wavePending ? 'var(--rh-color--text-secondary)' : 'var(--rh-color--text)' }}>{wave.label}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--rh-color--text-secondary)' }}>{wave.desc}</div>
                  </div>
                  {waveActive && <Spinner size="md" />}
                </div>

                {/* Agent cards */}
                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(wave.agents.length, 3)}, 1fr)`, gap: '8px', marginLeft: '38px' }}>
                  {wave.agents.map(agentId => {
                    const a = agentMap[agentId];
                    const isDone = a?.status === 'done';
                    const hw = HW_LABELS[a?.hardware_lane || 'xeon_eco'] || HW_LABELS.xeon_eco;
                    const isExpanded = expandedAgent === agentId;

                    return (
                      <Card key={agentId} style={{
                        borderLeft: `3px solid ${HW_COLORS[a?.hardware_lane || 'xeon_eco'] || '#555'}`,
                        opacity: a ? 1 : 0.4, cursor: isDone ? 'pointer' : 'default', transition: 'opacity 0.3s',
                      }} onClick={() => isDone && setExpandedAgent(isExpanded ? null : agentId)}>
                        <CardBody style={{ padding: '10px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                            <span style={{ fontWeight: 700, fontSize: '0.82rem' }}>{a?.name || agentId}</span>
                            <Label isCompact color={hw.color}>{hw.label}</Label>
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--rh-color--text-secondary)', marginBottom: '4px' }}>{a?.role || '...'}</div>
                          {isDone && (
                            <div style={{ fontSize: '0.72rem' }}>
                              <Label isCompact color="green">DONE</Label>
                              <span style={{ marginLeft: '6px', fontFamily: 'var(--pf-t--global--font--family--mono)' }}>{a.latency_ms.toFixed(0)}ms</span>
                            </div>
                          )}
                          {isExpanded && a?.output && (
                            <div style={{
                              marginTop: '8px', padding: '8px', borderRadius: '4px', fontSize: '0.78rem',
                              background: 'var(--rh-color--surface-secondary)', whiteSpace: 'pre-wrap', lineHeight: '1.5',
                              maxHeight: '200px', overflowY: 'auto',
                            }}>
                              {a.output}
                            </div>
                          )}
                        </CardBody>
                      </Card>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Final report */}
          {done && finalReport && (
            <Card style={{ marginTop: '16px', borderTop: '4px solid #3e8635' }}>
              <CardBody>
                <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '8px' }}>Swarm Output: Executive Incident Report</div>
                <div style={{ fontSize: '0.85rem', whiteSpace: 'pre-wrap', lineHeight: '1.6', padding: '12px', borderRadius: '6px', background: 'var(--rh-color--surface-secondary)' }}>
                  {finalReport}
                </div>
                <div style={{ marginTop: '12px', fontSize: '0.78rem', color: 'var(--rh-color--text-secondary)' }}>
                  5 agents · 3 waves · Intel Xeon 6 + Gaudi · Simulated
                </div>
                <Button variant="secondary" style={{ marginTop: '8px' }} onClick={() => { setAgents([]); setDone(false); setFinalReport(''); setCurrentWave(0); }}>
                  Run Again
                </Button>
              </CardBody>
            </Card>
          )}
        </PageSection>
      )}
    </>
  );
}
