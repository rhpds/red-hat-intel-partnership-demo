"""Agent Swarm — multi-agent coordination across Intel hardware."""

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class SwarmAgent:
    id: str
    name: str
    role: str
    hardware_lane: str
    task_type: str
    status: str = "pending"


INCIDENT_SWARM = {
    "name": "Incident Investigation Swarm",
    "description": "5 specialized agents investigate a production incident in parallel across Intel Xeon 6 and Gaudi.",
    "agents": [
        {"id": "triage", "name": "Triage Agent", "role": "Classify severity and identify affected services", "hardware_lane": "xeon_eco", "task_type": "classification", "hw_label": "Intel Xeon 6 Eco", "model": "granite-4-0-h-tiny"},
        {"id": "log_analyst", "name": "Log Analyst", "role": "Parse logs and find error patterns", "hardware_lane": "xeon_performance", "task_type": "rerank", "hw_label": "Intel Xeon 6 + AMX", "model": "codellama-7b-instruct"},
        {"id": "metrics", "name": "Metrics Agent", "role": "Analyze dashboards and interpret charts", "hardware_lane": "gaudi_overdrive", "task_type": "chart_interpretation", "hw_label": "Intel Gaudi", "model": "llama-scout-17b"},
        {"id": "rca", "name": "RCA Agent", "role": "Deep root cause analysis combining all findings", "hardware_lane": "gaudi_overdrive", "task_type": "incident_rca", "hw_label": "Intel Gaudi", "model": "llama-scout-17b"},
        {"id": "reporter", "name": "Reporter Agent", "role": "Synthesize findings into executive report", "hardware_lane": "gaudi_overdrive", "task_type": "batch_summary", "hw_label": "Intel Gaudi", "model": "llama-scout-17b"},
    ],
    "waves": [
        {"wave": 1, "label": "Parallel Investigation", "agents": ["triage", "log_analyst", "metrics"], "depends_on": None, "desc": "Three agents investigate simultaneously — classification on Xeon 6, log analysis on Xeon 6 + AMX, dashboard interpretation on Gaudi."},
        {"wave": 2, "label": "Root Cause Analysis", "agents": ["rca"], "depends_on": 0, "desc": "RCA agent receives all findings from Wave 1 and performs deep analysis on Gaudi."},
        {"wave": 3, "label": "Report Generation", "agents": ["reporter"], "depends_on": 1, "desc": "Reporter synthesizes everything into an executive summary on Gaudi."},
    ],
}

MOCK_AGENT_OUTPUTS = {
    "triage": {
        "output": "Severity: P1 — CRITICAL\nAffected services: checkout-service, payment-service, inference-gateway\nImpact: Customer-facing checkout flow degraded. Inference latency exceeding SLA.\nInitial classification: Cascading failure originating from payment-service connection pool exhaustion.",
        "latency_ms": 85,
    },
    "log_analyst": {
        "output": "Error patterns found (last 30 minutes):\n1. 47x 'connection pool exhausted' in payment-service (14:23-14:50 UTC)\n2. 23x 'timeout connecting to payment-service' in checkout-service\n3. 12x 'fallback routing activated' in inference-gateway\n4. 8x 'HBM allocation failed' in gaudi-inference namespace\n\nTimeline: payment-service connection pool hit limit at 14:23 → cascade started at 14:25 → Gaudi HBM pressure at 14:28 → full degradation at 14:32",
        "latency_ms": 320,
    },
    "metrics": {
        "output": "Dashboard analysis (3 panels examined):\n1. Latency panel: p99 spike from 200ms to 4,500ms starting 14:23 UTC. Not load-driven (request volume stable at 850 req/s).\n2. Error rate panel: 0.1% → 3.2% correlated with latency spike. HTTP 502 errors concentrated on /v1/route endpoint.\n3. Resource panel: Gaudi HBM utilization hit 97% at 14:28. Xeon 6 CPU stable at 55%. Correlation: latency spike began 5 minutes before Gaudi saturation.",
        "latency_ms": 1200,
    },
    "rca": {
        "output": "ROOT CAUSE ANALYSIS\n\nPrimary cause: Payment-service connection pool exhaustion (limit: 50 connections, peak demand: 120)\n\nCascade chain:\n1. Payment-service pool saturated → checkout-service timeouts\n2. Checkout retries amplified load → payment-service further degraded\n3. Inference gateway batch job consumed 94GB of 96GB Gaudi HBM\n4. New inference requests queued → routing engine activated Xeon 6 fallback\n5. Xeon 6 Performance lane received 4x normal traffic → p99 spike\n\nContributing factor: Unthrottled batch-job-7842 consumed Gaudi HBM without resource limits.\n\nRecommended fix:\n- Immediate: Increase payment-service pool to 200, terminate batch-job-7842\n- Short-term: Add circuit breaker to checkout→payment path, add Gaudi resource limits\n- Long-term: Implement token budget admission controller for Gaudi lane",
        "latency_ms": 2800,
    },
    "reporter": {
        "output": "EXECUTIVE INCIDENT REPORT\n\nIncident: Production checkout degradation\nDuration: 27 minutes (14:23-14:50 UTC)\nSeverity: P1\nImpact: 142 requests exceeded SLA. Zero requests dropped.\n\nWhat happened: A payment-service connection pool limit caused checkout timeouts. Simultaneously, an unthrottled batch job consumed all Gaudi accelerator memory. The routing engine correctly fell back to Xeon 6, but the combined load from both failures caused temporary latency spikes.\n\nWhat worked: Intelligent routing detected Gaudi failure and rerouted to Xeon 6 within 2 minutes. No requests were dropped. The platform degraded gracefully.\n\nWhat to fix: Connection pool limits, Gaudi resource quotas, and batch job admission controls.\n\nHardware insight: Intel Xeon 6 handled the fallback traffic at acceptable latency. Intel Gaudi recovered fully once the batch job was terminated. The dual-path architecture prevented a complete outage.",
        "latency_ms": 3200,
    },
}

