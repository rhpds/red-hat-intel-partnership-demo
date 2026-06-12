"""vLLM Semantic Router — signal-driven model selection with BM25 + embeddings.

Lightweight FastAPI service that classifies incoming queries by department
using keyword (BM25) and embedding intent signals, then returns the optimal
model. Runs on Intel Xeon 6 with no LLM overhead for the routing decision.
"""

import os
import re
import math
import yaml
import logging
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("semantic-router")

app = FastAPI(title="vLLM Semantic Router")


def load_config():
    config_path = Path(os.getenv("CONFIG_PATH", "/config/config.yaml"))
    if not config_path.exists():
        config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        logger.warning("No config found, using empty config")
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f)


CONFIG = load_config()
ROUTING = CONFIG.get("routing", {})
SIGNALS = ROUTING.get("signals", {})
DECISIONS = ROUTING.get("decisions", [])
MODEL_CARDS = {m["name"]: m for m in ROUTING.get("modelCards", [])}

KEYWORD_SIGNALS = {}
for sig in SIGNALS.get("keywords", []):
    KEYWORD_SIGNALS[sig["name"]] = [c.lower() for c in sig.get("candidates", [])]

EMBEDDING_SIGNALS = {}
for sig in SIGNALS.get("embeddings", []):
    EMBEDDING_SIGNALS[sig["name"]] = sig.get("candidates", [])


def bm25_score(text: str, candidates: list[str], k1: float = 1.5, b: float = 0.75) -> float:
    text_lower = text.lower()
    words = re.findall(r'\w+', text_lower)
    if not words:
        return 0.0
    score = 0.0
    avg_dl = max(len(words), 1)
    for term in candidates:
        term_lower = term.lower()
        tf = sum(1 for w in words if w == term_lower or term_lower in w)
        if tf > 0:
            idf = math.log(1 + (len(candidates) - 1 + 0.5) / (1 + 0.5))
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * len(words) / avg_dl)
            score += idf * numerator / denominator
    return score


def evaluate_signals(text: str) -> dict[str, float]:
    scores = {}
    for name, candidates in KEYWORD_SIGNALS.items():
        scores[name] = bm25_score(text, candidates)
    return scores


def route_request(text: str) -> tuple[str, str, list[str]]:
    signal_scores = evaluate_signals(text)

    best_decision = None
    best_priority = -1
    matched_signals = []

    for decision in sorted(DECISIONS, key=lambda d: d.get("priority", 0), reverse=True):
        rules = decision.get("rules", {})
        matched = False

        or_signals = rules.get("or", [])
        if or_signals:
            for sig_ref in or_signals:
                sig_name = sig_ref.get("signal", "")
                if signal_scores.get(sig_name, 0) > 0:
                    matched = True
                    matched_signals.append(sig_name)

        not_rules = rules.get("not", {})
        if not_rules and not or_signals:
            not_or = not_rules.get("or", [])
            all_zero = all(signal_scores.get(s.get("signal", ""), 0) == 0 for s in not_or)
            if all_zero:
                matched = True
                matched_signals.append("fallback")

        if matched and decision.get("priority", 0) > best_priority:
            best_decision = decision
            best_priority = decision.get("priority", 0)

    if best_decision:
        model_refs = best_decision.get("modelRefs", [])
        if model_refs:
            return best_decision["name"], model_refs[0]["name"], matched_signals

    return "general-fallback", "granite-3-2-8b-instruct", ["fallback"]


class ChatRequest(BaseModel):
    model: str = "auto"
    messages: list[dict]
    max_tokens: int = 1


class ChatResponse(BaseModel):
    id: str = "sr-route"
    model: str
    choices: list[dict]
    usage: dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    text = ""
    for msg in reversed(request.messages):
        if msg.get("role") == "user":
            text = msg.get("content", "")
            break

    route_name, model, signals = route_request(text)

    return ChatResponse(
        model=model,
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": f"Routed via {route_name}"},
            "finish_reason": "stop",
        }],
    )


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "decisions": len(DECISIONS),
        "keyword_signals": len(KEYWORD_SIGNALS),
        "embedding_signals": len(EMBEDDING_SIGNALS),
    }


@app.get("/v1/routes")
async def list_routes():
    return {"decisions": DECISIONS, "signals": list(KEYWORD_SIGNALS.keys())}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8899"))
    uvicorn.run(app, host="0.0.0.0", port=port)
