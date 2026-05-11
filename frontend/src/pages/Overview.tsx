import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  CardTitle,
  Gallery,
  GalleryItem,
  Label,
  PageSection,
  Split,
  SplitItem,
  
  Content,
} from '@patternfly/react-core';
import { ArrowRightIcon } from '@patternfly/react-icons';
import { useHealth } from '../api/hooks';

export default function Overview() {
  const navigate = useNavigate();
  const health = useHealth();

  return (
    <>
      <PageSection style={{ background: 'var(--pf-t--global--background--color--primary--default)', paddingBottom: '2rem' }}>
        <Content>
          <Content component={"h1"} style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
            Enterprise AI Inference Platform
          </Content>
          <Content component={"p"} style={{ fontSize: '1.15rem', maxWidth: '720px', color: 'var(--pf-t--global--text--color--subtle)' }}>
            Intel Xeon 6 and Gaudi accelerators, operated on Red Hat OpenShift AI.
            The gateway routes every request to the optimal hardware — and tells you why.
          </Content>
          <Split hasGutter style={{ marginTop: '1.5rem' }}>
            <SplitItem>
              <Button variant="primary" size="lg" onClick={() => navigate('/try-it')}>
                Try It Live <ArrowRightIcon style={{ marginLeft: '0.5rem' }} />
              </Button>
            </SplitItem>
            <SplitItem>
              <Button variant="secondary" size="lg" onClick={() => navigate('/architecture')}>
                See How It Works
              </Button>
            </SplitItem>
            <SplitItem style={{ marginLeft: '1rem', display: 'flex', alignItems: 'center' }}>
              <Label color={health.data?.status === 'healthy' ? 'green' : 'yellow'}>
                {health.data?.status === 'healthy' ? 'Platform Online' : 'Connecting...'}
              </Label>
            </SplitItem>
          </Split>
        </Content>
      </PageSection>

      <PageSection>
        <Gallery hasGutter minWidths={{ default: '320px' }}>
          <GalleryItem>
            <Card isFullHeight>
              <CardTitle>
                <Label color="blue" style={{ marginRight: '0.5rem' }}>Xeon 6</Label>
                Scale
              </CardTitle>
              <CardBody>
                <Content>
                  <Content component={"p"}>
                    Embeddings, classification, and reranking run on Intel Xeon 6 with AMX acceleration.
                    Fast, cost-efficient, and always available.
                  </Content>
                  <Content component={"small"} style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>
                    $0.001–0.002 per 1K tokens &bull; &lt;10ms latency &bull; Models up to 8B parameters
                  </Content>
                </Content>
              </CardBody>
            </Card>
          </GalleryItem>

          <GalleryItem>
            <Card isFullHeight>
              <CardTitle>
                <Label color="orange" style={{ marginRight: '0.5rem' }}>Gaudi</Label>
                Power
              </CardTitle>
              <CardBody>
                <Content>
                  <Content component={"p"}>
                    Large language model generation and batch processing on Intel Gaudi accelerators.
                    10–20x faster than CPU for heavyweight inference.
                  </Content>
                  <Content component={"small"} style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>
                    $0.001 per 1K tokens &bull; &lt;2s TTFT &bull; Models 8B–70B+ parameters
                  </Content>
                </Content>
              </CardBody>
            </Card>
          </GalleryItem>

          <GalleryItem>
            <Card isFullHeight>
              <CardTitle>
                <Label color="red" style={{ marginRight: '0.5rem' }}>OpenShift AI</Label>
                Operations
              </CardTitle>
              <CardBody>
                <Content>
                  <Content component={"p"}>
                    Intelligent routing, governance gates, full audit trail, and cost observability.
                    The platform selects the right hardware — you just send the request.
                  </Content>
                  <Content component={"small"} style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>
                    {health.data?.routes || '—'} routing rules &bull; Policy enforcement &bull; Every decision logged
                  </Content>
                </Content>
              </CardBody>
            </Card>
          </GalleryItem>
        </Gallery>
      </PageSection>

      <PageSection variant="secondary">
        <Content>
          <Content component={"h2"}>The Demo Story</Content>
          <Content component={"p"} style={{ maxWidth: '720px' }}>
            This platform doesn't just run models. It decides which hardware runs each request,
            explains why, measures the cost, and enforces governance — all in the routing response.
            That's what makes Intel + Red Hat credible for enterprise AI.
          </Content>
        </Content>
        <Gallery hasGutter minWidths={{ default: '250px' }} style={{ marginTop: '1rem' }}>
          {[
            { num: '1', title: 'See the Architecture', desc: 'Understand the routing logic and hardware tiers.', path: '/architecture' },
            { num: '2', title: 'Try It Live', desc: 'Send a request and watch the gateway route it.', path: '/try-it' },
            { num: '3', title: 'Explore Use Cases', desc: 'RAG, AIOps, and governed agents — built on this platform.', path: '/use-cases' },
            { num: '4', title: 'Check Operations', desc: 'Live request history, latency, cost, and routing distribution.', path: '/operations' },
          ].map((step) => (
            <GalleryItem key={step.num}>
              <Card isClickable isSelectable onClick={() => navigate(step.path)}>
                <CardTitle>
                  <Label style={{ marginRight: '0.5rem' }}>{step.num}</Label>
                  {step.title}
                </CardTitle>
                <CardBody>
                  <Content component={"p"}>{step.desc}</Content>
                </CardBody>
              </Card>
            </GalleryItem>
          ))}
        </Gallery>
      </PageSection>
    </>
  );
}
