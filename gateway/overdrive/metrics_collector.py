"""Aggregate metrics from a batch of workload results."""

from collections import Counter


def collect_metrics(results: list[dict], total_duration_ms: float) -> dict:
    n = len(results)
    if n == 0:
        return {"total_requests": 0, "completed_requests": 0}

    latencies = sorted(r["latency_ms"] for r in results)
    route_counts = dict(Counter(r["lane"] for r in results))
    total_input = sum(r["input_tokens"] for r in results)
    total_output = sum(r["output_tokens"] for r in results)

    duration_sec = total_duration_ms / 1000 if total_duration_ms > 0 else 1

    eco_count = route_counts.get("eco", 0)
    perf_count = route_counts.get("performance", 0)
    gaudi_count = route_counts.get("overdrive", 0)

    return {
        "total_requests": n,
        "completed_requests": n,
        "failed_requests": 0,
        "route_counts": route_counts,
        "total_input_tokens_estimate": total_input,
        "total_output_tokens_estimate": total_output,
        "requests_per_second": round(n / duration_sec, 2),
        "estimated_tokens_per_second": round((total_input + total_output) / duration_sec, 2),
        "p50_latency_ms": _percentile(latencies, 50),
        "p95_latency_ms": _percentile(latencies, 95),
        "p99_latency_ms": _percentile(latencies, 99),
        "min_latency_ms": latencies[0],
        "max_latency_ms": latencies[-1],
        "total_duration_ms": total_duration_ms,
        "xeon_eco_utilization_pct": round(eco_count / n * 100, 1) if n else 0,
        "xeon_performance_utilization_pct": round(perf_count / n * 100, 1) if n else 0,
        "gaudi_overdrive_utilization_pct": round(gaudi_count / n * 100, 1) if n else 0,
    }


def _percentile(sorted_values: list, pct: int) -> float:
    if not sorted_values:
        return 0
    k = (len(sorted_values) - 1) * (pct / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return sorted_values[-1]
    d = k - f
    return round(sorted_values[f] + (sorted_values[c] - sorted_values[f]) * d, 2)
