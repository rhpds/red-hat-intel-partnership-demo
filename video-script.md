# Intel-Red Hat AI Inference Platform — Demo Video Script
## 8-10 min Technical Walkthrough (SAs & Engineers)

**Environment:** infra01 internal deployment
**URL:** https://frontend-intel-rh-demo.apps.ocpv-infra01.dal12.infra.demo.redhat.com

---

## Scene 1: Overview (0:00 – 1:00)

**Page:** Overview (landing page)

**CLICK:** Navigate to the site. The Overview page loads.

**SAY:**
> "This is the Intel-Red Hat AI Inference Platform — a multi-tenant inference gateway running on Red Hat OpenShift AI. The core idea is simple: not every AI task needs a GPU. Embedding a query takes milliseconds on a CPU. Generating a 2,000-word report needs GPU memory bandwidth. This platform routes each request to the right Intel hardware automatically — Xeon 6 for fast, cheap tasks, Gaudi 3 for heavy generation. On mixed workloads, this cuts inference costs by 60 to 80 percent compared to GPU-only."

---

## Scene 2: Architecture (1:00 – 2:00)

**CLICK:** Sidebar → Architecture

**SAY:**
> "Here's the architecture. The frontend talks to a FastAPI gateway, which routes requests through Red Hat's Model-as-a-Service LiteLLM proxy to Intel hardware. We have 17 models available across two hardware tiers — Xeon 6 with AMX acceleration for embeddings, classification, and small models, and Gaudi 3 with 128 gigs of HBM for large model generation."

**CLICK:** Scroll to the Semantic Department Routing table.

**SAY:**
> "The platform supports three routing strategies. Standard routes by task type and model size. Semantic Department classifies your query into one of six business departments and picks the domain-optimized model. And the vLLM Semantic Router uses signal-driven routing with OpenVINO on Xeon 6 — no LLM call for the routing decision itself."

---

## Scene 3: Routing Engine (2:00 – 3:30)

**CLICK:** Sidebar → Routing Engine

**SAY:**
> "The Routing Engine page shows how all three strategies work."

**CLICK:** Scroll to the Three Routing Strategies section.

**SAY:**
> "Standard routing is deterministic — embeddings always go to Xeon 6, large completions go to Gaudi. Semantic Department routing classifies your question — an HR question about PTO goes to a small cheap model on Xeon 6, an engineering question about Kubernetes goes to a 14-billion parameter model on Gaudi. The vLLM Semantic Router combines BM25 keyword signals with embedding intent signals to make the routing decision entirely on CPU — the KV cache stays on Gaudi for generation, routing intelligence runs on Xeon 6."

**CLICK:** Scroll down to Three Inference Lanes and the infrastructure status.

**SAY:**
> "Below that, you can see the three inference lanes — Eco, Performance, and Overdrive — each backed by specific Intel hardware. You can toggle lanes on and off to simulate hardware failure and see workloads reroute automatically."

---

## Scene 4: Try It Live (3:30 – 5:30)

**CLICK:** Sidebar → Try It Live

**SAY:**
> "Try It Live lets you run real inference calls and watch the routing in action. Let me start with the Enterprise RAG scenario."

**CLICK:** Select "Standard (task-type)" from the Routing Strategy dropdown (if not already selected).

**CLICK:** Click the "Technical question" scenario card.

**SAY:**
> "Watch the four steps execute. The embed query and vector search run on Xeon 6 using nomic-embed-text — fast and cheap. Reranking also stays on Xeon 6. Only the final generation step goes to Gaudi, where the 14-billion parameter model needs the GPU memory bandwidth."

**WAIT:** for the workflow to complete. Point out the latency and cost numbers.

**SAY:**
> "Total time under 10 seconds, cost fractions of a cent. Now let's switch the routing strategy and run the same question again."

**CLICK:** Change Routing Strategy dropdown to "vLLM Semantic Router."

**CLICK:** Click the same "Technical question" scenario card again.

**SAY:**
> "Same question, different strategy. Watch the Generate step — the vLLM Semantic Router classified this as an engineering question and selected a different model. The embedding and reranking steps stay the same because those are task-type routed regardless of strategy. But the generation model changed based on the semantic classification."

**CLICK:** Change to "Semantic Department" and run the same scenario.

**SAY:**
> "And with Semantic Department routing, the department classifier kicks in. Same question, potentially a different model and cost profile. This is the core value prop — the platform adapts the model to the workload, not the other way around."

---

## Scene 5: Interactive Chat (5:30 – 7:30)

**CLICK:** Sidebar → Interactive Chat

**SAY:**
> "The Interactive Chat shows the full RAG pipeline with document upload and streaming responses."

**CLICK:** Upload a document (have a PDF or markdown file ready — use one of the test docs already uploaded if available).

**SAY:**
> "Upload a document — PDF, markdown, code files. The system chunks it, embeds it with nomic-embed-text on Xeon 6, and stores the vectors in PostgreSQL with pgvector."

**CLICK:** Switch Routing Strategy to "vLLM Semantic Router."

**TYPE:** A question about the uploaded document, e.g., "What are the key points in this document?"

**CLICK:** Send.

**SAY:**
> "Watch the routing trace on the left. Embed query — Xeon 6. Vector search — pgvector. Rerank — Xeon 6. And the vLLM Semantic Router classified this as a general question and selected granite-3-2-8b on Xeon 6 — no GPU needed for this query. The response streams back in real time."

**CLICK:** Ask a more technical question, e.g., "Explain the security architecture in detail."

**SAY:**
> "Now a more technical question. Watch — the semantic router classifies this differently. It might route to a larger model on Gaudi for the deeper reasoning. You can see the routing decision, the model selected, latency, and cost right in the trace."

**CLICK:** Switch to "Standard" routing and ask the same question.

**SAY:**
> "Switch back to standard routing — same question goes to the default model. Three strategies, three different cost and performance profiles, all on the same hardware."

---

## Scene 6: Run at Scale (7:30 – 8:30)

**CLICK:** Sidebar → Run at Scale

**SAY:**
> "Finally, Run at Scale lets you simulate enterprise workload patterns — hundreds of requests across different task types, seeing how the routing engine distributes them across hardware tiers."

**CLICK:** Select a workload profile and run it (if the backend supports it on infra01).

**SAY:**
> "Each request routes independently. You can see the distribution — how many went to Xeon 6, how many to Gaudi, the aggregate latency and cost. This is what an enterprise inference platform looks like in production."

---

## Scene 7: Wrap-up (8:30 – 9:00)

**CLICK:** Navigate back to Overview.

**SAY:**
> "To summarize — this platform demonstrates three things. First, dual-path inference on Intel hardware cuts costs by routing the right task to the right silicon. Second, semantic routing with the vLLM Semantic Router on Xeon 6 makes intelligent model selection without burning GPU cycles on the routing decision. And third, it all runs on Red Hat OpenShift AI with enterprise features — multi-tenant isolation, Keycloak SSO, ArgoCD GitOps, and Prometheus observability. The entire demo is orderable on the Red Hat Demo Platform as an AI Quickstart."

---

## Pre-Recording Checklist

- [ ] infra01 deployment is running and healthy (check `/health` endpoint)
- [ ] Have 1-2 documents ready to upload in Interactive Chat (PDF or markdown)
- [ ] Screen resolution: 1920x1080, browser zoom 100%
- [ ] Close other browser tabs and notifications
- [ ] Test each page loads before recording
- [ ] Verify MAAS is responding (Try It Live → run one scenario to warm up)
- [ ] Clear chat session (click "New Chat" before recording Scene 5)
