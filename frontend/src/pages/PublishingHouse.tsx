import { useState, useEffect } from 'react';
import { Card, CardBody, Content, Label, PageSection, Spinner } from '@patternfly/react-core';
import { api } from '../api/client';

interface PocItem {
  id: string;
  title: string;
  category: string;
  status: string;
  description: string;
  hardware: string[];
  tags: string[];
}

const STATUS_COLORS: Record<string, 'green' | 'blue' | 'orange' | 'grey'> = {
  live: 'green',
  'in-progress': 'blue',
  planned: 'orange',
};

const CATEGORY_COLORS: Record<string, 'green' | 'blue' | 'orange' | 'purple' | 'grey'> = {
  inference: 'blue',
  agents: 'orange',
  training: 'green',
  resilience: 'green',
  infrastructure: 'grey',
  security: 'purple',
};

export default function PublishingHouse() {
  const [items, setItems] = useState<PocItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const resp = await api.galleryPocs() as { items: PocItem[] };
        setItems(resp.items || []);
      } catch { /* ignore */ }
      setLoading(false);
    })();
  }, []);

  return (
    <>
      <PageSection>
        <Content>
          <Content component="h1">Publishing House</Content>
          <Content component="p" style={{ maxWidth: '780px', fontSize: '1.05rem' }}>
            The idea factory. Proof-of-concept gallery showcasing what's possible on the
            Intel-Red Hat AI Inference Platform. Each POC demonstrates a capability that
            partners can evaluate and build upon.
          </Content>
        </Content>
      </PageSection>

      <PageSection>
        {loading && <Spinner size="lg" />}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '12px' }}>
          {items.map(item => (
            <Card key={item.id} style={{ borderLeft: `3px solid ${item.status === 'live' ? '#3e8635' : item.status === 'in-progress' ? '#0068b5' : '#888'}` }}>
              <CardBody>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{item.title}</span>
                  <Label isCompact color={STATUS_COLORS[item.status] || 'grey'}>{item.status}</Label>
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <Label isCompact color={CATEGORY_COLORS[item.category] || 'grey'}>{item.category}</Label>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--rh-color--text-secondary)', marginBottom: '10px', lineHeight: '1.5' }}>
                  {item.description}
                </div>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '6px' }}>
                  {item.hardware.map(hw => (
                    <Label key={hw} isCompact color={hw.includes('Gaudi') ? 'orange' : hw.includes('TDX') ? 'purple' : 'blue'}>{hw}</Label>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {item.tags.map(tag => (
                    <span key={tag} style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '3px', background: 'var(--pf-t--global--background--color--secondary--default)', color: 'var(--pf-t--global--text--color--subtle)' }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      </PageSection>
    </>
  );
}
