"""Semantic routing — classify questions by department and route to optimal model.

Three classification strategies:
1. Rule-Based: keyword matching (fastest, 0ms overhead)
2. Embedding: cosine similarity to department templates (fast, ~50ms)
3. LLM Classifier: ask a small model to classify (most accurate, ~500ms)
"""

from __future__ import annotations

import os
import time
import math
import yaml
from pathlib import Path
from typing import Optional


def _load_departments() -> dict:
    config_path = Path(__file__).parent / "departments.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {"departments": {}, "opus_baseline": {}}


_CONFIG = _load_departments()
DEPARTMENTS = _CONFIG.get("departments", {})
OPUS_BASELINE = _CONFIG.get("opus_baseline", {})


def classify_rules(text: str) -> dict:
    """Strategy 1: Rule-based keyword matching. Instant, no API calls."""
    start = time.time()
    text_lower = text.lower()
    scores = {}

    for dept_id, dept in DEPARTMENTS.items():
        keywords = dept.get("keywords", [])
        if not keywords:
            continue
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            scores[dept_id] = matches / len(keywords)

    elapsed_ms = (time.time() - start) * 1000

    if scores:
        best = max(scores, key=scores.get)
        confidence = min(scores[best] * 5, 1.0)
    else:
        best = "general"
        confidence = 0.3

    dept = DEPARTMENTS.get(best, DEPARTMENTS.get("general", {}))
    return {
        "strategy": "rules",
        "department": best,
        "department_label": dept.get("label", best),
        "model": dept.get("model", "granite-3-2-8b-instruct"),
        "confidence": round(confidence, 2),
        "reasoning": dept.get("reasoning", ""),
        "routing_ms": round(elapsed_ms, 1),
    }


async def classify_embedding(text: str, http_client, backend) -> dict:
    """Strategy 2: Embedding similarity. Embed query + cosine match to dept templates."""
    start = time.time()

    try:
        embed_payload = {
            "model": "nomic-embed-text-v1-5",
            "input": [text] + [dept.get("description", dept.get("label", ""))
                               for dept in DEPARTMENTS.values()],
        }
        headers = {}
        if backend and backend.api_key:
            headers["Authorization"] = f"Bearer {backend.api_key}"

        resp = await http_client.post(
            f"{backend.url}/v1/embeddings", json=embed_payload, headers=headers, timeout=30.0
        )
        resp.raise_for_status()
        result = resp.json()

        embeddings = [d["embedding"] for d in result.get("data", [])]
        if len(embeddings) < 2:
            raise ValueError("Not enough embeddings returned")

        query_emb = embeddings[0]
        dept_ids = list(DEPARTMENTS.keys())
        best_score = -1
        best_dept = "general"

        for i, dept_id in enumerate(dept_ids):
            if i + 1 < len(embeddings):
                score = _cosine_similarity(query_emb, embeddings[i + 1])
                if score > best_score:
                    best_score = score
                    best_dept = dept_id

    except Exception as e:
        best_dept = "general"
        best_score = 0.0

    elapsed_ms = (time.time() - start) * 1000
    dept = DEPARTMENTS.get(best_dept, DEPARTMENTS.get("general", {}))

    return {
        "strategy": "embedding",
        "department": best_dept,
        "department_label": dept.get("label", best_dept),
        "model": dept.get("model", "granite-3-2-8b-instruct"),
        "confidence": round(max(best_score, 0), 2),
        "reasoning": dept.get("reasoning", ""),
        "routing_ms": round(elapsed_ms, 1),
    }


