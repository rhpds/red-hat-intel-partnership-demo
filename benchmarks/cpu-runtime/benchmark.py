#!/usr/bin/env python3
"""Streaming OpenAI-compatible benchmark for OVMS and vLLM runtimes."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable


PROFILES = {
    "short": {
        "prompt": "Name three practical benefits of Intel AMX for enterprise AI inference.",
        "max_tokens": 64,
    },
    "medium": {
        "prompt": (
            "Explain how a heterogeneous inference gateway should route embedding, "
            "reranking, generation, and governance stages between Intel Xeon CPUs and "
            "GPUs. Include operational tradeoffs and failure handling."
        ),
        "max_tokens": 256,
    },
    "long": {
        "prompt": (
            "You are reviewing an enterprise RAG architecture on Red Hat OpenShift. "
            "The pipeline embeds a query, searches pgvector, reranks candidates, "
            "generates an answer, and applies governance. Discuss hardware placement, "
            "model-serving runtime selection, batching, concurrency, observability, "
            "tenant isolation, recovery behavior, and how to benchmark the design "
            "without overstating cost or availability guarantees. Provide a structured "
            "technical recommendation with assumptions and risks."
        ),
        "max_tokens": 512,
    },
}


@dataclass
class RequestResult:
    ok: bool
    ttft_s: float = 0.0
    e2e_s: float = 0.0
    output_tokens: int = 0
    content_chunks: int = 0
    error: str = ""

    @property
    def output_tokens_per_second(self) -> float:
        generation_time = max(self.e2e_s - self.ttft_s, 1e-9)
        return self.output_tokens / generation_time

    @property
    def inter_token_latency_ms(self) -> float:
        if self.output_tokens <= 1:
            return 0.0
        return ((self.e2e_s - self.ttft_s) / (self.output_tokens - 1)) * 1000


def percentile(values: Iterable[float], pct: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * pct / 100.0
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def summarize(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
    return {
        "mean": round(statistics.mean(values), 6),
        "p50": round(percentile(values, 50), 6),
        "p95": round(percentile(values, 95), 6),
        "p99": round(percentile(values, 99), 6),
    }


def endpoint(base_url: str, api_prefix: str) -> str:
    return f"{base_url.rstrip('/')}/{api_prefix.strip('/')}/chat/completions"


def run_request(url: str, model: str, prompt: str, max_tokens: int, timeout: int) -> RequestResult:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer benchmark"},
        method="POST",
    )
    start = time.perf_counter()
    first_content = None
    chunks = 0
    usage_tokens = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                event = json.loads(data)
                usage = event.get("usage") or {}
                usage_tokens = max(usage_tokens, int(usage.get("completion_tokens", 0) or 0))
                choices = event.get("choices") or []
                if choices:
                    content = (choices[0].get("delta") or {}).get("content") or ""
                    if content:
                        chunks += 1
                        if first_content is None:
                            first_content = time.perf_counter()
        end = time.perf_counter()
        if first_content is None:
            return RequestResult(False, e2e_s=end - start, error="stream contained no content")
        output_tokens = usage_tokens or chunks
        return RequestResult(True, first_content - start, end - start, output_tokens, chunks)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return RequestResult(False, e2e_s=time.perf_counter() - start, error=str(exc)[:300])


def run_cell(
    url: str,
    model: str,
    profile_name: str,
    concurrency: int,
    requests: int,
    warmup: int,
    timeout: int,
) -> dict:
    profile = PROFILES[profile_name]
    for _ in range(warmup):
        warm = run_request(url, model, profile["prompt"], profile["max_tokens"], timeout)
        if not warm.ok:
            raise RuntimeError(f"warm-up failed: {warm.error}")

    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(run_request, url, model, profile["prompt"], profile["max_tokens"], timeout)
            for _ in range(requests)
        ]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    wall_s = time.perf_counter() - wall_start

    successes = [result for result in results if result.ok]
    failures = [result for result in results if not result.ok]
    total_output_tokens = sum(result.output_tokens for result in successes)
    return {
        "profile": profile_name,
        "max_tokens": profile["max_tokens"],
        "concurrency": concurrency,
        "requests": requests,
        "successful": len(successes),
        "failed": len(failures),
        "success_rate_pct": round(100 * len(successes) / requests, 3),
        "wall_seconds": round(wall_s, 6),
        "requests_per_second": round(len(successes) / wall_s, 6),
        "aggregate_output_tokens_per_second": round(total_output_tokens / wall_s, 6),
        "ttft_seconds": summarize([result.ttft_s for result in successes]),
        "e2e_seconds": summarize([result.e2e_s for result in successes]),
        "inter_token_latency_ms": summarize([result.inter_token_latency_ms for result in successes]),
        "per_request_output_tokens_per_second": summarize(
            [result.output_tokens_per_second for result in successes]
        ),
        "errors": sorted({result.error for result in failures})[:10],
        "individual_results": [asdict(result) for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-prefix", choices=["v1", "v3"], required=True)
    parser.add_argument("--model", default="phi35-mini-int4")
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--profiles", default="short,medium,long")
    parser.add_argument("--concurrency", default="1,2,4,8")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    url = endpoint(args.base_url, args.api_prefix)
    output = {
        "schema_version": 1,
        "runtime": args.runtime,
        "model": args.model,
        "endpoint": url,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "cells": [],
    }
    try:
        for profile in args.profiles.split(","):
            if profile not in PROFILES:
                raise ValueError(f"unknown profile: {profile}")
            for concurrency in [int(value) for value in args.concurrency.split(",")]:
                output["cells"].append(
                    run_cell(
                        url,
                        args.model,
                        profile,
                        concurrency,
                        args.requests,
                        args.warmup,
                        args.timeout,
                    )
                )
    except Exception as exc:
        output["fatal_error"] = str(exc)
        print(json.dumps(output, indent=2))
        return 1

    output["completed_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
