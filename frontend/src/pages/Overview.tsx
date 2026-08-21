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
            Intel Xeon 6 handles fast, small AI tasks cheaply. Intel GPU powers large models
            at scale. One gateway decides which hardware runs each request — and explains every decision.
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
                <Label color="blue" style={{ marginRight: '0.5rem' }}>Intel Xeon 6</Label>
                Efficient Inference
              </CardTitle>
              <CardBody>
                <Content>
                  <Content component={"p"}>
                    Embeddings, classification, and reranking run on Intel Xeon 6 with AMX
                    (Advanced Matrix Extensions) — hardware-accelerated matrix operations that make
                    AI inference 5-10x faster than standard CPUs, at a fraction of GPU cost.
                  </Content>
                  <Content component={"small"} style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>
                    $0.0004 per 1K tokens &bull; &lt;10ms latency &bull; Models up to 8B parameters
                  </Content>
                </Content>
              </CardBody>
            </Card>
          </GalleryItem>

          <GalleryItem>
            <Card isFullHeight>
              <CardTitle>
                <Label color="orange" style={{ marginRight: '0.5rem' }}>Intel GPU</Label>
                Large Model Generation
              </CardTitle>
              <CardBody>
                <Content>
                  <Content component={"p"}>
                    Large language models (17B+ parameters) need GPU memory bandwidth. Intel GPU
                    delivers 100+ tokens/sec generation with 128GB HBM — 10-20x faster than CPU for
                    tasks that demand sustained token generation.
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
                <Label color="red" style={{ marginRight: '0.5rem' }}>Red Hat OpenShift AI</Label>
                Enterprise Platform
              </CardTitle>
              <CardBody>
                <Content>
                  <Content component={"p"}>
                    Red Hat OpenShift provides the enterprise foundation: KServe for model serving,
                    Keycloak for SSO, ArgoCD for GitOps delivery, Prometheus for observability, and
                    namespace isolation for multi-tenant access — all managed by operators on
                    OpenShift Container Platform.
                  </Content>
                  <Content component={"small"} style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>
                    KServe model serving &bull; Multi-tenant isolation &bull; Operator-managed lifecycle
                  </Content>
                </Content>
              </CardBody>
            </Card>
          </GalleryItem>
        </Gallery>
      </PageSection>

      <PageSection variant="secondary">
        <Content>
          <Content component={"h2"}>Why We Built This</Content>
          <Content component={"p"} style={{ maxWidth: '720px' }}>
            GPU-only inference is expensive. CPU-only inference is too slow for large models.
            Enterprises need both — but manually deciding which hardware runs which task doesn't
            scale. We built a routing engine that solves this: it evaluates every request
            (task type, model size, token count, priority) and routes it to the optimal Intel
            hardware automatically.
          </Content>
          <Content component={"p"} style={{ maxWidth: '720px' }}>
            Red Hat OpenShift AI provides the platform that makes this possible at enterprise
            scale — KServe for model serving, operators for lifecycle management, namespace
            isolation for multi-tenant access, and a full observability stack. Intel provides
            the hardware diversity: Xeon 6 for cost-efficient inference, GPU for
            high-throughput generation. The routing engine is the bridge between them.
          </Content>
        </Content>
        <Content component={"h3"} style={{ marginTop: '1.5rem', marginBottom: '0.25rem' }}>The Demo in 4 Steps</Content>
        <Gallery hasGutter minWidths={{ default: '250px' }} style={{ marginTop: '0.5rem' }}>
          {[
            { num: '1', title: 'Architecture', desc: 'See the platform stack — Intel hardware, Red Hat OpenShift AI, and the routing engine that bridges them.', path: '/architecture' },
            { num: '2', title: 'Routing Engine', desc: 'Route a request. See the rubric evaluation, lane selection, and why Xeon 6 or GPU was chosen.', path: '/overdrive' },
            { num: '3', title: 'Try It Live', desc: 'Run RAG, AIOps, and Agent workflows. Watch each step route to the right hardware in real time.', path: '/try-it' },
            { num: '4', title: 'Run at Scale', desc: 'Simulate 25–1,000 requests. See cost savings from intelligent routing vs. GPU-only.', path: '/workload' },
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
