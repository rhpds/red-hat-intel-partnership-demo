# Heterogeneous Compute Architecture

## Intel-Red Hat AI Inference Platform

### The Problem

Enterprises adopting AI inference face a binary choice: run everything on GPUs (expensive, wasteful for lightweight tasks) or run everything on CPUs (cheap, but inadequate for complex reasoning). Neither option fits the reality of production AI workloads, which are a mix of small, fast operations and large, compute-intensive ones — often within a single pipeline.

### The Solution: Workload-Aware Heterogeneous Routing

This platform eliminates the binary by combining two complementary Intel hardware tiers — CPU and GPU — under a single intelligent routing engine on Red Hat OpenShift. Every AI request is evaluated and routed to the hardware that best fits its compute profile. The result: GPU-class quality where it matters, CPU-class economics where it doesn't.

---

## Platform Stack

```
┌──────────────────────────────────────────────────────────────────┐
│  Applications                                                    │
│  Inference Gateway · React Dashboard · Workload Demos            │
├──────────────────────────────────────────────────────────────────┤
│  Routing Engine                                                  │
│  Task classification · Hardware selection · Cost optimization    │
│  Decision logging · Governance gates · Audit trails              │
├──────────────────────────────────────────────────────────────────┤
│  Red Hat OpenShift AI                                            │
│  KServe model serving · ModelMesh · Pipelines · Workbenches   v  │
├──────────────────────────────────────────────────────────────────┤
│  Red Hat OpenShift Container Platform                            │
│  Operators · Keycloak SSO · ArgoCD GitOps · Prometheus        v  │
│  Namespace isolation · Multi-tenant delivery                     │
├──────────────────────────────────────────────────────────────────┤
│  Intel Hardware                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐              │
│  │  Intel Xeon 6 (CPU)  │  │  Intel GPU           │              │
│  │  AMX acceleration    │  │  HBM bandwidth       │              │
│  │  OpenVINO runtime    │  │  vLLM runtime        │              │
│  │                      │  │                      │              │
│  │  Embeddings          │  │  Large generation    │              │
│  │  Classification      │  │  Complex reasoning   │              │
│  │  Reranking           │  │  Batch workloads     │              │
│  │  Small model (<4B)   │  │  Large model (>4B)   │              │
│  │  Search              │  │  Deep analysis       │              │
│  │  Governance checks   │  │                      │              │
│  └──────────────────────┘  └──────────────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

---

## How Heterogeneous Routing Works

### Request Flow

Every inference request enters through a single FastAPI gateway. The routing engine evaluates four dimensions before dispatching:

```
                            ┌─────────────────┐
                            │  Incoming       │
                            │  Request        │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Auth + Rate    │
                            │  Limit          │
                            └────────┬────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
              ┌──────▼──────┐ ┌─────▼──────-┐ ┌──────▼──────┐
              │  Standard   │ │  Semantic   │ │  vLLM       │
              │  Route      │ │  Dept Route │ │  Semantic   │
              │  (task +    │ │  (classify  │ │  Router     │
              │  model size)│ │  by intent) │ │  (signal-   │
              │             │ │             │ │  driven)    │
              └──────┬──────┘ └───-──┬──────┘ └─────┬────-──┘
                     │               │              │
                     └───────────────┼──────────────┘
                                     │
                            ┌────────▼────────┐
                            │  Backend        │
                            │  Selection      │
                            │  (Xeon 6 / GPU) │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Inference      │
                            │  (MAAS/LiteLLM) │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Post-process   │
                            │  + Log to DB    │
                            └─────────────────┘
