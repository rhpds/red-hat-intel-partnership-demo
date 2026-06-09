# Intel-Red Hat AI Inference Platform — Status & Next Steps

**Repo:** https://github.com/rhpds/red-hat-intel-partnership-demo  
**Updated:** 2026-06-01  
**Owner:** Jonathan Kershaw

---

## What This Is

A multi-tenant inference gateway that routes AI workloads across Intel hardware (Xeon 6 CPU and Gaudi GPU) on Red Hat OpenShift. Built as a demo/POC for partner enablement.

**Components:**
- **Gateway** — FastAPI service with hardware-aware routing engine ("Overdrive"), governance layer, content validation, and multi-tenant auth
- **Frontend** — React/PatternFly dashboard with cockpit, workload demos, research agent, and tenant admin
- **Database** — PostgreSQL for request logging, tenant management, run persistence, and audit trail
- **Inference** — KServe manifests for vLLM (CPU + Gaudi) and OpenVINO (embeddings), routed through MAAS
- **CI Packaging** — AgnosticD config and AgnosticV catalog skeleton for Babylon deployment pipeline

---

## What Was Done (2026-05-25)

### Security Hardening
- [x] JWT authentication: replaced raw base64 decode with PyJWT signature verification
- [x] SQL injection: added UUID validation guard on `set_tenant_context`
- [x] Auth default: unauthenticated requests now get read-only access, not admin
- [x] Removed `trust_remote_code=True` from HuggingFace tokenizer loading
- [x] Restricted CORS from `*` to localhost dev ports
- [x] Removed `privileged: true` from Tekton build steps
- [x] Removed `--tls-verify=false` from container pushes
- [x] Gitignored secret manifests (`deploy/database/secret.yaml`, `deploy/cluster/secrets-template.yaml`)
- [x] Removed `changeme` default API keys from Ansible playbook/role
- [x] Fixed GitHub Actions shell injection (inputs now via `env:` vars)
- [x] Replaced internal IPs with RFC 5737 documentation IPs in sample data
- [x] Removed MAAS rate limit/budget details from embedded knowledge base
- [x] Bumped `transformers` 4.47→4.53 and `PyJWT` 2.9→2.12 (Dependabot clean)

### CI Packaging (AgnosticD/AgnosticV)
- [x] Created `agnosticd-config/` with 6-stage deployment playbooks
- [x] Created `agnosticv-catalog/` with dev/test/prod variable overrides
- [x] All hardcoded values parameterized (images, replicas, resources, MAAS endpoint)
- [x] Secrets created from variables at deploy time, not from checked-in YAML

### MAAS/CNV Alignment
- [x] Default gateway routing goes through MAAS proxy (`maas-rhdp.apps.maas.redhatworkshops.io`)
- [x] CPU inference moved to optional `local-inference` profile in podman-compose
- [x] All dev ports bound to `127.0.0.1`
- [x] Added coordination notices to GPU deploy READMEs (Ashok approval required)
- [x] Added `docs/cnv-experiments.md` with MAAS usage and CNV policy

### Repo Setup
- [x] Pushed to `rhpds/red-hat-intel-partnership-demo` with clean single-commit history
- [x] Updated Tekton pipeline and GitOps application URLs to point to rhpds repo
- [x] 0 open Dependabot alerts
- [x] Pre-commit hook blocking secrets, tokens, internal URLs

### Inference & Routing (2026-05-26 — 2026-05-28)
- [x] Fixed MAAS inference: added `api_key` to maas-proxy backend config
- [x] Fixed `${VAR:-default}` env var resolution in routing policy
- [x] Deployed to infra01 cluster (gateway, frontend, postgres all healthy)
- [x] CPU models added to MAAS: granite-2b-cpu, phi3-mini-cpu, qwen25-3b-cpu
- [x] Dual-path routing working: classification/embeddings → CPU (Xeon 6 OpenVINO), large completions → GPU (Gaudi 3)
- [x] Overdrive lanes updated: eco=granite-2b-cpu, performance=phi3-mini-cpu, overdrive=deepseek-14b
- [x] Concurrent batch runner: workloads use ThreadPoolExecutor with per-mode concurrency
- [x] API key rotated, cluster secret updated

### RHDP Packaging (2026-06-01)
- [x] Created `ocp4-workload-intel-rh-inference-demo` role (standard agnosticd workload pattern)
- [x] Templates for all K8s manifests (namespace, secrets, configmap, postgres, gateway, frontend)
- [x] AgnosticV catalog updated to reference workload role
- [x] GitHub Actions workflow for container image builds
- [ ] **Blocked:** RHDP shared cluster for AI quickstarts not yet available

---

## Next Steps — Need Team Input

### For Ashok / Tony

