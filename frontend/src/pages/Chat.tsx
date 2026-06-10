import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Alert,
  Button,
  Card,
  CardBody,
  Content,
  Label,
  PageSection,
  Split,
  SplitItem,
  TextArea,
} from '@patternfly/react-core';
import { PaperPlaneIcon, PlusCircleIcon } from '@patternfly/react-icons';
import ChatMessage from '../components/ChatMessage';
import DocumentUploader from '../components/DocumentUploader';
import ModelSelector from '../components/ModelSelector';
import { api } from '../api/client';
import type { TraceStep, CostInfo, UploadedDoc } from '../api/types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  trace?: TraceStep[];
  cost?: CostInfo;
}

const SESSION_KEY = 'intel-demo-chat-session';

export default function Chat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<UploadedDoc[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState('');
  const [currentTrace, setCurrentTrace] = useState<TraceStep[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [modelOverride, setModelOverride] = useState('auto');
  const [hardwareOverride, setHardwareOverride] = useState('auto');
  const [governanceMode, setGovernanceMode] = useState('supervised');
  const [routingStrategy, setRoutingStrategy] = useState('standard');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, streamingContent, scrollToBottom]);

  // Session management — persist in sessionStorage
  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) {
      setSessionId(stored);
    } else {
      createSession();
    }
  }, []);

  const createSession = async () => {
    try {
      const resp = await api.chatCreateSession({
        model_override: modelOverride === 'auto' ? undefined : modelOverride,
        hardware_override: hardwareOverride === 'auto' ? undefined : hardwareOverride,
        governance_mode: governanceMode,
      });
      setSessionId(resp.session_id);
      sessionStorage.setItem(SESSION_KEY, resp.session_id);
      setMessages([]);
      setDocuments([]);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create session');
    }
  };

  const handleNewChat = () => {
    sessionStorage.removeItem(SESSION_KEY);
    createSession();
  };

  const handleSend = async () => {
    if (!input.trim() || !sessionId || streaming) return;
    const userMessage = input.trim();
    setInput('');

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userMessage,
    };
    setMessages(prev => [...prev, userMsg]);

    setStreaming(true);
    setStreamingContent('');
    setCurrentTrace([]);

    try {
      const BASE_URL = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${BASE_URL}/v1/chat/sessions/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          model_override: modelOverride === 'auto' ? undefined : modelOverride,
          hardware_override: hardwareOverride === 'auto' ? undefined : hardwareOverride,
          routing_strategy: routingStrategy,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      if (!response.body) throw new Error('Response body unavailable');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let currentEvent = '';
      let content = '';
      const trace: TraceStep[] = [];
      let cost: CostInfo | undefined;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        for (const line of text.split('\n')) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5));
              if (currentEvent === 'step') {
                const step: TraceStep = { ...data, status: 'running' };
                if (trace.length > 0) trace[trace.length - 1].status = 'done';
                trace.push(step);
                setCurrentTrace([...trace]);
              } else if (currentEvent === 'token') {
                content += data.content || '';
                setStreamingContent(content);
              } else if (currentEvent === 'routing_decision') {
                if (trace.length > 0) {
                  trace[trace.length - 1].reason = data.reason;
                  trace[trace.length - 1].status = 'done';
                }
                setCurrentTrace([...trace]);
              } else if (currentEvent === 'done') {
                cost = data;
                trace.forEach(s => s.status = 'done');
                setCurrentTrace([...trace]);
              }
            } catch {
              // skip unparseable lines
            }
          }
        }
      }

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: content || 'No response generated.',
        trace,
        cost,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send message');
    } finally {
      setStreaming(false);
      setStreamingContent('');
      setCurrentTrace([]);
    }
  };

  const handleUpload = async (file: File) => {
    const result = await api.documentUpload(file);
    setDocuments(prev => [...prev, result]);
  };

  const handleDeleteDoc = (id: string) => {
    setDocuments(prev => prev.filter(d => d.id !== id));
    api.documentDelete(id).catch((e) => {
      setError(e instanceof Error ? e.message : 'Failed to delete document');
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <PageSection style={{ background: 'var(--pf-t--global--background--color--primary--default)', paddingBottom: '1rem' }}>
        <Split hasGutter>
          <SplitItem isFilled>
            <Content component="h1" style={{ fontSize: '1.5rem' }}>Interactive Chat — Intelligent Model Routing</Content>
            <Content component="p" style={{ color: 'var(--pf-t--global--text--color--subtle)', maxWidth: '720px' }}>
              Upload documents and ask questions across departments. The routing engine automatically selects
              the optimal Intel hardware and model for each query. Switch the <strong>Routing Strategy</strong> below
              to compare approaches and see how routing decisions change.
            </Content>
            <Content component="small" style={{ color: 'var(--pf-t--global--text--color--subtle)', display: 'block', marginTop: '0.5rem', maxWidth: '720px', lineHeight: '1.5' }}>
              <strong>Standard</strong> — routes by task type and model size. Embeddings and classification stay on
              Xeon 6, large generation goes to Gaudi 3.{' '}
              <strong>Semantic Department</strong> — classifies your question by department (HR, Engineering, Legal,
              Finance, Security, Executive) and routes to the model optimized for that domain.{' '}
              <strong>vLLM Semantic Router</strong> — production-grade signal-driven routing with OpenVINO on Intel Xeon 6.
            </Content>
          </SplitItem>
          <SplitItem style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {sessionId && <Label color="green" isCompact>Session active</Label>}
            <Button variant="secondary" size="sm" onClick={handleNewChat}>
              <PlusCircleIcon style={{ marginRight: '0.25rem' }} /> New Chat
            </Button>
          </SplitItem>
        </Split>
      </PageSection>

      <PageSection isFilled style={{ display: 'flex', flexDirection: 'column', gap: '1rem', paddingBottom: 0 }}>
        {error && <Alert variant="danger" title={error} isInline />}

        <DocumentUploader documents={documents} onUpload={handleUpload} onDelete={handleDeleteDoc} />

        <Card style={{ flex: 1, overflow: 'hidden' }}>
          <CardBody style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 420px)', minHeight: '300px', padding: '1.5rem' }}>
            {messages.length === 0 && !streaming && (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--pf-t--global--text--color--subtle)' }}>
                Upload documents and start asking questions. Watch the routing trace to see which Intel hardware handles each step.
              </div>
            )}

            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                role={msg.role}
                content={msg.content}
                trace={msg.trace}
                cost={msg.cost}
              />
            ))}

            {streaming && (
              <ChatMessage
                role="assistant"
                content={streamingContent}
                trace={currentTrace}
                streaming
              />
            )}

            <div ref={messagesEndRef} />
          </CardBody>
        </Card>
      </PageSection>

      <PageSection style={{ paddingTop: '0.5rem' }}>
        <ModelSelector
          model={modelOverride}
          hardware={hardwareOverride}
          governance={governanceMode}
          routingStrategy={routingStrategy}
          onModelChange={setModelOverride}
          onHardwareChange={setHardwareOverride}
          onGovernanceChange={setGovernanceMode}
          onRoutingStrategyChange={setRoutingStrategy}
        />

        <Split hasGutter>
          <SplitItem isFilled>
            <TextArea
              value={input}
              onChange={(_e, val) => setInput(val)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              rows={2}
              isDisabled={streaming || !sessionId}
              style={{ resize: 'none' }}
            />
          </SplitItem>
          <SplitItem>
            <Button
              variant="primary"
              onClick={handleSend}
              isDisabled={!input.trim() || streaming || !sessionId}
              style={{ height: '100%' }}
            >
              <PaperPlaneIcon />
            </Button>
          </SplitItem>
        </Split>
      </PageSection>
    </>
  );
}