```

Three routing strategies are available, selectable per request:

| Strategy | How It Works | Overhead | Best For |
|----------|-------------|----------|----------|
| **Standard** | Task type + model size → backend | 0ms | API workloads with known task types |
| **Semantic Department** | Classify query intent → department → model | 0-500ms | Interactive chat, unknown workloads |
| **vLLM Semantic Router** | Signal-driven keyword scoring → model | ~10ms | Production routing at scale |

### Standard Routing: Task + Model Size

The default strategy uses a rule-based routing table. Each task type maps to a backend, with model size as the tiebreaker for completions:

| Task | Backend | Hardware | Reasoning |
|------|---------|----------|-----------|
| Embeddings | maas-cpu | Xeon 6 | Vector math — AMX handles at wire speed |
| Classification | maas-cpu | Xeon 6 | Small model, low latency |
| Reranking | maas-cpu | Xeon 6 | Cross-encoder scoring, sub-second |
| Search | maas-cpu | Xeon 6 | Embedding similarity, no generation |
| Completion (≤4B) | maas-cpu | Xeon 6 | Small models fit CPU memory bandwidth |
| Completion (>4B) | maas-gpu | GPU | Large models need HBM throughput |
| Batch generation | maas-gpu | GPU | Sustained throughput workloads |
| Governance | maas-cpu | Xeon 6 | Fast policy checks via small model |

Every route has a fallback chain: primary backend → fallback backend → local inference (TinyLlama 1.1B). No request is ever dropped.

### Semantic Department Routing

For interactive or unknown workloads, the platform classifies user intent into one of seven enterprise departments, each mapped to an optimal model on the right hardware:

| Department | Model | Hardware | Why This Model |
|------------|-------|----------|---------------|
| HR | granite-2b-cpu | Xeon 6 | Simple policy lookups — smallest model sufficient |
| Engineering | qwen3-14b | GPU | Technical analysis needs reasoning |
| Legal | deepseek-r1-distill-qwen-14b | GPU | Legal precision requires deep reasoning |
| Finance | qwen3-14b | GPU | Financial analysis needs reasoning |
| Security | microsoft-phi-4 | GPU | Security analysis needs structured output |
| Executive | llama-31-70b | GPU | Strategic reasoning requires largest model |
| General | granite-2b-cpu | Xeon 6 | Default — fast TTFT for simple queries |

Four classification strategies run independently, and can be compared side by side:

1. **Rule-based** — keyword matching against department vocabularies. 0ms overhead, ~70% accuracy. Always available as a baseline.
2. **Embedding similarity** — cosine distance between the query embedding and department description embeddings via `nomic-embed-text-v1-5`. ~50ms overhead, ~85% accuracy.
3. **LLM classifier** — `granite-2b-cpu` classifies intent via a structured prompt. ~500ms overhead, ~90% accuracy.
4. **vLLM Semantic Router** — production-grade signal-driven routing using BM25 keyword scoring with OpenVINO on Xeon 6. ~10ms overhead, ~88% accuracy.

The platform calculates cost savings per department vs. a Claude Opus baseline ($15/M input tokens, $75/M output tokens), demonstrating the economic case for right-sized models on right-sized hardware.

---

## The Three-Lane Routing Engine (Overdrive)

For advanced workload management, the Overdrive engine extends standard routing with a three-lane model and rubric-based evaluation:

```
                    ┌──────────────────────────────────────────────────-─┐
                    │              Incoming Request                      │
                    │   task_type · token_estimate · priority · latency  │
                    └─────────────────────-─┬────────────────────────────┘
                                            │
                              ┌─────────────▼───────────-─┐
                              │    Routing Matrix         │
                              │    (25+ rules)            │
                              └────────────-─┬────────────┘
                                             │
                  ┌──────────────────────-──┬┴────────────────────────┐
                  │                         │                         │
         ┌────────▼────────┐      ┌─────────▼────────┐     ┌────────-─▼────────┐
         │     ECO         │      │   PERFORMANCE    │     │    OVERDRIVE      │
         │                 │      │                  │     │                   │
         │  granite-2b-cpu │      │  phi3-mini-cpu   │     │  deepseek-r1-14b  │
         │  Xeon 6         │      │  Xeon 6          │     │  GPU              │
         │  OpenVINO       │      │  OpenVINO        │     │  vLLM             │
         │                 │      │                  │     │                   │
         │  ≤4K tokens     │      │  ≤16K tokens     │     │  ≤64K tokens      │
         │  ≤8s latency    │      │  ≤5s latency     │     │  ≤10s latency     │
         │  any priority   │      │  normal+         │     │  high+            │
         └────────┬────────┘      └─────────┬────────┘     └────────-┬─────────┘
                  │                         │                        │
                  │    ┌────────────────────┘                        │
                  │    │ fallback (classification,                   │
                  │◄───┘  short_summary only)                        │
                  │                                                  │
                  │              ┌───────────────────────────────────┘
                  │              │ fallback (if <32K tokens)
                  │              ▼
                  │         PERFORMANCE
                  │
                  ▼
              RESPONSE
