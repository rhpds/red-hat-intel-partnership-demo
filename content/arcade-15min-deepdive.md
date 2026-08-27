# Arcade Talk Track: The 15-Minute Deep Dive

**Audience**: Partner / Customer technical team  
**Duration**: 15–18 minutes  
**Goal**: Full platform tour — routing engine, workflows, chat, cost analysis, agents, resilience, governance audit  

---

## Scene 1: Landing + Architecture (60s)

**Page**: Overview (`/`) → Architecture (`/architecture`)

**Action**: Open the demo. Quick scan of landing page, then navigate to Architecture.

**Talk track**:
> "Intel–Red Hat AI Inference Platform. Two hardware paths — Xeon 6 for lightweight AI tasks, GPU for heavy reasoning — with an intelligent routing engine that matches workload to hardware automatically."

**Click**: Navigate to Architecture. Point out the stack diagram.

> "Five-layer stack. The routing engine sits between your application and the models. It classifies every request — task type, token count, priority — and sends it to the right backend. These backend cards are live — you can see health, accelerator type, and cost per thousand tokens."

**Click**: Navigate to "Routing Engine."

---

## Scene 2: Routing Engine (150s)

**Page**: Routing Engine (`/overdrive`)

### Single Request Routing (60s)

**Talk track**:
> "Three lanes. Eco runs small requests on Xeon 6. Performance handles mid-range with AMX acceleration. Overdrive uses GPU for heavy workloads."

**Click**: Route a classification at 500 tokens → Eco lane.

> "500-token classification goes to Eco. Look at the decision trace — four rubric checks, all green. Endpoint healthy, capability match, tokens within limit, priority gate."

**Click**: Route a long_summary at 24K tokens → Overdrive.

> "24K-token summary goes to Overdrive on GPU. Same rubric, different outcome — token count exceeded the CPU threshold."

### Batch + Failover (90s)

**Click**: Click "Run Batch Demo" (10 mixed requests).

> "Ten mixed requests. Watch the route distribution build — the engine splits them across lanes based on what each request actually needs."

**Wait**: Batch completes. Point out the stacked bar chart.

**Click**: Click "Simulate GPU Failure."

> "GPU goes down. Before: requests split across all three lanes. After: the controlled workload reroutes to Xeon 6. Higher latency, but the compatible fallback remains available. Requests with no viable backend must be queued, retried, or surfaced explicitly."

**Click**: Navigate to "Try It Live."

---

## Scene 3: Multi-Step Workflows (90s)

**Page**: Try It Live (`/try-it`)

**Talk track**:
> "Real AI workflows, each step routed independently."

**Click**: Run the first Enterprise RAG scenario.

> "Enterprise RAG. Embed on Xeon 6, search on Xeon 6, rerank on Xeon 6, generate on GPU. Three of four steps at CPU pricing — that's where the savings come from."

**Click**: Switch to AIOps Copilot, run a scenario.

> "AIOps incident response. Classify, search, root-cause analysis, governance gate. The governance step on Xeon 6 checks whether the recommended action is safe before executing."

**Click**: Switch to Governed Agent, run a risky scenario.

> "Governed agent with a high-risk action. Watch the risk score — it exceeds the threshold, so the platform escalates instead of executing. Every decision logged to the audit trail."

**Click**: Navigate to "Interactive Chat."

---

## Scene 4: Interactive Chat + RAG (90s)

**Page**: Interactive Chat (`/chat`)

**Click**: Upload a document (PDF or DOCX).

**Talk track**:
> "Drag in a real document. The platform chunks it, embeds it on Xeon 6 using Nomic embeddings, stores vectors in PostgreSQL with pgvector."

**Type**: Ask a question about the document. Send.

> "Watch the routing trace on the response — embedding and search on Xeon 6, answer generation on GPU. Real-time SSE streaming."

**Click**: Change Routing Strategy to "Semantic Department."

**Type**: Ask "What are the security implications of this document?"

> "Semantic routing classified that as a Security question and routed to Phi-4 on GPU automatically. An HR question about PTO policy would go to Granite 2B on Xeon 6. Six departments, each with its own model — fully customizable."

**Click**: Change Governance to "Supervised."

> "In supervised mode, the platform flags high-risk responses for human review before they leave the system."

**Click**: Navigate to "Tokenizer & Cost."

---

## Scene 5: Cost Analysis (60s)

