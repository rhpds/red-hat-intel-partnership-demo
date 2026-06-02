import {
  Card, CardBody, CardTitle, Content, Gallery, GalleryItem,
  Label, LabelGroup, PageSection, Spinner, Alert,
} from '@patternfly/react-core';
import { Table, Thead, Tr, Th, Tbody, Td } from '@patternfly/react-table';
import { useBackends, useRoutes } from '../api/hooks';
import HardwareBadge from '../components/HardwareBadge';
import RequestFlowDiagram from '../components/RequestFlowDiagram';
import WorkflowDiagrams from '../components/WorkflowDiagrams';

export default function Architecture() {
  const backends = useBackends();
  const routes = useRoutes();

  return (
    <>
      <PageSection>
        <Content>
          <Content component="h1">Platform Architecture</Content>
          <Content component="p" style={{ maxWidth: '720px' }}>
            This platform combines Red Hat OpenShift AI with Intel Xeon 6 and Gaudi hardware
            to deliver enterprise AI inference with intelligent, cost-aware routing. Red Hat
            provides the platform — OpenShift Container Platform, KServe model serving, operator
            lifecycle management, multi-tenant isolation, and observability. Intel provides
            two complementary hardware tiers. The routing engine bridges them.
          </Content>
        </Content>
      </PageSection>

      <PageSection variant="secondary">
        <Content><Content component="h2">Platform Stack</Content></Content>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', maxWidth: '720px', marginTop: '1rem', fontFamily: 'var(--pf-t--global--font--family--mono)' }}>
          {[
            { label: 'Applications', detail: 'Inference Gateway · React Dashboard · Workload Demos', color: 'var(--pf-t--global--color--brand--default)' },
            { label: 'Routing Engine', detail: 'Task evaluation · Hardware selection · Cost optimization · Decision logging', color: '#f0ab00' },
            { label: 'Red Hat OpenShift AI', detail: 'KServe model serving · ModelMesh · Data Science Pipelines · Workbenches', color: '#ee0000' },
            { label: 'Red Hat OpenShift Platform', detail: 'Operators · Keycloak SSO · ArgoCD GitOps · Prometheus · Namespace isolation', color: '#ee0000' },
            { label: 'Intel Hardware', detail: 'Xeon 6 (AMX) — embeddings, classification · Gaudi (HBM) — large model generation', color: '#0071c5' },
          ].map((layer, i) => (
            <div key={i} style={{ background: layer.color, color: '#fff', padding: '0.75rem 1rem', borderRadius: i === 0 ? '6px 6px 0 0' : i === 4 ? '0 0 6px 6px' : '0' }}>
              <strong>{layer.label}</strong>
              <br />
              <span style={{ fontSize: '0.85rem', opacity: 0.9 }}>{layer.detail}</span>
            </div>
          ))}
        </div>
      </PageSection>

      <PageSection>
        <Content><Content component="h2">Request Flow</Content></Content>
        <Content component="p" style={{ maxWidth: '720px', marginBottom: '1rem' }}>
          Every request enters through a single API gateway deployed on OpenShift.
          The routing engine evaluates the task and selects the optimal Intel hardware path.
          Results, routing decisions, and cost data are persisted to PostgreSQL and exported
          to Prometheus for monitoring via the OpenShift observability stack.
        </Content>
        <RequestFlowDiagram />
      </PageSection>

      <PageSection variant="secondary">
        <Content>
          <Content component="h2">Why the Routing Engine Exists</Content>
          <Content component="p" style={{ maxWidth: '720px', marginBottom: '0.5rem' }}>
            Real AI pipelines aren't single-step. A RAG pipeline embeds a query, searches a
            knowledge base, reranks candidates, then generates an answer. Each step has
            fundamentally different compute needs. Embeddings are small and fast — ideal for
            Xeon 6. Generation requires sustained memory bandwidth — ideal for Gaudi.
          </Content>
          <Content component="p" style={{ maxWidth: '720px', marginBottom: '1rem' }}>
            Without intelligent routing, enterprises either overpay (running everything on GPUs)
            or underperform (running everything on CPUs). The routing engine evaluates each step
            independently and routes it to the right hardware — cutting costs by 60-80% on
            mixed workloads while maintaining performance. Every decision is logged with full
            evidence so enterprises can audit, tune, and trust the system.
          </Content>
          <Content component="h3">Multi-Step Workflow Routing</Content>
        </Content>
        <WorkflowDiagrams />
      </PageSection>

      <PageSection variant="secondary">
        <Content><Content component="h2">Inference Backends</Content></Content>
        {backends.isLoading ? <Spinner aria-label="Loading" /> : backends.isError ? (
          <Alert variant="warning" title="Backends unavailable — gateway may still be starting">
            <p>Refresh the page once the gateway is ready.</p>
          </Alert>
        ) : (
          <Gallery hasGutter minWidths={{ default: '300px' }} style={{ marginTop: '1rem' }}>
            {backends.data?.backends.map((b) => (
              <GalleryItem key={b.name}>
                <Card isFullHeight>
                  <CardTitle><HardwareBadge accelerator={b.accelerator} /> {b.name}</CardTitle>
                  <CardBody>
                    <LabelGroup>{b.capabilities.map((c) => <Label key={c} isCompact>{c}</Label>)}</LabelGroup>
                    <Content component="small" style={{ marginTop: '0.5rem', display: 'block' }}>
                      ${b.cost_per_1k_tokens}/1K tokens | {b.healthy ? 'Online' : 'Offline'}
                    </Content>
                  </CardBody>
                </Card>
              </GalleryItem>
            ))}
          </Gallery>
        )}
      </PageSection>

      <PageSection>
        <Content><Content component="h2">Routing Rules</Content></Content>
        {routes.isLoading ? <Spinner aria-label="Loading" /> : routes.isError ? (
          <Alert variant="warning" title="Routes unavailable — gateway may still be starting" />
        ) : (
          <Table aria-label="Routing rules" variant="compact" style={{ marginTop: '1rem' }}>
            <Thead><Tr><Th>Task</Th><Th>Backend</Th><Th>Why</Th></Tr></Thead>
            <Tbody>
              {(routes.data?.routes || []).map((r, i) => (
                <Tr key={r.task + '-' + i}>
                  <Td><Label isCompact>{r.task}</Label></Td>
                  <Td>{r.backend || r.default_backend || 'conditional'}</Td>
                  <Td><em>{r.reason || ''}</em></Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </PageSection>

      <PageSection variant="secondary">
        <Content>
          <Content component="h3">The Partnership</Content>
          <Content component="p" style={{ maxWidth: '720px' }}>
            Intel provides the hardware diversity that makes cost-aware routing possible — Xeon 6
            for efficient inference, Gaudi for high-throughput generation. Red Hat provides the
            enterprise platform that makes it operational — OpenShift for container orchestration,
            KServe for model serving, operators for lifecycle management, and namespace isolation
            for multi-tenant delivery. The routing engine ties them together: every response
            includes which hardware was selected, why, the latency, and the cost — full
            transparency that enterprises require.
          </Content>
        </Content>
      </PageSection>
    </>
  );
}