```

### Lane Capabilities

| Lane | Model | Hardware | Token Limit | Tasks |
|------|-------|----------|-------------|-------|
| **Eco** | granite-2b-cpu | Xeon 6 / OpenVINO | 4K | classification, image classification, screenshot classification |
| **Performance** | phi3-mini-cpu | Xeon 6 / OpenVINO | 16K | embedding, reranking, short/long summary, RAG Q&A, OCR, visual similarity |
| **Overdrive** | deepseek-r1-14b | GPU / vLLM | 64K | incident RCA, batch summary, code/document summary, chart interpretation, multimodal analysis |

### Rubric Evaluation

Every routing decision is validated against a 5-check rubric before dispatch:

| Check | What It Validates | Fail Action |
|-------|-------------------|-------------|
| Endpoint defined | Lane has a configured URL | Try fallback lane |
| Endpoint health | Backend responds to health probe | Try fallback lane |
| Supports task type | Lane's capability list includes this task | Try fallback lane |
| Token within limit | Request fits lane's max token capacity | Try fallback lane |
| Latency target met | Lane's max latency ≤ request's target | Try fallback lane |

If the primary lane fails rubric checks, the engine tries the fallback lane with health-only validation. If all lanes fail, the request queues for retry.

### Routing Matrix Rules

The matrix contains 25+ rules covering text and multimodal task types. Selection evaluates four dimensions:

- **Task type** — what kind of inference (classification, embedding, RAG question, incident RCA, etc.)
- **Token estimate** — request size drives hardware requirements
- **Priority** — low/normal/high/critical gates access to GPU resources
- **Latency target** — maximum acceptable response time

Key routing boundaries:

| Boundary | Below | Above |
|----------|-------|-------|
| 4K tokens | Eco (Xeon 6 / 2B) | Performance (Xeon 6 / 3.8B) |
| 16K tokens | Performance (Xeon 6 / 3.8B) | Overdrive (GPU / 14B) |
| Normal priority | Eco or Performance | Overdrive unlocked |
| 8s latency target | Eco | Performance or Overdrive |

---

## Multi-Step Pipeline Routing

Real AI workloads are not single-step. The platform routes each step of a pipeline independently, assigning each to the optimal hardware:

### Enterprise RAG Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌──────────-─┐    ┌────────────┐    ┌────────────┐
│ 1. Embed    │───▶│ 2. Search    │───▶│ 3. Rerank  │───▶│ 4. Generate│───▶│ 5. Govern  │
│   Xeon 6    │    │   Xeon 6     │    │   Xeon 6   │    │   GPU      │    │   Xeon 6   │
│   nomic-    │    │   pgvector   │    │  phi3-mini │    │  qwen3-14b │    │  granite-  │
│   embed     │    │              │    │            │    │            │    │  2b-cpu    │
│   $0.0004/1K│    │   $0.0004/1K │    │  $0.0004/1K│    │  $0.001/1K │    │  $0.0004/1K│
└─────────────┘    └──────────────┘    └──────────--┘    └────────────┘    └────────────┘
     CPU                CPU                CPU              GPU               CPU
```

**4 of 5 steps run on Xeon 6.** Only answer generation — which requires sustained memory bandwidth for large model inference — routes to GPU.

### Common Pipeline Patterns

Every pipeline follows this principle: use GPU only for steps that require it.

| Pipeline | Steps | CPU Steps | GPU Steps | CPU % |
|----------|-------|-----------|-----------|-------|
| **Enterprise RAG** | Embed → Search → Rerank → Generate → Govern | 4 | 1 | 80% |
| **AIOps Copilot** | Classify → Search → Root Cause → Govern | 2 | 1 | 75% |
| **Governed Agent** | Intent → Risk Score → Action Plan → Policy | 2 | 2 | 50% |
| **Research Agent** | Decompose → Search → Rerank → Synthesize → Review | 3 | 2 | 60% |
| **Multi-Agent Swarm** | 8 agents across 4 waves | 4-5 | 3-4 | ~60% |

The cost savings compound because the most frequent steps (embeddings, search, classification, governance) are also the lightest — they run on CPU at a fraction of GPU cost.

### Cost Impact

| Scenario | GPU-Only Cost | Heterogeneous Cost | Savings |
|----------|--------------|-------------------|---------|
| Single RAG query | $0.004 | $0.0022 | 45% |
| 1,000 mixed requests/day | $4.00 | $1.60 | 60% |
| 1M requests/month | $4,000 | $1,200 | 70% |

---

## Hardware Tiers

### Intel Xeon 6 (CPU Path)

- **Acceleration**: Intel AMX (Advanced Matrix Extensions) for INT8/BF16 matrix operations
- **Runtime**: OpenVINO optimized model serving
- **Models**: Granite 2B, Phi-3 Mini 3.8B, Qwen 2.5 3B (all ≤4B parameters)
- **Serving**: KServe InferenceService with OpenVINO runtime, 1-5 replicas, concurrency 10
- **Strengths**: Low latency for small models, high throughput for embeddings, cost-efficient at scale
- **Tasks**: Embeddings, classification, reranking, search, governance, policy checks, small-model Q&A
- **Cost**: $0.0004 per 1K tokens

