"""Deterministic workload batch generation from profile + mode + seed."""

import random
from .models import InferenceRequest
from .power_modes import get_mode_config
from .workload_profiles import PROFILES

LATENCY_DEFAULTS = {
    "classification": 8000,
    "embedding": 5000,
    "rerank": 5000,
    "short_summary": 8000,
    "long_summary": 5000,
    "incident_rca": 5000,
    "batch_summary": 10000,
    "rag_question": 5000,
    "document_summary": 5000,
    "code_summary": 5000,
}


def generate_workload(
    profile: str,
    mode: str,
    seed: int,
    count: int = None,
    concurrency: int = None,
) -> list[InferenceRequest]:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")

    profile_data = PROFILES[profile]
    cfg = get_mode_config(mode, count=count, concurrency=concurrency)
    total = cfg["count"]
    mix = profile_data["task_mix"]
    total_weight = sum(e["weight"] for e in mix)

    rng = random.Random(seed)
    requests = []

    for i in range(total):
        roll = rng.random() * total_weight
        cumulative = 0
        entry = mix[0]
        for e in mix:
            cumulative += e["weight"]
            if roll < cumulative:
                entry = e
                break

        low, high = entry["token_range"]
        token_estimate = rng.randint(low, high)

        prompts_for_task = profile_data.get("prompts", {}).get(entry["task_type"], [])
        prompt = prompts_for_task[rng.randint(0, len(prompts_for_task) - 1)] if prompts_for_task else ""

        requests.append(InferenceRequest(
            request_id=f"wl-{seed}-{i:05d}",
            task_type=entry["task_type"],
            priority=entry["priority"],
            token_estimate=token_estimate,
            latency_target_ms=LATENCY_DEFAULTS.get(entry["task_type"], 5000),
            prompt=prompt,
        ))

    return requests
