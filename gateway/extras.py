"""
Miscellaneous gateway endpoints — tokenizer, replay, recovery,
content validation, gallery, and semantic routing.
"""

import asyncio
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from utils import sanitize_prompt as _sanitize_prompt, check_rate_limit

router = APIRouter()

# ─── Tokenizer ───

_tokenizer_cache: dict = {}

TOKENIZER_MODELS = {
    "granite-2b-cpu": {"cost_per_1k": 0.0004, "multiplier": 1.3},
    "phi3-mini-cpu": {"cost_per_1k": 0.0004, "multiplier": 1.35},
    "deepseek-r1-distill-qwen-14b": {"cost_per_1k": 0.001, "multiplier": 1.25},
}


def _approximate_tokenize(text: str) -> list:
    import re as _re
    raw = _re.findall(r"\w+|[^\w\s]", text)
    return raw if raw else [""]


def _real_tokenize(text: str, model_name: str) -> list[str]:
    if model_name not in _tokenizer_cache:
        try:
            from transformers import AutoTokenizer
            hf_name = {
                "granite-2b-cpu": "ibm-granite/granite-3.0-2b-instruct",
                "phi3-mini-cpu": "microsoft/Phi-3-mini-4k-instruct",
                "deepseek-r1-distill-qwen-14b": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            }.get(model_name, model_name)
            _tokenizer_cache[model_name] = AutoTokenizer.from_pretrained(hf_name)
        except Exception:
            return _approximate_tokenize(text)
    tokenizer = _tokenizer_cache[model_name]
    ids = tokenizer.encode(text)
    return [tokenizer.decode([tid]) for tid in ids]


class TokenizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    mode: str = Field(default="approximate", pattern=r"^(approximate|real)$")


