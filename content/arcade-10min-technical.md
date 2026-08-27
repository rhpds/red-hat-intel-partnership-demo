# Arcade Talk Track: The 10-Minute Technical Demo

**Audience**: Partner / Customer technical decision-maker  
**Duration**: 8–10 minutes  
**Goal**: Full core demo — routing engine internals, multi-workflow execution, interactive chat with RAG  

---

## Scene 1: Landing Page (30s)

**Page**: Overview (`/`)

**Action**: Open the demo URL. Point out the live health badge.

**Talk track**:
> "This is the Intel–Red Hat AI Inference Platform — an intelligent routing layer that sends every AI workload to the right Intel hardware. Let me show you how it works."

**Click**: "See How It Works" button.

---

## Scene 2: Architecture (60s)

**Page**: Architecture (`/architecture`)

**Action**: Scroll through the stack diagram and backend cards.

**Talk track**:
> "Five layers. Applications on top, a routing engine that classifies every request, OpenShift AI managing the model serving, and two hardware paths at the bottom — Intel Xeon 6 for lightweight tasks, Intel GPU for heavy reasoning."

**Click**: Scroll to the live backend cards.

> "These backends are live. Xeon 6 runs Granite 2B and Phi-3 Mini via OpenVINO — fast, cheap, good for classification, embedding, and simple Q&A. GPU runs larger models — Qwen 14B, DeepSeek R1, Phi-4 — for tasks that need real reasoning depth."

**Click**: Scroll to the routing rules table.

> "Every routing decision is rule-based and auditable. The platform never makes a black-box decision — you can see exactly why each request went where it did."

**Click**: Navigate to "Routing Engine" in the sidebar.

---

## Scene 3: Routing Engine Deep Dive (120s)

**Page**: Routing Engine (`/overdrive`)

**Action**: The 3-lane architecture is visible.

**Talk track**:
> "The routing engine uses three lanes. Eco handles small requests up to 4K tokens on Xeon 6 — your HR lookups, simple classifications. Performance handles mid-range up to 16K tokens, also on Xeon 6 with AMX acceleration. Overdrive handles everything above 16K on GPU."

**Click**: Scroll to "Route a Request." Set Task Type to "classification", Token Estimate to 500, Priority to "normal." Click "Evaluate Route."

> "A 500-token classification goes to Eco lane on Xeon 6. Look at the decision trace — four checks: endpoint healthy, capability match, tokens within limit, priority gate. All passed. This is the rubric the engine evaluates for every single request."

**Click**: Change Task Type to "long_summary", Token Estimate to 24000. Click "Evaluate Route."

> "A 24K-token summary goes to Overdrive on GPU. Same four checks, different outcome — the token count exceeded the Xeon 6 limit, so it routes to GPU automatically."

**Click**: Scroll to "See It at Scale." Click "Simulate GPU Failure."

> "Now watch what happens when GPU goes down. In this controlled run, the platform detects the failure and reroutes every generated request to Xeon 6. Higher latency, yes — but the configured fallback remains available. When GPU recovers, traffic flows back automatically."

**Click**: Navigate to "Try It Live."

---

## Scene 4: Multi-Step Workflows (120s)

**Page**: Try It Live (`/try-it`)

**Talk track**:
> "Let's run real multi-step AI workflows. Each step in the pipeline gets routed independently."

### Enterprise RAG (40s)

**Click**: Click the first RAG scenario card.

> "Enterprise RAG — four steps. Embed the query on Xeon 6, vector search on Xeon 6, rerank on Xeon 6, generate the answer on GPU. Three of four steps at CPU pricing."

**Wait**: Pipeline completes.

### AIOps Copilot (40s)

**Click**: Switch to the "AIOps Copilot" tab. Click the first scenario.

> "AIOps incident response. Classify severity on Xeon 6, find similar past incidents on Xeon 6, generate a root cause analysis on GPU, then a governance gate on Xeon 6 that checks whether the recommended action is safe to execute."

**Wait**: Pipeline completes.

### Governed Agent (40s)

**Click**: Switch to "Governed Agent" tab. Click a scenario with a risky action (e.g., "decommission legacy server").

> "This is where governance matters. The agent classifies intent, scores risk, generates an action plan on GPU, then the policy check on Xeon 6 decides whether to allow, escalate, or deny. Watch the risk score — anything above the threshold gets flagged."

**Wait**: Pipeline completes. Point out the governance decision.

**Click**: Navigate to "Interactive Chat."

---

## Scene 5: Interactive Chat with RAG (120s)

**Page**: Interactive Chat (`/chat`)

**Talk track**:
> "Let's go hands-on. This is a RAG-powered chat with document upload and real-time routing."

**Click**: Drag a PDF or document into the upload area.

> "I'll upload a real document. The platform chunks it, embeds it on Xeon 6, and stores the vectors in PostgreSQL with pgvector."

**Wait**: Upload completes.

**Type**: Ask a question about the uploaded document. Send it.

> "Now watch the routing trace under each response. The embedding and search happen on Xeon 6, the answer generation on GPU. You can see the exact model, hardware, and latency for every step."

**Wait**: Response streams in via SSE.

**Click**: Change the Model dropdown from "auto" to "granite-2b-cpu."

**Type**: Ask the same question again.

> "Now I'm forcing it to Xeon 6 — Granite 2B. Faster, cheaper, but the answer quality may differ for complex questions. The platform lets you make that tradeoff explicitly, or let the router decide."

**Click**: Change Routing Strategy to "Semantic Department."

**Type**: Ask a security-related question.

> "With semantic routing, the platform classifies this as a Security question and routes to Phi-4 on GPU automatically. An HR question would go to Granite 2B on Xeon 6. The department taxonomy is fully customizable."

---

## Scene 6: Close (30s)

**Talk track**:
> "That's the full core demo. Intelligent routing across Intel Xeon 6 and GPU, multi-step workflow pipelines, RAG with document upload, governance controls, and full audit trails. All running on Red Hat OpenShift, deployable in under an hour. Let's talk about what this looks like in your environment."

---

## Key Messages to Hit

1. **Rubric-based routing** — every decision is auditable with a 4-check pipeline
2. **Multi-step workflows route each step independently** — 3 of 4 RAG steps on CPU
3. **Graceful degradation** — successful fallback in the controlled hardware-failure scenario
4. **Governance built in** — risk scoring, policy checks, escalation
5. **Semantic department routing** — automatic model selection by business domain
6. **Interactive + auditable** — every chat response shows its routing trace
