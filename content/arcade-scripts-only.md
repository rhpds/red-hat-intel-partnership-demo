# Arcade Talk Track Scripts

## 5-Minute Executive

### Scene 1 — Landing Page (45s)

"This is the Intel–Red Hat AI Inference Platform. It solves a real problem enterprises face today: not every AI workload needs a GPU. A simple HR policy lookup doesn't need the same hardware as a deep security analysis — but most platforms route everything the same way."

"The platform has two hardware paths. Intel Xeon 6 with AMX handles small, fast tasks at a fraction of the cost. Intel GPU handles the heavy reasoning. Red Hat OpenShift AI ties them together with intelligent routing."

### Scene 2 — Architecture (45s)

"Here's the stack. Applications at the top, our routing engine in the middle, OpenShift AI managing the serving runtimes, all running on Intel hardware. The routing engine is the key — it classifies every request and sends it to the right hardware automatically."

"These are live. You can see each backend's health, what accelerator it's using, and its cost per thousand tokens. The Xeon 6 backends are a fraction of the GPU cost."

### Scene 3 — Live Workflow (90s)

"Let's run a real AI workflow. This is Enterprise RAG — Retrieval-Augmented Generation. Four steps, each routed to the right hardware."

"Watch what happens. The first three steps — embedding, search, and reranking — run on Xeon 6. They're lightweight operations that don't need a GPU. Only the final answer generation goes to GPU."

"Three of four steps on Xeon 6 at CPU pricing. The platform made that decision automatically based on what each step actually needs. That's where the cost savings come from — not by compromising quality, but by matching hardware to workload."

### Scene 4 — Scale (60s)

"One request is interesting. Let's see what happens at enterprise scale."

"This is an incident storm — 25 mixed requests hitting the platform simultaneously. Watch the live feed."

"Look at the hardware utilization. The platform automatically split the workload — lightweight tasks on Xeon 6, heavy reasoning on GPU. No manual configuration, no overprovisioning. Every request got the right hardware for its workload."

### Scene 5 — Close (30s)

"That's the Intel–Red Hat AI Inference Platform. Intelligent routing across Xeon 6 and GPU, running on OpenShift, with full governance and audit trails. It's available today as a Red Hat demo — we can have it running in your environment in under an hour."

---

## 10-Minute Technical

### Scene 1 — Landing Page (30s)

"This is the Intel–Red Hat AI Inference Platform — an intelligent routing layer that sends every AI workload to the right Intel hardware. Let me show you how it works."

### Scene 2 — Architecture (60s)

"Five layers. Applications on top, a routing engine that classifies every request, OpenShift AI managing the model serving, and two hardware paths at the bottom — Intel Xeon 6 for lightweight tasks, Intel GPU for heavy reasoning."

"These backends are live. Xeon 6 runs Granite 2B and Phi-3 Mini via OpenVINO — fast, cheap, good for classification, embedding, and simple Q&A. GPU runs larger models — Qwen 14B, DeepSeek R1, Phi-4 — for tasks that need real reasoning depth."

"Every routing decision is rule-based and auditable. The platform never makes a black-box decision — you can see exactly why each request went where it did."

### Scene 3 — Routing Engine Deep Dive (120s)

"The routing engine uses three lanes. Eco handles small requests up to 4K tokens on Xeon 6 — your HR lookups, simple classifications. Performance handles mid-range up to 16K tokens, also on Xeon 6 with AMX acceleration. Overdrive handles everything above 16K on GPU."

"A 500-token classification goes to Eco lane on Xeon 6. Look at the decision trace — four checks: endpoint healthy, capability match, tokens within limit, priority gate. All passed. This is the rubric the engine evaluates for every single request."

"A 24K-token summary goes to Overdrive on GPU. Same four checks, different outcome — the token count exceeded the Xeon 6 limit, so it routes to GPU automatically."

"Now watch what happens when GPU goes down. The platform detects the failure and reroutes to Xeon 6. Zero dropped requests. Higher latency, yes — but no outage. When GPU recovers, traffic flows back automatically."

### Scene 4 — Multi-Step Workflows (120s)

"Let's run real multi-step AI workflows. Each step in the pipeline gets routed independently."

"Enterprise RAG — four steps. Embed the query on Xeon 6, vector search on Xeon 6, rerank on Xeon 6, generate the answer on GPU. Three of four steps at CPU pricing."

"AIOps incident response. Classify severity on Xeon 6, find similar past incidents on Xeon 6, generate a root cause analysis on GPU, then a governance gate on Xeon 6 that checks whether the recommended action is safe to execute."

"This is where governance matters. The agent classifies intent, scores risk, generates an action plan on GPU, then the policy check on Xeon 6 decides whether to allow, escalate, or deny. Watch the risk score — anything above the threshold gets flagged."

### Scene 5 — Interactive Chat + RAG (120s)

"Let's go hands-on. This is a RAG-powered chat with document upload and real-time routing."

"I'll upload a real document. The platform chunks it, embeds it on Xeon 6, and stores the vectors in PostgreSQL with pgvector."

"Now watch the routing trace under each response. The embedding and search happen on Xeon 6, the answer generation on GPU. You can see the exact model, hardware, and latency for every step."

"Now I'm forcing it to Xeon 6 — Granite 2B. Faster, cheaper, but the answer quality may differ for complex questions. The platform lets you make that tradeoff explicitly, or let the router decide."

