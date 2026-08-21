"""Batch runner: ties generator -> engine -> timing -> metrics -> report."""

import hashlib
import os
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .workload_generator import generate_workload
from .engine import OverdriveEngine
from .timing_provider import MockTimingProvider, RealTimingProvider
from .metrics_collector import collect_metrics
from .power_report import generate_json_report, generate_markdown_report
from .power_modes import get_mode_config
from .event_producer import get_event_producer

_DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"
_DEFAULT_RUBRICS = Path(__file__).parents[2] / "tests" / "rubrics" / "routes"

GOVERNED_MODES = {"boost", "overdrive", "max_q"}

ROUTING_EXPLANATIONS = {
    "eco": {
        "classification": "Small classification task — Granite Tiny on Xeon 6 handles this in milliseconds at minimal cost.",
        "short_summary": "Short summary within 4K token limit — runs efficiently on Xeon 6 without GPU overhead.",
    },
    "performance": {
        "embedding": "Vector encoding — nomic-embed on Xeon 6 with AMX acceleration for fast parallel indexing.",
        "rerank": "Cross-encoder reranking — CodeLlama 7B on Xeon 6 scores document relevance efficiently.",
        "short_summary": "Mid-range summary — CodeLlama 7B on Xeon 6 with AMX handles this at production throughput.",
        "long_summary": "Fallback from GPU — performance lane handles this generation workload on Xeon 6.",
        "rag_question": "RAG retrieval-side — small context questions answered on Xeon 6 without GPU cost.",
    },
    "overdrive": {
        "long_summary": "Large context generation — Llama Scout 17B needs GPU HBM bandwidth for 16K+ tokens.",
        "incident_rca": "Complex root cause analysis — multi-step reasoning requires GPU throughput and memory.",
        "batch_summary": "Batch report generation — 32K+ tokens aggregated on GPU at 100+ tokens/sec.",
        "document_summary": "Long document distillation — GPU 400K context window handles full whitepapers.",
        "code_summary": "Codebase analysis — sustained generation on GPU for comprehensive review output.",
        "rag_question": "Complex multi-document RAG — large context synthesis routed to GPU for deeper reasoning.",
    },
}


def _build_routing_reason(lane: str, task_type: str, token_estimate: int, reason_codes: list) -> str:
    specific = ROUTING_EXPLANATIONS.get(lane, {}).get(task_type)
    if specific:
        return specific
    if lane == "eco":
        return f"Small task ({token_estimate:,} tokens) routed to Xeon 6 Eco — fast and cost-efficient."
    if lane == "performance":
        return f"Mid-range task ({token_estimate:,} tokens) routed to Xeon 6 Performance with AMX acceleration."
    if lane == "overdrive":
        return f"Heavy generation ({token_estimate:,} tokens) routed to GPU — needs HBM bandwidth."
    return f"Unrouted — no lane matched for {task_type} at {token_estimate:,} tokens."


def _verify_unlock(unlock_code: str) -> bool:
    expected_hash = os.getenv("WORKLOAD_UNLOCK_HASH", "")
    if not expected_hash:
        return False
    provided_hash = hashlib.sha256(unlock_code.encode()).hexdigest()
    return provided_hash == expected_hash


