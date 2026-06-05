# CLAUDE.md — Agent Instructions for Intel-Red Hat AI Inference Platform

## What This Is

Multi-tenant AI inference gateway that routes workloads across Intel Xeon 6 (CPU) and Gaudi (GPU) hardware on Red Hat OpenShift. Includes an interactive RAG chat with document upload, real-time routing trace, and model switching.

## Architecture

```
Frontend (React/PatternFly 6) → Gateway (FastAPI) → MAAS/LiteLLM → Intel Hardware
                                    ↓
                               PostgreSQL (pgvector)
```

- **Gateway** (`gateway/`): FastAPI app, `router.py` is the main entry point. Runs as standalone script, NOT a package — use `import module` not `from . import module`.
- **Frontend** (`frontend/`): React 19 + PatternFly 6 + Vite. Dev proxy to gateway at localhost:8080.
- **Database**: PostgreSQL with pgvector extension for RAG embeddings.
- **MAAS**: LiteLLM proxy at `litellm-prod.apps.maas.redhatworkshops.io`. API key in `.env`.

## Development

```bash
# Local dev
cp .env.example .env  # Add LITELLM_API_KEY
podman-compose up --build -d

# Tests
python3 -m pytest tests/ -v

# Frontend dev
cd frontend && npm run dev
```

## Testing

- Backend: `python3 -m pytest tests/ -v` (133+ tests)
- Frontend: `cd frontend && npx vitest`
- TypeScript: `cd frontend && npx tsc --noEmit`

## Deployment (infra01)

The demo deploys to OpenShift via internal registry. **Local Mac is arm64, cluster is amd64** — always build with `--platform linux/amd64`.

```bash
REGISTRY="default-route-openshift-image-registry.apps.ocpv-infra01.dal12.infra.demo.redhat.com"
NS="intel-rh-demo"
podman build --platform linux/amd64 -t $REGISTRY/$NS/inference-gateway:latest -f gateway/Containerfile gateway/
podman push --tls-verify=false $REGISTRY/$NS/inference-gateway:latest
oc rollout restart deploy/gateway -n $NS
```

## Key Conventions

- **Gateway imports**: Use `import chat`, `import rag`, NOT `from . import chat` (standalone script, not package)
- **Containerfile**: If you add a new `.py` file to `gateway/`, add `COPY newfile.py .` to `gateway/Containerfile`
- **Pre-commit hook**: Blocks API keys, tokens, secrets. False positive? `git commit --no-verify`
- **PatternFly 6**: Use `size="sm"` not `isSmall`, `Label` color must be a valid PF6 color (no "gold")
- **Tests**: TDD with validation matrix. 90% pass threshold per stage. Write tests first (RED), then implement (GREEN).

## File Structure

```
gateway/
  router.py          # Main FastAPI app (all endpoints)
  chat.py            # Chat sessions, SSE streaming, context building
  rag.py             # Document upload, chunking, embedding, search, security
  db.py              # PostgreSQL async adapter
  auth.py            # JWT + API key auth
  routing_policy.py  # YAML-based routing rules
  overdrive/         # Advanced routing engine
  migrations/        # SQL migrations (001-004)

frontend/src/
  pages/Chat.tsx     # Interactive RAG chat page
  components/        # ChatMessage, RoutingTrace, DocumentUploader, ModelSelector
  api/client.ts      # API endpoints
  api/types.ts       # TypeScript interfaces

helm/                # Helm chart for RHDP quickstart_deploy_via_make pattern
tests/               # 133+ pytest tests with validation matrix
content/             # Antora docs site (ref arch, lab guide)
```

## Related Repos

- **NovaScan** (`~/Documents/checksum`, [rhpds/NovaScan](https://github.com/rhpds/NovaScan)): Capacity scanner — scans repos, recommends provisioning tiers
- **LiftOff** (`~/Documents/liftoff`): Provisioning engine — AgnosticV configs, Ansible roles for RHDP

## What NOT To Do

- Don't use relative imports in gateway (`from .` will fail — it runs as `python3 router.py`)
- Don't commit `.env` (has real API keys — it's in `.gitignore`)
- Don't build container images without `--platform linux/amd64` (cluster is x86)
- Don't add gateway files without updating `gateway/Containerfile`
- Don't use PatternFly props that don't exist in v6 (check the version)