### Intel GPU (GPU Path)

- **Acceleration**: HBM (High Bandwidth Memory) for large model parameter streaming
- **Runtime**: vLLM with Habana/Intel GPU integration
- **Models**: Qwen3 14B, DeepSeek R1 Distill 14B, Microsoft Phi-4, Llama 3.1 70B
- **Serving**: KServe InferenceService with vLLM Gaudi runtime, 1-3 replicas, concurrency 5
- **Strengths**: Complex reasoning, long-context generation, batch processing
- **Tasks**: Large model generation, multi-turn reasoning, deep analysis, batch workloads
- **Cost**: $0.001 per 1K tokens (2.5x CPU, still 95%+ below frontier API pricing)

### Why Two Tiers

Embeddings are mathematically simple — matrix multiplications on small vectors. Xeon 6 with AMX handles these at wire speed. Large model generation requires streaming billions of parameters through memory — GPU HBM provides the bandwidth. Using GPU for embeddings wastes expensive memory bandwidth on trivial math. Using CPU for 14B-parameter generation bottlenecks on memory throughput.

The routing engine matches the compute profile to the hardware profile — every request, every time.

---

## Resilience: Graceful Degradation

When GPU hardware fails, the platform does not drop requests. The routing engine detects the failure and reroutes to Xeon 6:

```
Phase 1 — Normal Operation
  Eco        → Xeon 6     ✓ healthy
  Performance → Xeon 6     ✓ healthy
  Overdrive  → GPU        ✓ healthy

Phase 2 — GPU Failure
  Eco        → Xeon 6     ✓ healthy
  Performance → Xeon 6     ✓ healthy
  Overdrive  → Xeon 6     ⚠ degraded (fallback, higher latency)

Phase 3 — Recovery
  Eco        → Xeon 6     ✓ healthy
  Performance → Xeon 6     ✓ healthy
  Overdrive  → GPU        ✓ restored
```

**Zero dropped requests** during the entire failure/recovery cycle. GPU-class requests continue on CPU with higher latency until recovery. No operator intervention required — the engine rebalances automatically when GPU health probes pass again.

The fallback chain at the infrastructure level mirrors this:

```
Primary backend → Fallback backend → Local inference (TinyLlama 1.1B)
```

Local inference is a last-resort TinyLlama model bundled in the gateway container itself, ensuring the platform can serve responses even if both MAAS backends are unreachable.

---

## Multi-Tenant Architecture

The platform supports isolated multi-tenant access for partner organizations:

```
┌─────────────────────────────────────────────────────────────────┐
│  Shared Infrastructure                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Gateway (intel-rh-inference-gateway)                       ││
│  │  JWT + API Key auth → Tenant resolution → Row-level security││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────-─┐  ┌─────────────-─┐  ┌──────────────┐         │
│  │ CPU Inference │  │ GPU Inference │  │  PostgreSQL  │         │
│  │ (shared)      │  │ (shared)      │  │  (RLS)       │         │
│  └─────────────-─┘  └────────────-──┘  └──────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  Tenant Namespaces                                              │
│  ┌───────────────┐  ┌──────────────-─┐  ┌───────────────┐       │
│  │ partner-acme  │  │ partner-initech│  │ partner-globex│       │
│  │               │  │                │  │               │       │
│  │ ResourceQuota │  │ ResourceQuota  │  │ ResourceQuota │       │
│  │ 8 CPU / 32Gi  │  │ 8 CPU / 32Gi   │  │ 8 CPU / 32Gi  │       │
│  │               │  │                │  │               │       │
│  │ LimitRange    │  │ LimitRange     │  │ LimitRange    │       │
│  │ NetworkPolicy │  │ NetworkPolicy  │  │ NetworkPolicy │       │
│  └───────────────┘  └───────────────-┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Isolation Boundaries

| Layer | Mechanism |
|-------|-----------|
| **Identity** | Keycloak SSO with per-tenant realm mappings; JWT carries tenant_id, slug, tier, scopes |
| **API access** | API keys (SHA256-hashed, `irh-` prefixed) scoped to tenant; 3 tiers (pilot, partner, internal) |
| **Data** | PostgreSQL row-level security — every table filtered by `app.current_tenant_id` session variable |
| **Compute** | Per-namespace ResourceQuota (8 CPU / 32Gi default) and LimitRange (max 4 CPU / 16Gi per container) |
| **Network** | NetworkPolicy: ingress only from gateway namespace, egress only to CPU/GPU inference namespaces + DNS |
| **Documents** | RAG documents tenant-scoped, auto-expire 24h, never shared across tenants |

---

## Enterprise Governance

Every routing decision is logged with full evidence:

- **Who** requested it (tenant, user, API key)
- **What** was classified (task type, token count, priority)
- **Where** it was routed (backend, hardware, model)
- **Why** it was routed there (rubric evaluation, check-by-check results)
- **Cost** incurred (tokens × rate)

### Governance Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Open** | Route and execute automatically | Development, trusted workloads |
| **Supervised** | Flag high-risk responses for human review | Production, sensitive domains |
| **Locked** | Require human approval at every step | Regulated industries, compliance |

The research agent pipeline demonstrates all three modes: in supervised mode, the synthesis step (which generates the final answer from retrieved documents) requires human approval before execution. In locked mode, every step — decompose, search, rerank, synthesize, and governance review — requires approval.

---

## Deployment Topology

The platform deploys on Red Hat OpenShift via three supported paths:

### RHDP (Red Hat Demo Platform) — Primary

```
Red Hat Demo Platform (Babylon)
  └── AgnosticV catalog item (agnosticv/intel-rh-inference/)
       └── Ansible workload playbook
            └── Helm chart (helm/)
                 ├── Gateway      (2 replicas, 500m-2 CPU, 2-4Gi)
                 ├── Frontend     (1 replica, nginx + oauth-proxy)
                 ├── PostgreSQL   (1 replica, pgvector, 10Gi PVC)
                 └── Routing config (ConfigMap from values.yaml)
