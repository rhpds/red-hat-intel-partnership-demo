import { Label, Button, Split, SplitItem } from '@patternfly/react-core';
import { CheckCircleIcon, SyncAltIcon, InProgressIcon } from '@patternfly/react-icons';

interface TraceStep {
  step: string;
  hardware: string;
  model?: string;
  latency_ms?: number;
  results?: number;
  reason?: string;
  status?: string;
}

interface Props {
  steps: TraceStep[];
  onSwitchHardware?: (stepName: string, hardware: string) => void;
}

const HARDWARE_COLORS: Record<string, 'blue' | 'orange' | 'grey' | 'purple'> = {
  xeon6: 'blue',
  gaudi: 'orange',
  postgresql: 'purple',
  local: 'grey',
  auto: 'grey',
};

const HARDWARE_LABELS: Record<string, string> = {
  xeon6: 'Xeon 6',
  gaudi: 'Gaudi',
  postgresql: 'pgvector',
  local: 'Local',
  auto: 'Auto',
};

const STEP_LABELS: Record<string, string> = {
  embed_query: 'Embed query',
  vector_search: 'Vector search',
  rerank: 'Rerank',
  generate: 'Generate',
  governance: 'Governance',
};

export default function RoutingTrace({ steps, onSwitchHardware }: Props) {
  return (
    <div style={{ fontSize: '0.85rem' }}>
      {steps.map((step, i) => (
        <div key={i} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0',
          borderLeft: '2px solid var(--pf-t--global--border--color--default)',
          paddingLeft: '0.75rem',
          marginLeft: '0.5rem',
        }}>
          <span style={{ width: '1.2rem', textAlign: 'center' }}>
            {step.status === 'done' ? <CheckCircleIcon color="var(--pf-t--global--icon--color--status--success--default)" /> :
             step.status === 'running' ? <InProgressIcon style={{ animation: 'spin 1s linear infinite' }} /> :
             <span style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>{i + 1}.</span>}
          </span>
          <span style={{ minWidth: '8rem' }}>{STEP_LABELS[step.step] || step.step}</span>
          <Label isCompact color={HARDWARE_COLORS[step.hardware] || 'grey'}>
            {HARDWARE_LABELS[step.hardware] || step.hardware}
          </Label>
          {step.model && <span style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>{step.model}</span>}
          {step.latency_ms != null && <span style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>{step.latency_ms}ms</span>}
          {step.results != null && <span style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>{step.results} chunks</span>}
          {step.step === 'generate' && onSwitchHardware && step.status === 'done' && (
            <Split hasGutter>
              <SplitItem>
                <Button variant="link" size="sm" onClick={() => onSwitchHardware(step.step, step.hardware === 'gaudi' ? 'xeon6' : 'gaudi')}>
                  <SyncAltIcon /> Switch to {step.hardware === 'gaudi' ? 'Xeon 6' : 'Gaudi'}
                </Button>
              </SplitItem>
            </Split>
          )}
          {step.reason && (
            <div style={{ marginLeft: '1.7rem', color: 'var(--pf-t--global--text--color--subtle)', fontSize: '0.8rem' }}>
              ↳ {step.reason}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