**Page**: Tokenizer & Cost (`/tokenizer`)

**Click**: Select the "Long" preset (full incident report).

**Talk track**:
> "Let's look at the economics. This is a 2,000-token incident report. The hardware routing threshold shows it falls in the Performance lane — Xeon 6 territory."

**Click**: Point out the three cost comparison cards.

> "Granite 2B on Xeon 6: fractions of a cent. DeepSeek R1 on GPU: several cents. Both give you a good answer for this workload — but at very different price points."

**Click**: Scroll to the Enterprise Scale Projection table.

> "At a million requests per month, routing small tasks to Xeon 6 instead of defaulting everything to GPU saves thousands of dollars. That's the core value proposition — same quality, right hardware, lower cost."

**Click**: Navigate to "Research Agent."

---

## Scene 6: Agent Workflows (90s)

**Page**: Research Agent (`/agent`)

**Click**: Select a question, set Governance to "Locked." Click "Run Agent."

**Talk track**:
> "Multi-step research agent with governance controls. Five steps: decompose the question on GPU, search the knowledge base on Xeon 6, rerank on Xeon 6, synthesize on GPU, content review on Xeon 6."

**Wait**: The agent pauses at each step waiting for approval.

**Click**: Click "Approve & Continue" at each step.

> "In locked mode, every step requires human approval. You can see the sub-queries it generated, the documents it retrieved with relevance scores, and the governance decision at the end. Full transparency, full control."

**Click**: Navigate to "Agent Swarm."

---

## Scene 7: Agent Swarm (60s)

**Page**: Agent Swarm (`/swarm`)

**Click**: Select "Incident Investigation," set depth to "Full Investigation" (5 agents, 3 waves). Click "Launch Swarm."

**Talk track**:
> "Multi-agent parallel execution. Five agents, three waves. Each agent routes to different hardware based on its task — a log analyzer runs on Xeon 6, a root cause reasoner runs on GPU."

**Wait**: Waves execute. Point out the parallel execution visualization.

> "Look at the speedup — 2.5x faster than running sequentially. And the hardware utilization shows each agent went to the right lane automatically."

**Click**: Navigate to "Recovery & Resilience."

---

## Scene 8: Resilience (45s)

**Page**: Recovery & Resilience (`/recovery`)

**Click**: Click "Simulate Recovery Scenario."

**Talk track**:
> "Three phases. Normal operation with GPU online. Hardware failure — GPU goes down, platform reroutes to Xeon 6. Recovery — GPU comes back, traffic rebalances."

**Wait**: Simulation completes.

> "In this deterministic recovery run, every generated request completed across all three phases. Latency increased during the failure — that's expected — and the trace shows the fallback path. In production, requests are queued, retried, or surfaced explicitly if no compatible backend remains available."

**Click**: Navigate to "Governance Audit."

---

## Scene 9: Governance Audit (45s)

**Page**: Governance Audit (`/governance`)

**Talk track**:
> "Every governed decision we made today is logged here. Time, source, intent classification, risk score, decision, who approved it. Click 'Evidence' on any row to see the full decision bundle — the exact inputs, model outputs, and policy evaluation that led to the decision."

**Click**: Click "Evidence" on a row. Show the modal with the JSON evidence bundle.

> "This is what enterprises need for compliance. Every AI-generated action has a full audit trail — who asked, what the model said, what risk it scored, and whether it was allowed, escalated, or denied."

---

## Scene 10: Close (30s)

**Talk track**:
> "That's the full platform. Intelligent routing across Intel Xeon 6 and GPU. Multi-step workflows, RAG with document upload, multi-agent orchestration, graceful degradation, cost optimization, and enterprise governance — all on Red Hat OpenShift. It's deployable today. Let's talk about running this in your environment."

---

## Key Messages to Hit

1. **Workload-aware routing** — every request evaluated against a 4-check rubric
2. **Cost optimization at scale** — millions saved by routing small tasks to CPU
3. **Multi-step independence** — each pipeline step routed to optimal hardware
4. **Governance at every layer** — risk scoring, policy checks, locked mode, full audit trail
5. **Resilience controls** — demonstrated fallback during a controlled hardware-failure scenario
6. **Multi-agent scaling** — parallel execution with hardware-aware routing per agent
7. **Semantic intelligence** — department-based routing maps business context to models
8. **Enterprise-ready** — OpenShift, multi-tenant, SSO, auditable, deployable in an hour
