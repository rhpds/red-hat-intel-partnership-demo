# Intel-Red Hat AI Inference Platform — Project Roadmap

**Primary POC:** Jonathan Kershaw (jkershaw@redhat.com)
**Last Updated:** 2026-06-12
**Jira:** [GPTEINFRA-16811](https://redhat.atlassian.net/browse/GPTEINFRA-16811)
**Repo:** [rhpds/red-hat-intel-partnership-demo](https://github.com/rhpds/red-hat-intel-partnership-demo)

---

## Strategic Direction

**Xeon-first messaging** — Intel marketing strategy leads with Xeon for AI inferencing. The demo demonstrates that not every AI task needs a GPU: embeddings, classification, reranking, and routing intelligence all run on Xeon 6 with AMX acceleration. Gaudi 3 is present for large model generation but is positioned as the secondary hardware tier.

The platform shows **60-80% cost reduction** on mixed workloads by routing the right task to the right silicon.

---

## Architecture

```
Frontend (React/PatternFly 6) → Gateway (FastAPI) → MAAS LiteLLM → Intel Hardware
                                      ↓                                  ↓
                                 PostgreSQL (pgvector)         Gaudi 3 GPU / Xeon 6 CPU
                                      ↓
                            vLLM Semantic Router (Xeon 6 / OpenVINO)
```

**Three Routing Strategies:**
| Strategy | How It Works | Routing Overhead |
|----------|-------------|-----------------|
| Standard | Task type + model size → hardware | 0ms |
| Semantic Department | Classifies query by department → domain-optimized model | ~50ms (rules) |
| vLLM Semantic Router | BM25 keywords + embedding signals → model selection | ~20ms (no LLM call) |

**Xeon 6 Workloads:** Embeddings (nomic-embed-text), classification (granite-2b), reranking (phi3-mini), routing intelligence (vLLM SR/OpenVINO), small generation (granite-2b, granite-3-2-8b)
**Gaudi 3 Workloads:** Large model generation (qwen3-14b, deepseek-r1-14b, llama-scout-17b)

---

## Milestone Timeline

### Completed

| Milestone | Date | Status |
|-----------|------|--------|
| Demo application (gateway + frontend + RAG chat) | May 2026 | ✅ Done |
| 1,437 tests across 75 test files | May 2026 | ✅ Done |
| Semantic department routing (6 departments, 4 strategies) | June 2026 | ✅ Done |
| Security hardening (SQL injection, prompt injection, race conditions) | June 10 | ✅ Done |
| Container images on Quay (`quay.io/rh-intel-demo/*`) | June 10 | ✅ Done |
| AgnosticV catalog items merged (cluster + tenant) | June 11 | ✅ Done |
| Sandbox pool `ai-qs-intel-inference` created | June 11 | ✅ Done |
| E2E provisioning on RHDP integration tier | June 11 | ✅ Done |
| vLLM Semantic Router service deployed | June 12 | ✅ Done |
| Showroom lab guide (Antora) rendering | June 11 | ✅ Done |
| Deployed to infra01 (internal) | June 10 | ✅ Done |

### Week 1 — June 12-18

| Milestone | Owner | Status | Notes |
|-----------|-------|--------|-------|
| Roadmap document created | Kersh | ✅ This document | |
| Schedule meeting with Nate (Jonathan Cuper) | Kersh | 🔲 Pending | ACLs, governance, search filters |
| Connect with Jamie Lean (Summit Connect) | Patrick → Kersh | 🔲 Pending | Patrick facilitating intro |
| Follow up with Stacy (planned labs/events) | Kersh | 🔲 Pending | Identify Intel-capable labs |
| Grant Bertrand dev catalog access | Kersh | 🔲 Pending | Needs ACL mechanism from Nate |
| Review Jennifer's Intel-Red Hat story content | Kersh | 🔲 Pending | Jennifer sharing content |

### Week 2 — June 19-25

| Milestone | Owner | Status | Dependency |
|-----------|-------|--------|------------|
| Configure ACLs for Intel personnel | Kersh | 🔲 Blocked | Employee list from Sridhar/Kevin |
| Catalog description/branding template | Kersh | 🔲 Pending | Jennifer's content + Nate input |
| Add Intel search filter on platform | Kersh | 🔲 Pending | Nate meeting |
| Demo video recorded (8-10 min technical) | Kersh | 🔲 Pending | Script ready, need to record |

### Week 3 — June 26-30

| Milestone | Owner | Status | Dependency |
|-----------|-------|--------|------------|
| Promote catalog items to prod (partner platform) | Kersh | 🔲 Pending | Nate approval + ACLs + branding |
| Communicate timeline to team | Kersh | 🔲 Pending | All above |

### August-September

| Milestone | Owner | Status | Notes |
|-----------|-------|--------|-------|
| September hands-on lab prep | Sridhar + Preston + Kersh | 🔲 Planning | Leverage Summit labs |
| Summit Connect event support | Kersh + Jamie Lean | 🔲 Planning | ~10-15 events |

---

## Container Images

| Image | Registry | Platform |
|-------|----------|----------|
| `quay.io/rh-intel-demo/inference-gateway:latest` | Public | linux/amd64 |
| `quay.io/rh-intel-demo/inference-frontend:latest` | Public | linux/amd64 |
| `quay.io/rh-intel-demo/semantic-router:latest` | Public | linux/amd64 |
| `docker.io/pgvector/pgvector:pg15` | Public | linux/amd64 |

---

## RHDP Catalog Items

| Item | Purpose | AgnosticV Path | Status |
|------|---------|----------------|--------|
| `ai-qs-intel-inference-cluster` | Base infra (Keycloak, RHOAI, GitOps) | `ai-quickstarts/ai-qs-intel-inference-cluster/` | ✅ Merged |
| `ai-qs-intel-inference-tenant` | Per-user workload (Helm/ArgoCD) | `ai-quickstarts/ai-qs-intel-inference-tenant/` | ✅ Merged |

---

## Key Contacts

| Person | Role | For |
|--------|------|-----|
| Jonathan Kershaw | Primary POC (RHDP) | All project matters |
| Patrick Rutledge | Backend support | Coordination, introductions |
| Nate (Jonathan Cuper) | Platform architect | Catalog governance, ACLs |
| Tony Kay | CI/CD pipeline | AgnosticV, provisioning |
| Andrew Jones | Sandbox API | Cluster onboarding |
| Ashok Jammula | GPU approval | Gaudi access, agnosticd |
| Jennifer Horvath | Intel marketing | Branding, storytelling content |
| Sridhar Kayathi | Intel technical | Employee list, use cases |
| Preston Davis | Intel sales | September lab qualification |
| Jamie Lean | Summit Connect | Event labs and agendas |
| Stacy | Events | Planned labs and events |

---

## Blockers

| Blocker | Owner | Impact |
|---------|-------|--------|
| Intel employee list for ACLs | Sridhar / Kevin | Blocks partner platform access |
| Jennifer's branding content | Jennifer Horvath | Blocks catalog description template |
| Nate meeting (governance) | Kersh to schedule | Blocks prod promotion + search filters |
| Patrick → Jamie Lean intro | Patrick Rutledge | Blocks Summit Connect lab planning |

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Gaudi hardware not available for live demos | Demo works fully on Xeon 6 via MAAS — Gaudi models served remotely, no local GPU needed |
| vLLM SR service not deployed on RHDP tenant | Smart fallback to rules-based classification; SR service deployed on infra01 for internal demos |
| Gateway image is 2.2 GB (slow pulls) | First pull is slow; subsequent deploys use cached layers. Pre-pull DaemonSet possible if needed |
| Intel employee list delayed | Dev catalog already accessible; prod promotion can proceed for RH-internal users first |