SWARM_SCENARIOS = {
    "incident": INCIDENT_SWARM,
}


def run_swarm(scenario: str = "incident", seed: int = 42, run_state: dict = None) -> dict:
    swarm = SWARM_SCENARIOS.get(scenario, INCIDENT_SWARM)
    rng = random.Random(seed)
    agents = {a["id"]: {**a, "status": "pending"} for a in swarm["agents"]}
    timeline = []
    agent_results = []
    start = time.monotonic()

    for wave_idx, wave in enumerate(swarm["waves"]):
        wave_start = time.monotonic() - start

        for agent_id in wave["agents"]:
            agent = agents[agent_id]
            agent["status"] = "running"
            t0 = time.monotonic() - start

            mock = MOCK_AGENT_OUTPUTS.get(agent_id, {"output": f"[{agent_id} output]", "latency_ms": 500})
            jitter = rng.uniform(0.8, 1.2)
            latency = round(mock["latency_ms"] * jitter, 1)

            agent["status"] = "done"
            t1 = time.monotonic() - start

            result = {
                "agent_id": agent_id,
                "name": agent["name"],
                "role": agent["role"],
                "hardware_lane": agent["hardware_lane"],
                "hw_label": agent.get("hw_label", agent["hardware_lane"]),
                "model": agent.get("model", "unknown"),
                "status": "done",
                "output": mock["output"],
                "latency_ms": latency,
                "wave": wave_idx + 1,
            }
            agent_results.append(result)

            timeline.append({
                "agent_id": agent_id,
                "name": agent["name"],
                "wave": wave_idx + 1,
                "hw": agent.get("hw_label", ""),
                "started_at": round(t0, 2),
                "completed_at": round(t1, 2),
                "latency_ms": latency,
            })

        if run_state:
            run_state["agent_results"] = list(agent_results)
            run_state["timeline"] = list(timeline)
            run_state["current_wave"] = wave_idx + 1

    total_ms = round((time.monotonic() - start) * 1000, 1)

    reporter_output = next((r["output"] for r in agent_results if r["agent_id"] == "reporter"), "")

    result = {
        "status": "completed",
        "scenario": scenario,
        "swarm_name": swarm["name"],
        "agent_count": len(agents),
        "wave_count": len(swarm["waves"]),
        "agent_results": agent_results,
        "timeline": timeline,
        "total_ms": total_ms,
        "final_report": reporter_output,
        "waves": swarm["waves"],
    }

    if run_state:
        run_state.update(result)

    return result