@router.post("/v1/tokenize")
async def tokenize_text(req: TokenizeRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    req.text = _sanitize_prompt(req.text)
    results = {}
    for model_name, meta in TOKENIZER_MODELS.items():
        if req.mode == "real":
            tokens = _real_tokenize(req.text, model_name)
        else:
            base_tokens = _approximate_tokenize(req.text)
            multiplier = meta["multiplier"]
            count = max(1, int(len(base_tokens) * multiplier))
            tokens = base_tokens[:count] if count <= len(base_tokens) else base_tokens + base_tokens[:count - len(base_tokens)]
        token_count = len(tokens)
        cost = round((token_count / 1000) * meta["cost_per_1k"], 6)
        results[model_name] = {
            "token_count": token_count,
            "tokens": tokens,
            "mode": req.mode,
            "cost_estimate": cost,
        }
    return {"models": results}


# ─── Replay Comparison ───

class ReplayCompareRequest(BaseModel):
    profile: str = Field(default="incident_storm")
    seed: int = Field(default=42)


@router.post("/v1/replay/compare")
async def replay_compare(req: ReplayCompareRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    from overdrive.replay import run_comparison
    return run_comparison(profile=req.profile, seed=req.seed)


# ─── Recovery Demo ───

class RecoveryRunRequest(BaseModel):
    seed: int = Field(default=42)


@router.post("/v1/recovery/run")
async def recovery_run(req: RecoveryRunRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    from overdrive.recovery import run_recovery_demo
    return run_recovery_demo(seed=req.seed)


# ─── Content Validation ───

class ContentValidateRequest(BaseModel):
    name: str
    type: str = "model"
    source: str = "partner"


@router.post("/v1/content/validate")
async def validate_content(req: ContentValidateRequest):
    from content_validator import validate_artifact
    return validate_artifact({"name": req.name, "type": req.type, "source": req.source})


# ─── Publishing House Gallery ───

GALLERY_POCS = [
    {"id": "intelligent-routing", "title": "Intelligent Hardware Routing", "category": "inference", "status": "live",
     "description": "Route AI workloads across Intel Xeon 6 and GPU based on task complexity, cost, and hardware capability.",
     "hardware": ["Xeon 6", "GPU"], "tags": ["routing", "inference", "cost-optimization"]},
    {"id": "multi-agent-swarm", "title": "Multi-Agent Incident Swarm", "category": "agents", "status": "live",
     "description": "5-8 specialized agents coordinate across Intel hardware to investigate, analyze, and report on incidents.",
     "hardware": ["Xeon 6", "GPU"], "tags": ["agents", "incident-response", "parallel"]},
    {"id": "training-pipeline", "title": "Fine-Tuning on Intel Hardware", "category": "training", "status": "live",
     "description": "LoRA/QLoRA fine-tuning with hardware benchmarks comparing Xeon 6 vs GPU training performance.",
     "hardware": ["Xeon 6", "GPU"], "tags": ["training", "fine-tuning", "lora"]},
    {"id": "multimodal-inference", "title": "Multimodal Vision-Language", "category": "inference", "status": "live",
     "description": "Image classification, chart interpretation, and document analysis with vision-language models on GPU.",
     "hardware": ["GPU"], "tags": ["multimodal", "vision", "documents"]},
    {"id": "recovery-resilience", "title": "Hardware Failure Recovery", "category": "resilience", "status": "live",
     "description": "Automatic rerouting when GPU goes offline — zero dropped requests, graceful degradation to Xeon 6.",
     "hardware": ["Xeon 6", "GPU"], "tags": ["resilience", "failover", "zero-downtime"]},
    {"id": "sovereign-cloud", "title": "Sovereign Cloud Deployment", "category": "infrastructure", "status": "planned",
     "description": "Air-gapped deployment model with mirrored images and no external egress for regulated environments.",
     "hardware": ["Xeon 6", "GPU"], "tags": ["sovereign", "air-gap", "compliance"]},
    {"id": "tdx-confidential", "title": "Intel TDX Confidential Computing", "category": "security", "status": "planned",
     "description": "Attestation-aware routing with Intel Trust Domain Extensions for partner workload confidentiality.",
     "hardware": ["Xeon 6 + TDX"], "tags": ["tdx", "confidential", "attestation"]},
    {"id": "capacity-virtualization", "title": "Capacity Virtualization", "category": "infrastructure", "status": "in-progress",
     "description": "Per-tenant resource allocation with dynamic capacity planning and auto-scaling recommendations.",
     "hardware": ["Xeon 6", "GPU"], "tags": ["capacity", "quotas", "scaling"]},
]


@router.get("/v1/gallery/pocs")
async def gallery_pocs(category: str = None):
    items = GALLERY_POCS
    if category:
        items = [p for p in items if p["category"] == category]
    return {"items": items, "total": len(items)}


# ─── Semantic Routing Endpoints ───

@router.post("/v1/semantic/classify")
async def semantic_classify(request: Request):
    """Classify a question using all 3 routing strategies."""
    import semantic_router
    body = await request.json()
    text = body.get("text", body.get("message", ""))
    if not text:
        raise HTTPException(status_code=400, detail="text or message required")

    http_client = request.app.state.http_client
    backends = request.app.state.policy.list_backends()
    backend = backends[0] if backends else None

    result = await semantic_router.classify_all(text, http_client, backend)
    return result


@router.post("/v1/semantic/compare")
async def semantic_compare(request: Request):
    """Classify + route + generate on all 3 strategies simultaneously."""
    import semantic_router

    body = await request.json()
    text = body.get("text", body.get("message", ""))
    if not text:
        raise HTTPException(status_code=400, detail="text or message required")

    http_client = request.app.state.http_client
    backends = request.app.state.policy.list_backends()
    backend = backends[0] if backends else None

    classification = await semantic_router.classify_all(text, http_client, backend)

    async def generate_for_strategy(strategy: dict) -> dict:
        model = strategy["model"]
        start = time.time()
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 256,
                "temperature": 0.7,
            }
            headers = {}
            if backend and backend.api_key:
                headers["Authorization"] = f"Bearer {backend.api_key}"
            resp = await http_client.post(
                f"{backend.url}/v1/chat/completions", json=payload, headers=headers, timeout=30.0
            )
            resp.raise_for_status()
            result = resp.json()
            choices = result.get("choices", [])
            msg = choices[0].get("message", {}) if choices else {}
            response_text = msg.get("content") or msg.get("reasoning_content") or ""
        except Exception as e:
            response_text = f"Error: {str(e)[:100]}"

        inference_ms = (time.time() - start) * 1000
        return {
            **strategy,
            "response": response_text[:500],
            "inference_ms": round(inference_ms),
            "total_ms": round(strategy["routing_ms"] + inference_ms),
        }

    tasks = [generate_for_strategy(s) for s in classification["strategies"]]
    results = await asyncio.gather(*tasks)

    return {
        "query": text[:200],
        "strategies": results,
        "agreement": classification["agreement"],
        "all_agree": classification["all_agree"],
    }
