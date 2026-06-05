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
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  trace?: TraceStep[];
  cost?: CostInfo;
}

interface UploadedDoc {
  id: string;
  filename: string;
  modality: string;
  category: string;
  chunk_count: number;
  content_warnings?: string[];
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
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body!.getReader();
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
    api.documentDelete(id).catch(() => {});
    setDocuments(prev => prev.filter(d => d.id !== id));
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
            <Content component="h1" style={{ fontSize: '1.5rem' }}>Interactive RAG Chat</Content>
            <Content component="p" style={{ color: 'var(--pf-t--global--text--color--subtle)' }}>
              Upload documents, ask questions, and watch the routing engine select hardware in real-time.
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
          <CardBody style={{ overflowY: 'auto', maxHeight: '50vh', padding: '1rem' }}>
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
          onModelChange={setModelOverride}
          onHardwareChange={setHardwareOverride}
          onGovernanceChange={setGovernanceMode}
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
