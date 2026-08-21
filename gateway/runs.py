"""
Run management endpoints — workload, agent, swarm, training.

Extracted from router.py (Phase 3). Owns the in-memory run state dicts,
cleanup logic, platform status aggregation, and capacity overview.
"""

import threading
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import db
from utils import sanitize_prompt as _sanitize_prompt, check_rate_limit

router = APIRouter()

_runs_lock = threading.Lock()
_workload_runs: dict = {}
_agent_runs: dict = {}
_training_runs: dict = {}
_swarm_runs: dict = {}
_RUN_EXPIRY_SECONDS = 600


def _cleanup_old_runs():
    now = time.time()
    for store in (_workload_runs, _agent_runs, _swarm_runs, _training_runs):
        expired = [k for k, v in store.items()
                   if v.get("status") in ("complete", "completed", "error")
                   and now - v.get("started_at", now) > _RUN_EXPIRY_SECONDS]
        for k in expired:
            store.pop(k, None)


# ─── Platform Status ───

@router.get("/v1/platform/status")
async def platform_status():
    """Unified platform status — aggregates all active runs for cockpit dashboard."""
    from router import LANE_MODEL_MAP

    active_runs = []
    latest_completed = None
    training_info = None

    with _runs_lock:
        workload_snapshot = dict(_workload_runs)
        agent_snapshot = dict(_agent_runs)
        training_snapshot = dict(_training_runs)
        swarm_snapshot = dict(_swarm_runs)

    for run_id, run in workload_snapshot.items():
        if run.get("status") == "running":
            active_runs.append({"type": "workload", "run_id": run_id, "profile": run.get("workload_profile", ""), "mode": run.get("power_mode", ""), "completed": run.get("completed", 0), "total": run.get("total", 0)})
        elif run.get("status") == "complete" and (latest_completed is None or run.get("completed_at", 0) > latest_completed.get("_completed_at", 0)):
            latest_completed = {"type": "workload", "run_id": run_id, "_completed_at": run.get("completed_at", 0), **{k: run.get(k) for k in ["workload_profile", "power_mode", "total_requests", "completed_requests", "route_counts", "requests_per_second", "estimated_tokens_per_second", "p50_latency_ms", "p95_latency_ms", "p99_latency_ms", "xeon_eco_utilization_pct", "xeon_performance_utilization_pct", "gaudi_overdrive_utilization_pct", "total_images", "total_documents", "modality_counts", "mode_label", "results"]}}

    for run_id, run in agent_snapshot.items():
        if run.get("status") == "running":
            active_runs.append({"type": "agent", "run_id": run_id, "steps_done": len([s for s in run.get("steps", []) if s.get("status") == "done"]), "steps_total": len(run.get("steps", []))})

    for run_id, run in training_snapshot.items():
        if run.get("status") == "running":
            active_runs.append({"type": "training", "run_id": run_id})
            training_info = {"status": "running", "run_id": run_id}
        elif run.get("status") == "completed":
            training_info = {"status": "completed", "run_id": run_id, "model": run.get("model_profile_id", ""), "base_score": run.get("evaluation", {}).get("base_score", 0), "tuned_score": run.get("evaluation", {}).get("tuned_score", 0), "improvement": run.get("evaluation", {}).get("improvement", 0)}

    swarm_completed = None
    for run_id, run in swarm_snapshot.items():
        if run.get("status") == "running":
            agent_results = run.get("agent_results", [])
            total_agents = len(run.get("timeline", [])) or len(agent_results)
            active_runs.append({"type": "swarm", "run_id": run_id, "scenario": run.get("scenario", ""), "agents_done": len([a for a in agent_results if a.get("status") == "done"]), "agents_total": total_agents})
        elif run.get("status") == "completed":
            if swarm_completed is None:
                swarm_completed = {"run_id": run_id, "scenario": run.get("scenario", ""), "agent_count": run.get("agent_count", 0), "route_counts": run.get("route_counts", {}), "total_ms": run.get("total_ms", 0)}

    agg_mode = "STANDBY"
    agg_rps = 0
    agg_tps = 0
    agg_p95 = 0
    agg_routes = {}
    agg_images = 0
    agg_docs = 0
    agg_modalities = {}
    live_progress = None

    model_telemetry = {}
    task_telemetry = {}

    active_workloads = [r for r in _workload_runs.values() if r.get("status") == "running"]
    if active_workloads:
        aw = active_workloads[0]
        agg_mode = (aw.get("power_mode", aw.get("mode", "DRIVE")) or "DRIVE").upper()
        results = aw.get("results", [])
        completed = aw.get("completed", 0)
        total = aw.get("total", 0)
        if results:
            from collections import Counter
            rc = dict(Counter(r.get("lane", "unknown") for r in results))
            agg_routes = rc
            latencies = sorted(r.get("latency_ms", 0) for r in results)
            agg_images = sum(r.get("image_count", 0) for r in results)
            agg_docs = sum(1 for r in results if r.get("page_count", 0) > 0)
            agg_modalities = dict(Counter(r.get("modality", "text") for r in results))
            elapsed_sec = max(sum(r.get("latency_ms", 0) for r in results) / 1000, 0.1)
            agg_rps = round(len(results) / elapsed_sec, 1)
            total_tokens = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in results)
            agg_tps = round(total_tokens / elapsed_sec, 0)
            if latencies:
                idx = int(len(latencies) * 0.95)
                agg_p95 = round(latencies[min(idx, len(latencies) - 1)], 1)
        live_progress = {"completed": completed, "total": total, "pct": round(completed / total * 100) if total else 0}

        from collections import defaultdict as _dd
        model_stats = _dd(lambda: {"count": 0, "total_latency": 0, "total_input_tokens": 0, "total_output_tokens": 0, "tasks": _dd(int)})
        task_stats = _dd(lambda: {"count": 0, "total_latency": 0, "lanes": _dd(int)})
        for r in results:
            lane = r.get("lane", "unknown")
            task = r.get("task_type", "unknown")
            lat = r.get("latency_ms", 0)
            inp = r.get("input_tokens", 0)
            out = r.get("output_tokens", 0)
            model_name = LANE_MODEL_MAP.get(lane, "unknown")
            ms = model_stats[model_name]
            ms["count"] += 1
            ms["total_latency"] += lat
            ms["total_input_tokens"] += inp
            ms["total_output_tokens"] += out
            ms["tasks"][task] += 1
            ts = task_stats[task]
            ts["count"] += 1
            ts["total_latency"] += lat
            ts["lanes"][lane] += 1

        for mname, ms in model_stats.items():
            avg_lat = round(ms["total_latency"] / ms["count"], 1) if ms["count"] else 0
            tps = round(ms["total_output_tokens"] / (ms["total_latency"] / 1000)) if ms["total_latency"] > 0 else 0
            model_telemetry[mname] = {
                "count": ms["count"],
                "avg_latency_ms": avg_lat,
                "total_input_tokens": ms["total_input_tokens"],
                "total_output_tokens": ms["total_output_tokens"],
                "tokens_per_sec": tps,
                "tasks": dict(ms["tasks"]),
            }

        for tname, ts in task_stats.items():
            avg_lat = round(ts["total_latency"] / ts["count"], 1) if ts["count"] else 0
            task_telemetry[tname] = {"count": ts["count"], "avg_latency_ms": avg_lat, "lanes": dict(ts["lanes"])}
    elif latest_completed:
        agg_rps = latest_completed.get("requests_per_second", 0) or 0
        agg_tps = latest_completed.get("estimated_tokens_per_second", 0) or 0
        agg_routes = latest_completed.get("route_counts", {}) or {}
        agg_mode = (latest_completed.get("power_mode", "standby") or "standby").upper()
        agg_p95 = latest_completed.get("p95_latency_ms", 0) or 0
        agg_images = latest_completed.get("total_images", 0) or 0
        agg_docs = latest_completed.get("total_documents", 0) or 0
        agg_modalities = latest_completed.get("modality_counts", {}) or {}

        results = latest_completed.get("results", [])
        if results:
            from collections import defaultdict as _dd
            model_stats = _dd(lambda: {"count": 0, "total_latency": 0, "total_input_tokens": 0, "total_output_tokens": 0, "tasks": _dd(int)})
            task_stats = _dd(lambda: {"count": 0, "total_latency": 0, "lanes": _dd(int)})
            for r in results:
                lane = r.get("lane", "unknown")
                task = r.get("task_type", "unknown")
                lat = r.get("latency_ms", 0)
                inp = r.get("input_tokens", 0)
                out = r.get("output_tokens", 0)
                model_name = LANE_MODEL_MAP.get(lane, "unknown")
                ms = model_stats[model_name]
                ms["count"] += 1
                ms["total_latency"] += lat
                ms["total_input_tokens"] += inp
                ms["total_output_tokens"] += out
                ms["tasks"][task] += 1
                ts = task_stats[task]
                ts["count"] += 1
                ts["total_latency"] += lat
                ts["lanes"][lane] += 1
            for mname, ms in model_stats.items():
                avg_lat = round(ms["total_latency"] / ms["count"], 1) if ms["count"] else 0
                tps_val = round(ms["total_output_tokens"] / (ms["total_latency"] / 1000)) if ms["total_latency"] > 0 else 0
                model_telemetry[mname] = {"count": ms["count"], "avg_latency_ms": avg_lat, "total_input_tokens": ms["total_input_tokens"], "total_output_tokens": ms["total_output_tokens"], "tokens_per_sec": tps_val, "tasks": dict(ms["tasks"])}
            for tname, ts in task_stats.items():
                avg_lat = round(ts["total_latency"] / ts["count"], 1) if ts["count"] else 0
                task_telemetry[tname] = {"count": ts["count"], "avg_latency_ms": avg_lat, "lanes": dict(ts["lanes"])}

    return {
        "active_runs": active_runs,
        "latest_completed": latest_completed,
        "training": training_info,
        "swarm_completed": swarm_completed,
        "live_progress": live_progress,
        "model_telemetry": model_telemetry,
        "task_telemetry": task_telemetry,
        "aggregate": {
            "mode": agg_mode,
            "requests_per_second": agg_rps,
            "estimated_tokens_per_second": agg_tps,
            "p95_latency_ms": agg_p95,
            "route_counts": agg_routes,
            "total_images": agg_images,
            "total_documents": agg_docs,
            "modality_counts": agg_modalities,
            "active_count": len(active_runs),
        },
    }