async def classify_llm(text: str, http_client, backend) -> dict:
    """Strategy 3: LLM classifier. Ask a small model to classify the department."""
    start = time.time()

    dept_list = ", ".join(f"{k} ({v.get('label', k)})" for k, v in DEPARTMENTS.items())

    try:
        payload = {
            "model": "granite-2b-cpu",
            "messages": [{
                "role": "user",
                "content": (
                    f"Classify this question into exactly one department: {dept_list}. "
                    f"Respond with ONLY the department key (e.g., 'hr', 'engineering', 'legal'). "
                    f"Question: {text[:500]}"
                ),
            }],
            "max_tokens": 10,
            "temperature": 0.1,
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
        answer = choices[0].get("message", {}).get("content", "").strip().lower() if choices else ""

        # Match to known department
        best_dept = "general"
        for dept_id in DEPARTMENTS:
            if dept_id in answer:
                best_dept = dept_id
                break

        confidence = 0.85 if best_dept != "general" else 0.4

    except Exception as e:
        best_dept = "general"
        confidence = 0.0

    elapsed_ms = (time.time() - start) * 1000
    dept = DEPARTMENTS.get(best_dept, DEPARTMENTS.get("general", {}))

    return {
        "strategy": "llm",
        "department": best_dept,
        "department_label": dept.get("label", best_dept),
        "model": dept.get("model", "granite-3-2-8b-instruct"),
        "confidence": round(confidence, 2),
        "reasoning": dept.get("reasoning", ""),
        "routing_ms": round(elapsed_ms, 1),
    }


VLLM_SR_URL = os.environ.get("VLLM_SR_URL", "http://semantic-router:8899")

# Map vLLM SR model IDs back to department IDs
_MODEL_TO_DEPT = {}
for _dept_id, _dept in DEPARTMENTS.items():
    _model = _dept.get("model", "")
    if _model and _dept_id != "general":
        _MODEL_TO_DEPT[_model] = _dept_id
_MODEL_TO_DEPT["granite-3-2-8b-instruct"] = "general"


async def classify_vllm_sr(text: str, http_client) -> dict:
    """Strategy 4: vLLM Semantic Router — production-grade signal-driven routing with OpenVINO."""
    start = time.time()

    try:
        payload = {
            "model": "auto",
            "messages": [{"role": "user", "content": text[:500]}],
            "max_tokens": 1,
        }
        resp = await http_client.post(
            f"{VLLM_SR_URL}/v1/chat/completions",
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        result = resp.json()

        routed_model = result.get("model", "")
        route_name = ""
        for header_name in ["x-vsr-route", "x-semantic-route", "x-routed-model"]:
            route_name = resp.headers.get(header_name, "")
            if route_name:
                break

        best_dept = _MODEL_TO_DEPT.get(routed_model, "general")
        if not best_dept or best_dept == "general":
            for dept_id, dept in DEPARTMENTS.items():
                if dept.get("model") == routed_model:
                    best_dept = dept_id
                    break

        confidence = 0.90

    except Exception:
        best_dept = "general"
        routed_model = "granite-3-2-8b-instruct"
        confidence = 0.0

    elapsed_ms = (time.time() - start) * 1000
    dept = DEPARTMENTS.get(best_dept, DEPARTMENTS.get("general", {}))

    return {
        "strategy": "vllm-sr",
        "department": best_dept,
        "department_label": dept.get("label", best_dept),
        "model": routed_model or dept.get("model", "granite-3-2-8b-instruct"),
        "confidence": round(confidence, 2),
        "reasoning": "vLLM Semantic Router — signal-driven routing with OpenVINO on Intel Xeon 6",
        "routing_ms": round(elapsed_ms, 1),
    }


async def classify_all(text: str, http_client, backend) -> dict:
    """Run all 4 strategies in parallel and return comparison."""
    import asyncio

    rules_result = classify_rules(text)

    embedding_task = classify_embedding(text, http_client, backend)
    llm_task = classify_llm(text, http_client, backend)
    vllm_sr_task = classify_vllm_sr(text, http_client)

    embedding_result, llm_result, vllm_sr_result = await asyncio.gather(
        embedding_task, llm_task, vllm_sr_task
    )

    strategies = [rules_result, embedding_result, llm_result, vllm_sr_result]

    opus_input = OPUS_BASELINE.get("cost_per_m_input", 15.0)
    opus_output = OPUS_BASELINE.get("cost_per_m_output", 75.0)
    opus_cost = (2000 / 1_000_000 * opus_input) + (1000 / 1_000_000 * opus_output)

    for s in strategies:
        dept = DEPARTMENTS.get(s["department"], {})
        model_input = dept.get("cost_per_m_input", 0)
        model_cost = (2000 / 1_000_000 * model_input) + (1000 / 1_000_000 * model_input * 4)
        s["estimated_cost"] = round(model_cost, 6)
        s["opus_cost"] = round(opus_cost, 4)
        s["savings_vs_opus"] = round(opus_cost - model_cost, 4) if opus_cost > model_cost else 0

    agreement = len(set(s["department"] for s in strategies))

    return {
        "query": text[:200],
        "strategies": strategies,
        "agreement": 4 - agreement + 1,
        "all_agree": agreement == 1,
    }


def calculate_annual_savings(dept_id: str, queries_per_day: int = 1000) -> dict:
    """Calculate annual cost savings for a department vs Opus baseline."""
    dept = DEPARTMENTS.get(dept_id, {})
    model_input = dept.get("cost_per_m_input", 0)

    chosen_daily = queries_per_day * (2000 / 1_000_000 * model_input + 1000 / 1_000_000 * model_input * 4)
    opus_daily = queries_per_day * (2000 / 1_000_000 * 15.0 + 1000 / 1_000_000 * 75.0)

    return {
        "department": dept_id,
        "model": dept.get("model", "?"),
        "daily_cost": round(chosen_daily, 2),
        "opus_daily_cost": round(opus_daily, 2),
        "annual_cost": round(chosen_daily * 250, 0),
        "opus_annual_cost": round(opus_daily * 250, 0),
        "annual_savings": round((opus_daily - chosen_daily) * 250, 0),
    }


def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
