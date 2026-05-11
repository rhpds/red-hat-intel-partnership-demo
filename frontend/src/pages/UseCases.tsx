import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  CardTitle,
  Label,
  PageSection,
  
  Content,
  Grid,
  GridItem,
} from '@patternfly/react-core';
import { ArrowRightIcon } from '@patternfly/react-icons';

const useCases = [
  {
    title: 'Enterprise RAG',
    subtitle: 'Knowledge-powered Q&A',
    message: 'Run enterprise RAG on Intel hardware with Red Hat as the platform.',
    steps: [
      { label: 'Embed query', hw: 'Xeon 6', time: '<5ms' },
      { label: 'Vector search', hw: 'Local', time: '<1ms' },
      { label: 'Rerank candidates', hw: 'Xeon 6', time: '<10ms' },
      { label: 'Generate answer', hw: 'Gaudi', time: '<2s' },
    ],
    insight: 'Xeon 6 handles 3 of 4 stages. Gaudi only activates for heavyweight generation.',
    color: 'red' as const,
  },
  {
    title: 'AIOps Copilot',
    subtitle: 'From alert to governed action',
    message: 'Intel + Red Hat can power governed AIOps from signal to action.',
    steps: [
      { label: 'Classify severity', hw: 'Xeon 6', time: '<5ms' },
      { label: 'Find similar incidents', hw: 'Xeon 6', time: '<10ms' },
      { label: 'Generate RCA', hw: 'Gaudi', time: '<2s' },
      { label: 'Governance gate', hw: 'Policy', time: '<1ms' },
    ],
    insight: 'Fast triage on CPU, deep analysis on GPU, policy validation before any action.',
    color: 'red' as const,
  },
  {
    title: 'Governed Agent',
    subtitle: 'Autonomous actions with audit trails',
    message: 'AI agents need governed execution, not just inference.',
    steps: [
      { label: 'Classify intent', hw: 'Xeon 6', time: '<5ms' },
      { label: 'Score risk', hw: 'Xeon 6', time: '<5ms' },
      { label: 'Generate plan', hw: 'Gaudi', time: '<2s' },
      { label: 'Policy check', hw: 'Policy', time: '<1ms' },
    ],
    insight: 'Every action is classified, risk-scored, planned, and policy-checked with evidence.',
    color: 'red' as const,
  },
];

const hwColor = (hw: string) => {
  if (hw.includes('Xeon')) return 'blue';
  if (hw.includes('Gaudi')) return 'orange';
  return 'grey';
};

export default function UseCases() {
  const navigate = useNavigate();

  return (
    <>
      <PageSection>
        <Content>
          <Content component={"h1"}>What Can You Build?</Content>
          <Content component={"p"} style={{ maxWidth: '720px' }}>
            Three proof-of-concept applications built on the inference platform.
            Each routes multiple AI tasks across hardware tiers — showing that
            enterprise AI is not one model on one accelerator, but a governed
            pipeline across the right hardware for each stage.
          </Content>
        </Content>
      </PageSection>

      {useCases.map((uc) => (
        <PageSection key={uc.title} variant="secondary" style={{ borderTop: '1px solid var(--pf-t--global--border--color--default)' }}>
          <Grid hasGutter>
            <GridItem span={5}>
              <Content>
                <Content component={"h2"}>
                  <Label color={uc.color} style={{ marginRight: '0.5rem' }}>{uc.title}</Label>
                </Content>
                <Content component={"h3"} style={{ fontWeight: 400, color: 'var(--pf-t--global--text--color--subtle)' }}>
                  {uc.subtitle}
                </Content>
                <Content component={"p"} style={{ marginTop: '1rem' }}>
                  {uc.insight}
                </Content>
                <Content component={"blockquote"} style={{ marginTop: '1rem', borderLeft: '3px solid var(--pf-t--global--border--color--default)', paddingLeft: '1rem' }}>
                  "{uc.message}"
                </Content>
                <Button variant="link" onClick={() => navigate('/try-it')} style={{ marginTop: '1rem' }}>
                  Try this scenario <ArrowRightIcon />
                </Button>
              </Content>
            </GridItem>
            <GridItem span={7}>
              <Card>
                <CardTitle>Pipeline</CardTitle>
                <CardBody>
                  {uc.steps.map((step, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', gap: '1rem',
                      padding: '0.75rem 0',
                      borderBottom: i < uc.steps.length - 1 ? '1px solid var(--pf-t--global--border--color--default)' : 'none',
                    }}>
                      <Label isCompact style={{ width: '24px', textAlign: 'center' }}>{i + 1}</Label>
                      <span style={{ flex: 1 }}>{step.label}</span>
                      <Label color={hwColor(step.hw)} isCompact>{step.hw}</Label>
                      <span style={{ fontFamily: 'var(--pf-t--global--font--family--mono)', fontSize: '0.85rem', color: 'var(--pf-t--global--text--color--subtle)', width: '60px', textAlign: 'right' }}>
                        {step.time}
                      </span>
                    </div>
                  ))}
                </CardBody>
              </Card>
            </GridItem>
          </Grid>
        </PageSection>
      ))}
    </>
  );
}