def _process_single_request(engine, timing, req, run_id, event_producer):
    decision = engine.evaluate(req)
    lane = decision.selected_route or "unrouted"
    expected_output = max(50, req.token_estimate // 10)

    t = timing.simulate(
        lane=lane,
        task_type=req.task_type,
        token_estimate=req.token_estimate,
        expected_output_tokens=expected_output,
        modality=req.modality,
        image_count=req.image_count,
        page_count=req.page_count,
    )

    hw_label = "GPU" if lane == "overdrive" else "Xeon 6"
    reason_codes = decision.reason_codes or []
    routing_reason = _build_routing_reason(lane, req.task_type, req.token_estimate, reason_codes)

    result_entry = {
        "lane": lane,
        "task_type": req.task_type,
        "latency_ms": t["latency_ms"],
        "input_tokens": req.token_estimate,
        "output_tokens": expected_output,
        "prompt": req.prompt or "",
        "hw": hw_label,
        "routing_reason": routing_reason,
        "outcome": decision.outcome,
        "modality": req.modality,
        "image_count": req.image_count,
        "page_count": req.page_count,
        "image_url": req.metadata.get("image_url", ""),
        "image_title": req.metadata.get("image_title", ""),
    }

    event_producer.emit({
        "run_id": run_id,
        "request_id": req.request_id,
        "task_type": req.task_type,
        "lane": lane,
        "hw": hw_label,
        "latency_ms": t["latency_ms"],
        "input_tokens": req.token_estimate,
        "routing_reason": routing_reason,
        "modality": req.modality,
        "image_count": req.image_count,
        "image_url": req.metadata.get("image_url", ""),
        "image_title": req.metadata.get("image_title", ""),
    })

    return result_entry


def run_workload(
    profile: str,
    mode: str,
    seed: int = 42,
    count: int = None,
    concurrency: int = None,
    live: bool = False,
    unlock_code: str = "",
    config_path: Path = None,
    rubric_dir: Path = None,
) -> dict:
    if live and mode in GOVERNED_MODES:
        if not unlock_code or not _verify_unlock(unlock_code):
            raise PermissionError(
                f"Live mode with '{mode}' requires a valid unlock code. "
                f"Modes {sorted(GOVERNED_MODES)} are governed to protect the LiteLLM backend."
            )

    config_path = config_path or _DEFAULT_CONFIG
    rubric_dir = rubric_dir or _DEFAULT_RUBRICS
    engine = OverdriveEngine(config_path=config_path, rubric_dir=rubric_dir)

    if live:
        api_key = os.getenv("API_KEY", "")
        timing = RealTimingProvider(gateway_url="http://localhost:8080", api_key=api_key)
    else:
        timing = MockTimingProvider(seed=seed)

    requests = generate_workload(
        profile=profile, mode=mode, seed=seed,
        count=count, concurrency=concurrency,
    )

    mode_cfg = get_mode_config(mode, count=count, concurrency=concurrency)
    max_workers = mode_cfg["concurrency"]

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    event_producer = get_event_producer()
    start = time.monotonic()

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_process_single_request, engine, timing, req, run_id, event_producer): i
            for i, req in enumerate(requests)
        }
        for future in as_completed(futures):
            results.append(future.result())

    elapsed = (time.monotonic() - start) * 1000

    metrics = collect_metrics(results, total_duration_ms=elapsed)
    metrics["run_id"] = run_id
    metrics["workload_profile"] = profile
    metrics["power_mode"] = mode
    metrics["concurrency"] = max_workers
    metrics["mode_label"] = "live" if live else "simulated"
    metrics["events"] = event_producer.get_events()

    metrics["report_json"] = generate_json_report(metrics)
    metrics["report_md"] = generate_markdown_report(metrics)

    return metrics


def run_workload_streaming(
    profile: str,
    mode: str,
    seed: int = 42,
    count: int = None,
    concurrency: int = None,
    live: bool = False,
    unlock_code: str = "",
    run_state: dict = None,
    config_path: Path = None,
    rubric_dir: Path = None,
) -> dict:
    """Like run_workload but updates run_state dict in real-time for polling."""
    if live and mode in GOVERNED_MODES:
        if not unlock_code or not _verify_unlock(unlock_code):
            raise PermissionError("Unlock code required")

    config_path = config_path or _DEFAULT_CONFIG
    rubric_dir = rubric_dir or _DEFAULT_RUBRICS
    engine = OverdriveEngine(config_path=config_path, rubric_dir=rubric_dir)

    if live:
        api_key = os.getenv("API_KEY", "")
        timing = RealTimingProvider(gateway_url="http://localhost:8080", api_key=api_key)
    else:
        timing = MockTimingProvider(seed=seed)

    requests = generate_workload(
        profile=profile, mode=mode, seed=seed,
        count=count, concurrency=concurrency,
    )

    mode_cfg = get_mode_config(mode, count=count, concurrency=concurrency)
    max_workers = mode_cfg["concurrency"]

    run_id = run_state["run_id"] if run_state else f"run-{uuid.uuid4().hex[:8]}"
    event_producer = get_event_producer()
    if run_state:
        run_state["total"] = len(requests)
        run_state["concurrency"] = max_workers

    start = time.monotonic()
    results = []
    results_lock = threading.Lock()
    completed_count = 0
    count_lock = threading.Lock()

    def _process_and_track(req):
        nonlocal completed_count
        result = _process_single_request(engine, timing, req, run_id, event_producer)
        with results_lock:
            results.append(result)
        with count_lock:
            completed_count += 1
            if run_state:
                run_state["completed"] = completed_count
                run_state["results"] = list(results)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_process_and_track, req) for req in requests]
        for future in as_completed(futures):
            future.result()

    elapsed = (time.monotonic() - start) * 1000

    metrics = collect_metrics(results, total_duration_ms=elapsed)
    metrics["run_id"] = run_id
    metrics["workload_profile"] = profile
    metrics["power_mode"] = mode
    metrics["concurrency"] = max_workers
    metrics["mode_label"] = "live" if live else "simulated"
    metrics["events"] = event_producer.get_events()

    metrics["report_json"] = generate_json_report(metrics)
    metrics["report_md"] = generate_markdown_report(metrics)

    return metrics