```

Three tiers with progressive hardening:

| Tier | Gateway Replicas | Rate Limit | Storage | CPU Limit |
|------|-----------------|------------|---------|-----------|
| **dev** | 1 | disabled | 10Gi | 250m |
| **test** | 2 | 85 RPM | 10Gi | 2 CPU |
| **prod** | 3 | 120 RPM | 50Gi | 2 CPU |

### GitOps — ArgoCD

An ArgoCD Application pointing at `deploy/cluster/` provides continuous reconciliation. Manual sync policy ensures human approval before changes reach the cluster.

### Tekton CI/CD

A four-stage Tekton Pipeline runs in-cluster:

```
git clone → build gateway image → build frontend image → rollout restart
                  (parallel)
```

Container images publish to `quay.io/redhat-gpte/` with both SHA and `latest` tags.

---

## The Partnership

**Intel** provides the hardware diversity that makes heterogeneous routing possible — Xeon 6 with AMX for efficient small-model inference, GPU with HBM for high-throughput generation. Two tiers, each optimized for its class of workload.

**Red Hat** provides the enterprise platform that makes it operational — OpenShift for container orchestration, KServe for model serving, OpenVINO for CPU-optimized runtimes, operators for lifecycle management, namespace isolation for multi-tenant delivery, and observability for production monitoring.

**The routing engine** bridges them: every response includes which hardware was selected, why, the latency, and the cost — full transparency that enterprises require for compliance and cost management.

---

## Models Inventory

### GPU Models (via MAAS/LiteLLM on Intel GPU)

| Model | Parameters | Primary Use | Strengths |
|-------|-----------|-------------|-----------|
| qwen3-14b | 14B | Engineering, finance | Strong reasoning, code generation |
| deepseek-r1-distill-qwen-14b | 14B | Legal, deep analysis | Chain-of-thought reasoning, precision |
| microsoft-phi-4 | 14B | Security | Structured output, compact efficiency |
| llama-31-70b | 70B | Executive strategy | Largest available, complex reasoning |

### CPU Models (via MAAS/LiteLLM on Intel Xeon 6 + OpenVINO)

| Model | Parameters | Primary Use | Strengths |
|-------|-----------|-------------|-----------|
| granite-2b-cpu | 2B | HR, general, governance | Fast TTFT, classification, policy checks |
| phi3-mini-cpu | 3.8B | Reranking, summaries | Cross-encoder scoring, mid-range Q&A |
| qwen25-3b-cpu | 3B | General Q&A | Balanced quality/speed |
| nomic-embed-text-v1-5 | — | Embeddings | 768-dim vectors, AMX-accelerated |

### Local Fallback

| Model | Parameters | Purpose |
|-------|-----------|---------|
| TinyLlama 1.1B | 1.1B | Last-resort fallback bundled in gateway container |
