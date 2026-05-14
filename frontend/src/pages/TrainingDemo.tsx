import { useState, useCallback, useRef, useEffect } from 'react';
import {
  Alert,
  Button,
  Card,
  CardBody,
  Content,
  Gallery,
  GalleryItem,
  Label,
  MenuToggle,
  NumberInput,
  PageSection,
  Select,
  SelectOption,
  Spinner,
} from '@patternfly/react-core';
import { api } from '../api/client';

const TASKS = [
  { value: 'incident_rca_finetune', label: 'Incident RCA', desc: 'Fine-tune for better incident root cause analysis' },
  { value: 'openshift_troubleshooting_finetune', label: 'OpenShift Troubleshooting', desc: 'Tune for OpenShift-specific error explanations' },
  { value: 'dashboard_vision_finetune', label: 'Dashboard Vision', desc: 'Adapt multimodal model for dashboard interpretation' },
  { value: 'code_failure_finetune', label: 'Code Failure', desc: 'Tune coder model for build/test failure explanations' },
  { value: 'small_classifier_tune', label: 'Small Classifier', desc: 'Train lightweight classifier for Xeon-side utility' },
];

const MODELS: Record<string, Array<{ value: string; label: string }>> = {
  incident_rca_finetune: [{ value: 'qwen_2_5_7b', label: 'Qwen 2.5 7B' }, { value: 'llama_3_1_8b', label: 'Llama 3.1 8B' }],
  openshift_troubleshooting_finetune: [{ value: 'granite_ops_model', label: 'Granite Ops' }, { value: 'llama_3_1_8b', label: 'Llama 3.1 8B' }],
  dashboard_vision_finetune: [{ value: 'qwen_2_5_vl_7b', label: 'Qwen 2.5 VL 7B' }],
  code_failure_finetune: [{ value: 'qwen_2_5_coder_7b', label: 'Qwen 2.5 Coder 7B' }],
  small_classifier_tune: [{ value: 'phi_small_utility', label: 'Phi Small' }],
};

const DATASETS: Record<string, string> = {
  incident_rca_finetune: 'synthetic_incident_rca_v1',
  openshift_troubleshooting_finetune: 'synthetic_openshift_troubleshooting_v1',
  dashboard_vision_finetune: 'synthetic_dashboard_vision_v1',
  code_failure_finetune: 'synthetic_code_failure_v1',
  small_classifier_tune: 'synthetic_small_classifier_v1',
};

interface TrainingResult {
  training_run_id: string;
  status: string;
  base_model_name: string;
  demo_task: string;
  training_mode: string;
  hardware_lane: string;
  metrics: { train_loss_start: number; train_loss_end: number; training_duration_seconds: number; samples_seen: number; simulated: boolean };
  evaluation: { base_score: number; tuned_score: number; improvement: number; dimensions: Record<string, { base: number; tuned: number }> };
  loss_curve: number[];
  artifacts: { adapter_ref: string; model_card_ref: string };
  serving_candidate: { status: string; target_lane: string };
  report_md: string;
  model_card: string;
}

