import { useState } from 'react';
import { Button, Card, CardBody, Content, Label, PageSection } from '@patternfly/react-core';
import { api } from '../api/client';

interface TenantCapacity {
  slug: string;
  display_name: string;
  tier: string;
  active: boolean;
  expires_at: string | null;
  resource_quota: Record<string, number>;
  active_runs: number;
}

export default function CapacityDashboard() {
  const [tenants, setTenants] = useState<TenantCapacity[]>([]);
  const [totalActive, setTotalActive] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadCapacity = async () => {
    setLoading(true);
    try {
      const resp = await api.capacityOverview() as { tenants: TenantCapacity[]; total_active_runs: number };
      setTenants(resp.tenants || []);
      setTotalActive(resp.total_active_runs || 0);
      setLoaded(true);
    } catch { setLoaded(true); }
    setLoading(false);
  };

  return (
    <>
      <PageSection>
        <Content>
          <Content component="h1">Capacity & Allocation</Content>
          <Content component="p" style={{ maxWidth: '780px', fontSize: '1.05rem' }}>
            Per-tenant resource allocation, quota usage, and active demo runs across the platform.
            Each partner gets isolated capacity with defined limits.
          </Content>
        </Content>
      </PageSection>

      <PageSection variant="secondary">
        <Button variant="primary" onClick={loadCapacity} isLoading={loading}>
          {loaded ? 'Refresh' : 'Load Capacity Data'}
        </Button>

        {loaded && (
          <>
            <div style={{ display: 'flex', gap: '16px', margin: '16px 0' }}>
              <Card style={{ flex: 1 }}>
                <CardBody style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--pf-t--global--font--family--mono)' }}>{tenants.length}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--rh-color--text-secondary)' }}>Total Tenants</div>
                </CardBody>
              </Card>
              <Card style={{ flex: 1 }}>
                <CardBody style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--pf-t--global--font--family--mono)', color: 'var(--rh-color--success)' }}>{tenants.filter(t => t.active).length}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--rh-color--text-secondary)' }}>Active</div>
                </CardBody>
              </Card>
              <Card style={{ flex: 1 }}>
                <CardBody style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--pf-t--global--font--family--mono)', color: '#0068b5' }}>{totalActive}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--rh-color--text-secondary)' }}>Active Runs</div>
                </CardBody>
              </Card>
            </div>

            {tenants.map(t => (
              <Card key={t.slug} style={{ marginBottom: '8px' }}>
                <CardBody>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem', marginRight: '8px' }}>{t.display_name}</span>
                      <Label isCompact color={t.tier === 'internal' ? 'blue' : t.tier === 'partner' ? 'orange' : 'green'}>{t.tier}</Label>
                      {!t.active && <Label isCompact color="grey" style={{ marginLeft: '4px' }}>Inactive</Label>}
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      {t.active_runs > 0 && <Label isCompact color="blue">{t.active_runs} running</Label>}
                      {t.expires_at && <span style={{ fontSize: '0.72rem', color: 'var(--rh-color--text-secondary)' }}>Expires: {new Date(t.expires_at).toLocaleDateString()}</span>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem' }}>
                    <span><strong>{t.resource_quota.cpu_cores || 0}</strong> CPU cores</span>
                    <span><strong>{t.resource_quota.memory_gb || 0}</strong> GB memory</span>
                    <span><strong>{t.resource_quota.gpu_count || 0}</strong> GPUs</span>
                  </div>
                </CardBody>
              </Card>
            ))}
            {tenants.length === 0 && (
              <Card><CardBody style={{ color: 'var(--rh-color--text-secondary)' }}>No tenants found. DB may not be connected.</CardBody></Card>
            )}
          </>
        )}
      </PageSection>
    </>
  );
}
