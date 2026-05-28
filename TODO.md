# Intel-Red Hat AI Inference Platform — Status & Next Steps

**Repo:** https://github.com/rhpds/red-hat-intel-partnership-demo  
**Updated:** 2026-05-25  
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
- [x] Default gateway routing goes through MAAS proxy (`litellm-prod.apps.maas.redhatworkshops.io`)
- [x] CPU inference moved to optional `local-inference` profile in podman-compose
- [x] All dev ports bound to `127.0.0.1`
- [x] Added coordination notices to GPU deploy READMEs (Ashok approval required)
- [x] Added `docs/cnv-experiments.md` with MAAS usage and CNV policy

### Repo Setup
- [x] Pushed to `rhpds/red-hat-intel-partnership-demo` with clean single-commit history
- [x] Updated Tekton pipeline and GitOps application URLs to point to rhpds repo
- [x] 0 open Dependabot alerts

---

## Next Steps — Need Team Input

### For Ashok

1. **AgnosticV catalog placement** — Where in the agnosticv repo does our catalog entry go? Which account path? (`agnosticv-catalog/` in this repo is a reference skeleton ready to copy over)

2. **Existing Intel demo CIs** — Are there existing Intel demo catalog items we should model after or integrate with?

3. **GPU access for testing** — When we're ready to test the Gaudi inference path live, which CNV cluster should we use? What's the approval process?

4. **Image registry** — Which quay.io org should we push container images to? (`quay.io/intel-redhat/` is a placeholder in the manifests)

### For Tony

5. **CI/CD pipeline** — What branch/tag triggers the integration environment? Is there a Jenkins/Tekton pipeline we should hook into, or do we use the one in `deploy/pipelines/pipeline.yaml`?

6. **Image build automation** — Should container builds happen in the agnosticd config (during deploy) or pre-built and pushed to a registry?

7. **Secrets management** — What's the standard approach for demo secrets in the Babylon pipeline? Vault? ExternalSecrets? Manual injection?

### For Jonathan (Self)

8. **Learn agnosticd workflow** — Walk through creating a config PR against `github.com/redhat-cop/agnosticd` using an existing config as a template. Ashok/Tony can pair on this.

9. **Test devel deployment** — Once items 1-4 are resolved, do a devel deployment to validate the agnosticd config end-to-end.

10. **Smoke deploy (Stage 5)** — Pending cluster access: deploy the full stack to an OpenShift cluster and validate all components work together.

---

## Known Issues (from code review — not blocking)

These were identified during a full repo review. Fix as time allows.

### High Priority
- In-memory rate limiter grows unboundedly — switch to `slowapi` (already in requirements) or add key eviction
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