export default function TrainingDemo() {
  const [task, setTask] = useState('incident_rca_finetune');
  const [taskOpen, setTaskOpen] = useState(false);
  const [model, setModel] = useState('qwen_2_5_7b');
  const [modelOpen, setModelOpen] = useState(false);
  const [seed, setSeed] = useState(42);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<TrainingResult | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const models = MODELS[task];
    if (models && models.length > 0) setModel(models[0].value);
  }, [task]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const runTraining = useCallback(async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const resp = await api.trainingRun(task, model, DATASETS[task], 'mock_lora', seed) as { run_id: string };
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.trainingStatus(resp.run_id) as Record<string, unknown>;
          if (status.status === 'completed') {
            setResult(status as unknown as TrainingResult);
            setLoading(false);
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch { /* retry */ }
      }, 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Training failed');
      setLoading(false);
    }
  }, [task, model, seed]);

  const taskMeta = TASKS.find(t => t.value === task);
  const availableModels = MODELS[task] || [];

  return (
    <>
      <PageSection>
        <Content>
          <Content component="h1">Train + Serve</Content>
          <Content component="p" style={{ maxWidth: '780px', fontSize: '1.05rem' }}>
            Select an open-weight model and a training task. The platform simulates fine-tuning
            on Intel Gaudi, evaluates before vs after, and produces a serving-ready artifact.
            All training is simulated in this demo — designed to plug into real Gaudi training later.
          </Content>
        </Content>
      </PageSection>

      <PageSection variant="secondary">
        <Content component="h2" style={{ marginBottom: '0.75rem' }}>Configure Training Run</Content>
        <Card>
          <CardBody>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'flex-end' }}>
              <div style={{ minWidth: '220px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>Training Task</div>
                <Select toggle={(ref) => (<MenuToggle ref={ref} onClick={() => setTaskOpen(!taskOpen)} isExpanded={taskOpen} style={{ width: '220px' }}>{taskMeta?.label || task}</MenuToggle>)}
                  isOpen={taskOpen} onSelect={(_e, v) => { setTask(v as string); setTaskOpen(false); }} onOpenChange={setTaskOpen} selected={task}>
                  {TASKS.map(t => <SelectOption key={t.value} value={t.value} description={t.desc}>{t.label}</SelectOption>)}
                </Select>
              </div>
              <div style={{ minWidth: '200px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>Model</div>
                <Select toggle={(ref) => (<MenuToggle ref={ref} onClick={() => setModelOpen(!modelOpen)} isExpanded={modelOpen} style={{ width: '200px' }}>{availableModels.find(m => m.value === model)?.label || model}</MenuToggle>)}
                  isOpen={modelOpen} onSelect={(_e, v) => { setModel(v as string); setModelOpen(false); }} onOpenChange={setModelOpen} selected={model}>
                  {availableModels.map(m => <SelectOption key={m.value} value={m.value}>{m.label}</SelectOption>)}
                </Select>
              </div>
              <div style={{ minWidth: '100px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>Seed</div>
                <NumberInput value={seed} min={0} max={999999} onMinus={() => setSeed(Math.max(0, seed - 1))} onPlus={() => setSeed(seed + 1)}
                  onChange={(e) => { const v = parseInt((e.target as HTMLInputElement).value, 10); if (!isNaN(v)) setSeed(v); }} widthChars={6} />
              </div>
              <Button variant="primary" onClick={runTraining} isLoading={loading} isDisabled={loading}>
                Run Simulated Training
              </Button>
            </div>
            <div style={{ marginTop: '0.75rem', fontSize: '0.82rem', color: 'var(--rh-color--text-secondary)' }}>
              Dataset: <strong>{DATASETS[task]}</strong> | Mode: mock_lora | Hardware: Gaudi (simulated)
            </div>
          </CardBody>
        </Card>
      </PageSection>

      {error && <PageSection><Alert variant="danger" title={error} isInline /></PageSection>}
      {loading && <PageSection><Spinner size="lg" /> Running simulated training...</PageSection>}

      {result && (
        <>
          {/* Training Metrics */}
          <PageSection>
            <Content component="h2" style={{ marginBottom: '0.75rem' }}>
              Training Results
              <Label color="blue" isCompact style={{ marginLeft: '0.75rem' }}>SIMULATED</Label>
            </Content>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', maxWidth: '700px' }}>
              {[
                { label: 'Start Loss', value: result.metrics.train_loss_start.toFixed(3) },
                { label: 'End Loss', value: result.metrics.train_loss_end.toFixed(3) },
                { label: 'Samples', value: result.metrics.samples_seen.toLocaleString() },
                { label: 'Duration', value: `${result.metrics.training_duration_seconds.toFixed(0)}s` },
              ].map(m => (
                <Card key={m.label}><CardBody style={{ textAlign: 'center', padding: '1rem' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{m.value}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--rh-color--text-secondary)' }}>{m.label}</div>
                </CardBody></Card>
              ))}
            </div>

            {/* Loss Curve */}
            {result.loss_curve.length > 0 && (
              <div style={{ marginTop: '1.5rem', maxWidth: '500px' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '8px' }}>Loss Curve</div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '80px' }}>
                  {result.loss_curve.map((loss, i) => {
                    const maxLoss = Math.max(...result.loss_curve);
                    const height = (loss / maxLoss) * 100;
                    return (
                      <div key={i} style={{
                        flex: 1, height: `${height}%`, borderRadius: '2px 2px 0 0',
                        background: i < result.loss_curve.length / 2 ? 'var(--rh-color--gaudi)' : 'var(--rh-color--success)',
                        transition: 'height 0.3s',
                      }} title={`Step ${i + 1}: ${loss.toFixed(4)}`} />
                    );
                  })}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--rh-color--text-secondary)', marginTop: '4px' }}>
                  <span>Step 1 ({result.loss_curve[0].toFixed(3)})</span>
                  <span>Step {result.loss_curve.length} ({result.loss_curve[result.loss_curve.length - 1].toFixed(3)})</span>
                </div>
              </div>
            )}
          </PageSection>

          {/* Evaluation */}
          <PageSection variant="secondary">
            <Content component="h2" style={{ marginBottom: '0.75rem' }}>Before vs After Evaluation</Content>
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <Card style={{ flex: '1 1 200px', maxWidth: '250px' }}>
                <CardBody style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--rh-color--text-secondary)' }}>Base Model</div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--rh-color--brand)' }}>{(result.evaluation.base_score * 100).toFixed(0)}%</div>
                </CardBody>
              </Card>
              <Card style={{ flex: '1 1 200px', maxWidth: '250px', borderTop: '4px solid var(--rh-color--success)' }}>
                <CardBody style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--rh-color--text-secondary)' }}>Fine-Tuned</div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--rh-color--success)' }}>{(result.evaluation.tuned_score * 100).toFixed(0)}%</div>
                </CardBody>
              </Card>
              <Card style={{ flex: '1 1 200px', maxWidth: '250px' }}>
                <CardBody style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--rh-color--text-secondary)' }}>Improvement</div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--rh-color--xeon6)' }}>+{(result.evaluation.improvement * 100).toFixed(0)}%</div>
                </CardBody>
              </Card>
            </div>

            {result.evaluation.dimensions && (
              <div style={{ maxWidth: '600px' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '8px' }}>Score Breakdown</div>
                {Object.entries(result.evaluation.dimensions).map(([dim, scores]) => (
                  <div key={dim} style={{ marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '3px' }}>
                      <span style={{ textTransform: 'capitalize' }}>{dim.replace(/_/g, ' ')}</span>
                      <span style={{ fontFamily: 'var(--pf-t--global--font--family--mono)' }}>
                        {((scores as {base: number; tuned: number}).base * 100).toFixed(0)}% → {((scores as {base: number; tuned: number}).tuned * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ display: 'flex', height: '8px', borderRadius: '4px', overflow: 'hidden', background: 'var(--rh-color--surface-secondary)' }}>
                      <div style={{ width: `${(scores as {base: number}).base * 100}%`, background: 'var(--rh-color--brand)', opacity: 0.4 }} />
                      <div style={{ width: `${((scores as {tuned: number}).tuned - (scores as {base: number}).base) * 100}%`, background: 'var(--rh-color--success)' }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </PageSection>

          {/* Serving */}
          <PageSection>
            <Content component="h2" style={{ marginBottom: '0.75rem' }}>Serving Readiness</Content>
            <Gallery hasGutter minWidths={{ default: '200px' }}>
              <GalleryItem>
                <Card><CardBody>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>Status</div>
                  <Label color="green" style={{ fontSize: '0.88rem' }}>{result.serving_candidate?.status?.toUpperCase() || 'READY'}</Label>
                </CardBody></Card>
              </GalleryItem>
              <GalleryItem>
                <Card><CardBody>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>Target Lane</div>
                  <Label color={result.serving_candidate?.target_lane?.includes('gaudi') ? 'orange' : 'blue'}>
                    {result.serving_candidate?.target_lane || result.hardware_lane}
                  </Label>
                </CardBody></Card>
              </GalleryItem>
              <GalleryItem>
                <Card><CardBody>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>Artifact</div>
                  <div style={{ fontSize: '0.78rem', fontFamily: 'var(--pf-t--global--font--family--mono)' }}>
                    {result.artifacts?.adapter_ref || 'N/A'}
                  </div>
                </CardBody></Card>
              </GalleryItem>
            </Gallery>
            <Alert variant="info" isInline style={{ marginTop: '1rem', maxWidth: '600px' }} title="Simulated training">
              This is a simulated training run. The fine-tuned model artifact is a placeholder.
              In production, this would deploy to the {result.serving_candidate?.target_lane || 'gaudi_overdrive'} lane
              and serve through the existing inference routing engine.
            </Alert>
          </PageSection>
        </>
      )}
    </>
  );
}
