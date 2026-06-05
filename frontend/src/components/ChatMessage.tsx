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
  const [traceOpen, setTraceOpen] = useState(true);
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
        width: isUser ? 'auto' : '100%',
        maxWidth: isUser ? '70%' : '100%',
        background: isUser
          ? 'var(--pf-t--global--background--color--primary--default)'
          : 'var(--pf-t--global--background--color--secondary--default)',
        border: isUser ? '1px solid var(--pf-t--global--border--color--default)' : 'none',
        boxShadow: isUser ? 'none' : '0 1px 4px rgba(0,0,0,0.06)',
      }}>
        <CardBody style={{ padding: '1rem 1.25rem' }}>
          <Split hasGutter style={{ marginBottom: '0.75rem' }}>
            <SplitItem>
              {isUser
                ? <UserIcon style={{ color: 'var(--pf-t--global--icon--color--brand--default)' }} />
                : <RobotIcon style={{ color: 'var(--pf-t--global--icon--color--status--success--default)' }} />}
            </SplitItem>
            <SplitItem isFilled>
              <strong style={{ fontSize: '0.9rem' }}>{isUser ? 'You' : 'Assistant'}</strong>
            </SplitItem>
          </Split>

          <div style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: 1.7,
            fontSize: '0.95rem',
            maxHeight: streaming ? 'none' : '600px',
            overflowY: streaming ? 'visible' : 'auto',
          }}>
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
