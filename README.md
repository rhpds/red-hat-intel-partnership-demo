# Intel-Red Hat AI Inference Platform

Multi-tenant AI inference gateway that routes workloads across Intel Xeon 6 (CPU) and Intel GPU hardware on Red Hat OpenShift. Features interactive RAG chat with document upload, semantic department routing, model switching, and real-time routing trace.

## Architecture

```
Frontend (React/PatternFly 6) → Gateway (FastAPI) → MAAS/LiteLLM → Intel Hardware
                                     ↓                                  ↓
                                PostgreSQL (pgvector)           Intel GPU / Xeon 6 CPU
                                     ↓
                          vLLM Semantic Router (optional)
```

**Gateway** routes requests across 17 models served on Intel hardware via MAAS:
- **Intel GPU**: qwen3-14b, deepseek-r1-distill-qwen-14b, microsoft-phi-4, llama-31-70b
- **Intel Xeon 6 CPU** (OpenVINO): granite-2b-cpu, phi3-mini-cpu, qwen25-3b-cpu

## Features

- **Semantic Department Routing** — 4 classification strategies (rules, embedding, LLM, vLLM Semantic Router) route queries to optimal models per department
- **Interactive RAG Chat** — Document upload (PDF, DOCX, TXT), embedding search, SSE streaming
- **Model Comparison** — Side-by-side comparison of routing strategies with cost/latency metrics
- **Multi-Tenant** — Per-tenant namespaces, Keycloak SSO, scoped LiteLLM virtual keys
- **Cost Optimization** — Right-size hardware to workload, annual savings vs frontier models

## Quick Start

```bash
cp .env.example .env   # Add LITELLM_API_KEY
podman-compose up --build -d
```

Frontend: http://localhost:3000
Gateway API: http://localhost:8080/health

## Development

```bash
# Backend tests
python3 -m pytest tests/ -v

# Frontend dev
cd frontend && npm run dev

# TypeScript check
cd frontend && npx tsc --noEmit

# Helm template test
cd helm && make template NAMESPACE=test EXTRA_HELM_ARGS="--set litellm.apiKey=test --set litellm.apiBase=https://maas-rhdp.apps.maas.redhatworkshops.io --set postgres.password=test"
```

## Deployment (RHDP)

Deploys via the `quickstart_deploy_via_make` pattern on Red Hat Demo Platform:

```bash
# Helm install (what RHDP runs)
cd helm
make install NAMESPACE=user-demo-intel-inference \
  EXTRA_HELM_ARGS="--set litellm.apiKey=\$KEY --set litellm.apiBase=https://maas-rhdp.apps.maas.redhatworkshops.io --set postgres.password=\$PW"
```

Container images are built via GitHub Actions CI on push to main.

## Project Structure

```
gateway/                    # FastAPI backend
  router.py                 #   Main app (all endpoints)
  chat.py                   #   Chat sessions, SSE streaming
  rag.py                    #   Document upload, chunking, embedding, search
  semantic_router.py        #   4-strategy department classifier
  departments.yaml          #   6-department taxonomy → model mappings
  vllm-sr-config.yaml       #   vLLM Semantic Router config
  content_validator.py      #   RAG content screening + output safety
  auth.py                   #   JWT + API key auth
  routing_policy.py         #   YAML-based routing rules
  config.yaml               #   Backend configuration (MAAS endpoints)
  overdrive/                #   Advanced routing engine

frontend/src/               # React 19 + PatternFly 6
  pages/Chat.tsx            #   Interactive RAG chat
  components/               #   ChatMessage, RoutingTrace, DocumentUploader, ModelSelector
  api/client.ts             #   API endpoints

helm/                       # Helm chart (RHDP quickstart_deploy_via_make)
tests/                      # 1,437 pytest tests
content/                    # Antora docs site (Showroom lab guide)
.github/workflows/          # CI: tests, image builds
```

## License

Apache-2.0