1. **RHDP shared cluster timeline** — When will the shared cluster for AI quickstarts be available? The Summit quickstarts currently fail to provision because no shared clusters exist. Our demo is blocked on the same infrastructure.

2. **Catalog entry format** — Should we follow the `rh-ai-quickstart` pattern (app code + Showroom lab guide + Developer Hub template) or the agnosticd workload role pattern? We have the workload role ready at `ansible/roles/ocp4-workload-intel-rh-inference-demo/`.

3. **Image registry** — Confirm `quay.io/intel-redhat/` or provide the correct org. GitHub Actions workflow for builds is ready at `.github/workflows/build-images.yaml`.

4. **MAAS LiteLLM access** — Will the shared cluster have network access to `maas-rhdp.apps.maas.redhatworkshops.io`? Our demo depends on it for all inference.

5. **Showroom lab guide** — If following the quickstart pattern, we need a Showroom guide (like `rhpds/showroom-ai-quickstart-ai-product-recommender`). Should we create one?

### For Jonathan (Self)

6. **Test workload role on infra01** — Run the ocp4-workload role with `ACTION=create` against infra01 to validate end-to-end.

7. **Build and push images to quay.io** — Once registry access is confirmed, tag `v1.0.0` and push images.

8. **Create Showroom lab guide** — If that's the format needed, create a guided walkthrough of the demo features.

### Reference: AI Quickstart Ecosystem
- App repos: [github.com/rh-ai-quickstart](https://github.com/rh-ai-quickstart)
- Showroom guides: `rhpds/showroom-ai-quickstart-*`
- Developer Hub templates: [redhat-developer/aiquickstarttemplates](https://github.com/redhat-developer/aiquickstarttemplates)
- RHDP Skills Marketplace (new tooling): [rhpds/rhdp-skills-marketplace](https://github.com/rhpds/rhdp-skills-marketplace)

---

## Known Issues (from code review — not blocking)

These were identified during a full repo review. Fix as time allows.

### High Priority
- ~~In-memory rate limiter grows unboundedly~~ — FIXED: periodic eviction + 10K key cap
- In-memory run dicts (`_agent_runs`, `_training_runs`, `_swarm_runs`) have no cleanup
- Background threads in `router.py` create new event loops vs shared `asyncpg` pool — use `asyncio.run_coroutine_threadsafe()`
- Timing attack on unlock hash in `batch_runner.py` — use `hmac.compare_digest()`
- Kafka event producer silently swallows send errors and connection failures
- Frontend silently catches errors on 5+ pages (ReplayDemo, RecoveryDemo, SwarmDemo, TrainingDemo, CockpitDashboard)
- Missing `securityContext` on cluster deployments (`deploy/cluster/frontend-deployment.yaml`, `gateway-deployment.yaml`, `postgres-deployment.yaml`)

### Medium Priority
- Tenant API `revoke_api_key` and `list_api_keys` are no-op stubs
- ServiceMonitor namespace mismatch — Prometheus scrapes nothing
- Postgres backup CronJob reads `POSTGRES_PASSWORD` but `pg_dump` needs `PGPASSWORD`
- No 404 catch-all route in frontend — blank page on invalid URLs
- `liveMode` missing from `useCallback` dependency array in ResearchAgent
- Google Fonts CDN dependency breaks air-gapped deployments
- ~60-70% of test assertions are substring checks on file contents, not behavioral tests

### Low Priority
- Duplicate infrastructure definitions between `deploy/cluster/` and `deploy/database/` + `deploy/gateway/`
- PostgreSQL uses Deployment instead of StatefulSet
- Container images use `:latest` tags — pin to semver or digests for production
- OAuth proxy image in `deploy/cluster/frontend-deployment.yaml` is from OpenShift 4.4

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend   │────▶│  Gateway (FastAPI)│────▶│   MAAS/LiteLLM  │
│  React/PF6   │     │  Routing Engine   │     │  (model access)  │
└─────────────┘     │  Auth / Tenant    │     └─────────────────┘
                    │  Governance       │
                    │  Overdrive Engine │     ┌─────────────────┐
                    └────────┬─────────┘     │   PostgreSQL     │
                             │               │  (persistence)   │
                             └──────────────▶└─────────────────┘
```

**Routing:** All inference requests go through MAAS by default. Direct cluster endpoints (Xeon 6 CPU, Gaudi GPU, OpenVINO) are available for approved deployments via `config.local.yaml` or `config.direct.yaml`.

**Auth:** JWT (requires `JWT_SECRET` env var) or API key (`X-API-Key` header). Unauthenticated requests get read-only access.

**Local dev:** `podman-compose up --build -d` starts gateway + frontend + postgres using MAAS. Add `--profile local-inference` for offline CPU inference with TinyLlama.