# ─── Workload Endpoints ───

@router.get("/v1/workload/profiles")
async def workload_profiles():
    from overdrive.workload_profiles import list_profiles, SCENARIO_NARRATIVES
    from overdrive.power_modes import list_modes
    return {"profiles": list_profiles(), "modes": list_modes(), "narratives": SCENARIO_NARRATIVES}


class WorkloadRunRequest(BaseModel):
    profile: str
    mode: str
    seed: int = 42
    live: bool = False
    unlock_code: str = ""


@router.post("/v1/workload/run")
async def workload_run(req: WorkloadRunRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    from overdrive.batch_runner import run_workload_streaming, _verify_unlock, GOVERNED_MODES

    if req.live and req.mode in GOVERNED_MODES:
        if not req.unlock_code or not _verify_unlock(req.unlock_code):
            raise HTTPException(status_code=403, detail="Unlock code required for live mode with this power mode")

    with _runs_lock:
        _cleanup_old_runs()

    run_id = f"run-{uuid.uuid4().hex[:8]}"

    run_state = {
        "run_id": run_id,
        "status": "running",
        "completed": 0,
        "total": 0,
        "results": [],
        "started_at": time.time(),
    }
    with _runs_lock:
        _workload_runs[run_id] = run_state

    def _run_in_background():
        try:
            result = run_workload_streaming(
                profile=req.profile, mode=req.mode, seed=req.seed,
                live=req.live, unlock_code=req.unlock_code,
                run_state=run_state,
            )
            run_state.update(result)
            run_state["status"] = "complete"
            run_state["completed_at"] = time.time()
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(db.persist_run(
                    run_id=run_id, run_type="workload", status="complete",
                    summary={"profile": req.profile, "mode": req.mode, "total": run_state.get("total", 0), "route_counts": run_state.get("route_counts", {})}
                ))
                loop.close()
            except Exception:
                pass
        except PermissionError as e:
            run_state["status"] = "error"
            run_state["error"] = str(e)
        except Exception as e:
            run_state["status"] = "error"
            run_state["error"] = str(e)

    thread = threading.Thread(target=_run_in_background, daemon=True)
    thread.start()

    return {"run_id": run_id, "status": "running"}


@router.get("/v1/workload/status/{run_id}")
async def workload_status(run_id: str):
    with _runs_lock:
        run = _workload_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run


# ─── Agent Research Endpoints ───

class AgentResearchRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    governance_mode: str = Field(default="open", pattern=r"^(open|supervised|locked)$")
    live: bool = False


@router.post("/v1/agent/research")
async def agent_research(req: AgentResearchRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    run_id = f"agent-{uuid.uuid4().hex[:8]}"
    run_state = {"run_id": run_id, "status": "running", "steps": [], "started_at": time.time()}
    with _runs_lock:
        _cleanup_old_runs()
        _agent_runs[run_id] = run_state

    def _run():
        try:
            from overdrive.research_agent import run_research_agent
            run_research_agent(
                question=_sanitize_prompt(req.question),
                governance_mode=req.governance_mode,
                live=req.live,
                run_state=run_state,
            )
        except Exception as e:
            run_state["status"] = "error"
            run_state["error"] = str(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"run_id": run_id, "status": "running"}


@router.get("/v1/agent/status/{run_id}")
async def agent_status(run_id: str):
    with _runs_lock:
        run = _agent_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Agent run '{run_id}' not found")
    return run


@router.post("/v1/agent/approve/{run_id}/{step_name}")
async def agent_approve(run_id: str, step_name: str):
    with _runs_lock:
        run = _agent_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Agent run '{run_id}' not found")
    for step in run.get("steps", []):
        if step["name"] == step_name and step["status"] == "awaiting_approval":
            step["status"] = "approved"
            return {"approved": True, "step": step_name}
    return {"approved": False, "detail": f"Step '{step_name}' not awaiting approval"}


# ─── Swarm Endpoints ───

class SwarmRunRequest(BaseModel):
    scenario: str = "incident"
    seed: int = 42
    depth: str = Field(default="full", pattern=r"^(triage|full|deep)$")


@router.post("/v1/swarm/run")
async def swarm_run(req: SwarmRunRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    run_id = f"swarm-{uuid.uuid4().hex[:8]}"
    run_state = {"run_id": run_id, "status": "running", "agent_results": [], "timeline": [], "type": "swarm", "started_at": time.time()}
    with _runs_lock:
        _cleanup_old_runs()
        _swarm_runs[run_id] = run_state

    def _run():
        try:
            from overdrive.swarm import run_swarm
            run_swarm(scenario=req.scenario, depth=req.depth, seed=req.seed, run_state=run_state)
        except Exception as e:
            run_state["status"] = "error"
            run_state["error"] = str(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"run_id": run_id, "status": "running"}


@router.get("/v1/swarm/status/{run_id}")
async def swarm_status(run_id: str):
    with _runs_lock:
        run = _swarm_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Swarm run '{run_id}' not found")
    return run


# ─── Training Endpoints ───

@router.get("/v1/training/profiles")
async def training_profiles():
    from overdrive.training_models import list_model_profiles, list_dataset_profiles, list_training_tasks
    return {"models": list_model_profiles(), "datasets": list_dataset_profiles(), "tasks": list_training_tasks()}


class TrainingRunRequest(BaseModel):
    task: str
    model: str
    dataset: str
    mode: str = "mock_lora"
    seed: int = 42


@router.post("/v1/training/run")
async def training_run(req: TrainingRunRequest, raw_request: Request):
    check_rate_limit(raw_request.client.host)
    run_id = f"train-{uuid.uuid4().hex[:8]}"
    run_state = {"run_id": run_id, "status": "running", "started_at": time.time()}
    with _runs_lock:
        _cleanup_old_runs()
        _training_runs[run_id] = run_state

    def _run():
        try:
            from overdrive.training_backend import MockTrainingBackend
            from overdrive.training_report import generate_training_markdown, generate_model_card
            backend = MockTrainingBackend(seed=req.seed)
            result = backend.run(req.task, req.model, req.dataset, req.mode, req.seed)
            candidate = backend.create_serving_candidate(result)
            from dataclasses import asdict
            run_state.update(asdict(result))
            run_state["serving_candidate"] = asdict(candidate)
            run_state["report_md"] = generate_training_markdown(result)
            run_state["model_card"] = generate_model_card(result)
            run_state["status"] = "completed"
        except Exception as e:
            run_state["status"] = "error"
            run_state["error"] = str(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"run_id": run_id, "status": "running"}


@router.get("/v1/training/status/{run_id}")
async def training_status(run_id: str):
    with _runs_lock:
        run = _training_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Training run '{run_id}' not found")
    return run


# ─── Run History ───

@router.get("/v1/runs/history")
async def run_history(run_type: str = None, limit: int = 50):
    runs = await db.get_run_history(run_type=run_type, limit=limit)
    return {"runs": runs}


# ─── Capacity Overview ───

@router.get("/v1/capacity/overview")
async def capacity_overview():
    tenants = await db.list_tenants()
    active_counts = {}
    with _runs_lock:
        all_runs = list(_workload_runs.values()) + list(_swarm_runs.values()) + list(_training_runs.values()) + list(_agent_runs.values())
    for run in all_runs:
        tid = run.get("tenant_id", "internal")
        if run.get("status") == "running":
            active_counts[tid] = active_counts.get(tid, 0) + 1

    capacity = []
    for t in tenants:
        quota = t.get("resource_quota", {}) if isinstance(t.get("resource_quota"), dict) else {}
        capacity.append({
            "slug": t.get("slug", ""),
            "display_name": t.get("display_name", ""),
            "tier": t.get("tier", ""),
            "active": t.get("active", True),
            "expires_at": str(t.get("expires_at", "")) if t.get("expires_at") else None,
            "resource_quota": quota,
            "active_runs": active_counts.get(str(t.get("id", "")), 0),
        })
    return {"tenants": capacity, "total_active_runs": sum(active_counts.values())}
