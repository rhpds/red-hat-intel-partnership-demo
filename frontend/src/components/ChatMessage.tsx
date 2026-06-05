import { Card, CardBody, ExpandableSection, Label, Split, SplitItem } from '@patternfly/react-core';
import { UserIcon, RobotIcon } from '@patternfly/react-icons';
import { useState } from 'react';
import RoutingTrace from './RoutingTrace';

interface TraceStep {
  step: string;
  hardware: string;
  model?: string;
  latency_ms?: number;
  results?: number;
  reason?: string;
  status?: string;
}

interface CostInfo {
  total_latency_ms: number;
  total_cost: number;
  total_tokens?: number;
  xeon_ms?: number;
  gaudi_ms?: number;
}

interface Props {
  role: 'user' | 'assistant';
  content: string;
  trace?: TraceStep[];
  cost?: CostInfo;
  streaming?: boolean;
  onSwitchHardware?: (stepName: string, hardware: string) => void;
}

export default function ChatMessage({ role, content, trace, cost, streaming, onSwitchHardware }: Props) {
  const [traceOpen, setTraceOpen] = useState(false);
  const isUser = role === 'user';

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '1rem',
      paddingLeft: isUser ? '4rem' : 0,
      paddingRight: isUser ? 0 : '4rem',
    }}>
      <Card isCompact style={{
        maxWidth: '80%',
        background: isUser
          ? 'var(--pf-t--global--background--color--primary--default)'
          : 'var(--pf-t--global--background--color--secondary--default)',
        border: isUser ? '1px solid var(--pf-t--global--border--color--default)' : 'none',
      }}>
        <CardBody>
          <Split hasGutter style={{ marginBottom: '0.5rem' }}>
            <SplitItem>
              {isUser ? <UserIcon /> : <RobotIcon />}
            </SplitItem>
            <SplitItem isFilled>
              <strong>{isUser ? 'You' : 'Assistant'}</strong>
            </SplitItem>
          </Split>

          <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
            {content}
            {streaming && <span style={{ animation: 'blink 1s infinite' }}>▌</span>}
          </div>

          {trace && trace.length > 0 && (
            <ExpandableSection
              toggleText={traceOpen ? 'Hide routing trace' : 'Show routing trace'}
              isExpanded={traceOpen}
              onToggle={(_e, expanded) => setTraceOpen(expanded)}
              style={{ marginTop: '0.75rem' }}
            >
              <RoutingTrace steps={trace} onSwitchHardware={onSwitchHardware} />
            </ExpandableSection>
          )}

          {cost && (
            <Split hasGutter style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--pf-t--global--text--color--subtle)' }}>
              <SplitItem><Label isCompact>{(cost.total_latency_ms / 1000).toFixed(1)}s</Label></SplitItem>
              <SplitItem><Label isCompact color="blue">${cost.total_cost.toFixed(4)}</Label></SplitItem>
              {cost.total_tokens && <SplitItem><Label isCompact>{cost.total_tokens} tokens</Label></SplitItem>}
            </Split>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