"With semantic routing, the platform classifies this as a Security question and routes to Phi-4 on GPU automatically. An HR question would go to Granite 2B on Xeon 6. The department taxonomy is fully customizable."

### Scene 6 — Close (30s)

"That's the full core demo. Intelligent routing across Intel Xeon 6 and GPU, multi-step workflow pipelines, RAG with document upload, governance controls, and full audit trails. All running on Red Hat OpenShift, deployable in under an hour. Let's talk about what this looks like in your environment."

---

## 15-Minute Deep Dive

### Scene 1 — Landing + Architecture (60s)

"Intel–Red Hat AI Inference Platform. Two hardware paths — Xeon 6 for lightweight AI tasks, GPU for heavy reasoning — with an intelligent routing engine that matches workload to hardware automatically."

"Five-layer stack. The routing engine sits between your application and the models. It classifies every request — task type, token count, priority — and sends it to the right backend. These backend cards are live — you can see health, accelerator type, and cost per thousand tokens."

### Scene 2 — Routing Engine (150s)

"Three lanes. Eco runs small requests on Xeon 6. Performance handles mid-range with AMX acceleration. Overdrive uses GPU for heavy workloads."

"500-token classification goes to Eco. Look at the decision trace — four rubric checks, all green. Endpoint healthy, capability match, tokens within limit, priority gate."

"24K-token summary goes to Overdrive on GPU. Same rubric, different outcome — token count exceeded the CPU threshold."

"Ten mixed requests. Watch the route distribution build — the engine splits them across lanes based on what each request actually needs."

"GPU goes down. Before: requests split across all three lanes. After: everything reroutes to Xeon 6. Zero dropped requests — higher latency but no outage. This is automatic graceful degradation with no application changes."

### Scene 3 — Multi-Step Workflows (90s)

"Real AI workflows, each step routed independently."

"Enterprise RAG. Embed on Xeon 6, search on Xeon 6, rerank on Xeon 6, generate on GPU. Three of four steps at CPU pricing — that's where the savings come from."

"AIOps incident response. Classify, search, root-cause analysis, governance gate. The governance step on Xeon 6 checks whether the recommended action is safe before executing."

"Governed agent with a high-risk action. Watch the risk score — it exceeds the threshold, so the platform escalates instead of executing. Every decision logged to the audit trail."

### Scene 4 — Interactive Chat + RAG (90s)

"Drag in a real document. The platform chunks it, embeds it on Xeon 6 using Nomic embeddings, stores vectors in PostgreSQL with pgvector."

"Watch the routing trace on the response — embedding and search on Xeon 6, answer generation on GPU. Real-time SSE streaming."

"Semantic routing classified that as a Security question and routed to Phi-4 on GPU automatically. An HR question about PTO policy would go to Granite 2B on Xeon 6. Six departments, each with its own model — fully customizable."

"In supervised mode, the platform flags high-risk responses for human review before they leave the system."

### Scene 5 — Cost Analysis (60s)

"Let's look at the economics. This is a 2,000-token incident report. The hardware routing threshold shows it falls in the Performance lane — Xeon 6 territory."

"Granite 2B on Xeon 6: fractions of a cent. DeepSeek R1 on GPU: several cents. Both give you a good answer for this workload — but at very different price points."

"At a million requests per month, routing small tasks to Xeon 6 instead of defaulting everything to GPU saves thousands of dollars. That's the core value proposition — same quality, right hardware, lower cost."

### Scene 6 — Agent Workflows (90s)

"Multi-step research agent with governance controls. Five steps: decompose the question on GPU, search the knowledge base on Xeon 6, rerank on Xeon 6, synthesize on GPU, content review on Xeon 6."

"In locked mode, every step requires human approval. You can see the sub-queries it generated, the documents it retrieved with relevance scores, and the governance decision at the end. Full transparency, full control."

### Scene 7 — Agent Swarm (60s)

"Multi-agent parallel execution. Five agents, three waves. Each agent routes to different hardware based on its task — a log analyzer runs on Xeon 6, a root cause reasoner runs on GPU."

"Look at the speedup — 2.5x faster than running sequentially. And the hardware utilization shows each agent went to the right lane automatically."

### Scene 8 — Resilience (45s)

"Three phases. Normal operation with GPU online. Hardware failure — GPU goes down, platform reroutes to Xeon 6. Recovery — GPU comes back, traffic rebalances."

"The headline: zero requests dropped across all three phases. Latency increased during the failure — that's expected — but no request was lost. This is production-grade resilience."

### Scene 9 — Governance Audit (45s)

"Every governed decision we made today is logged here. Time, source, intent classification, risk score, decision, who approved it. Click 'Evidence' on any row to see the full decision bundle — the exact inputs, model outputs, and policy evaluation that led to the decision."

"This is what enterprises need for compliance. Every AI-generated action has a full audit trail — who asked, what the model said, what risk it scored, and whether it was allowed, escalated, or denied."

### Scene 10 — Close (30s)

"That's the full platform. Intelligent routing across Intel Xeon 6 and GPU. Multi-step workflows, RAG with document upload, multi-agent orchestration, graceful degradation, cost optimization, and enterprise governance — all on Red Hat OpenShift. It's deployable today. Let's talk about running this in your environment."
