import { Split, SplitItem, Select, SelectOption, MenuToggle } from '@patternfly/react-core';
import { useState } from 'react';

interface Props {
  model: string;
  hardware: string;
  governance: string;
  routingStrategy: string;
  onModelChange: (val: string) => void;
  onHardwareChange: (val: string) => void;
  onGovernanceChange: (val: string) => void;
  onRoutingStrategyChange: (val: string) => void;
}

const MODELS = ['auto', 'granite-2b-cpu', 'phi3-mini-cpu', 'deepseek-r1-distill-qwen-14b', 'microsoft-phi-4'];
const HARDWARE = ['auto', 'xeon6', 'gaudi'];
const GOVERNANCE = ['open', 'supervised', 'locked'];
const STRATEGIES = ['standard', 'semantic', 'vllm-sr'];

function ControlSelect({ label, value, options, onChange }: {
  label: string; value: string; options: string[]; onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <div style={{ fontSize: '0.75rem', marginBottom: '0.25rem', color: 'var(--pf-t--global--text--color--subtle)' }}>{label}</div>
      <Select
        isOpen={open}
        selected={value}
        onSelect={(_e, val) => { onChange(val as string); setOpen(false); }}
        onOpenChange={setOpen}
        toggle={(toggleRef) => (
          <MenuToggle ref={toggleRef} onClick={() => setOpen(!open)} isExpanded={open} style={{ minWidth: '10rem' }}>
            {value === 'auto' ? 'Auto' : value}
          </MenuToggle>
        )}
      >
        {options.map((opt) => (
          <SelectOption key={opt} value={opt}>
            {opt === 'auto' ? 'Auto-route'
              : opt === 'xeon6' ? 'Xeon 6 Only'
              : opt === 'gaudi' ? 'Gaudi Only'
              : opt === 'standard' ? 'Standard (task-type)'
              : opt === 'semantic' ? 'Semantic Department'
              : opt === 'vllm-sr' ? 'vLLM Semantic Router'
              : opt}
          </SelectOption>
        ))}
      </Select>
    </div>
  );
}

export default function ModelSelector({ model, hardware, governance, routingStrategy, onModelChange, onHardwareChange, onGovernanceChange, onRoutingStrategyChange }: Props) {
  return (
    <Split hasGutter style={{ padding: '0.5rem 0' }}>
      <SplitItem><ControlSelect label="Routing Strategy" value={routingStrategy} options={STRATEGIES} onChange={onRoutingStrategyChange} /></SplitItem>
      <SplitItem><ControlSelect label="Model" value={model} options={MODELS} onChange={onModelChange} /></SplitItem>
      <SplitItem><ControlSelect label="Hardware" value={hardware} options={HARDWARE} onChange={onHardwareChange} /></SplitItem>
      <SplitItem><ControlSelect label="Governance" value={governance} options={GOVERNANCE} onChange={onGovernanceChange} /></SplitItem>
    </Split>
  );
}
