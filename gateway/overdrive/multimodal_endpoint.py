"""Mock multimodal endpoint — deterministic synthetic responses per task type."""

import random

MOCK_RESPONSES = {
    "image_classification": [
        "Category: latency_anomaly | Confidence: 0.94 | Tags: latency_spike, service_degradation",
        "Category: normal_operations | Confidence: 0.87 | Tags: steady_state, healthy",
        "Category: resource_pressure | Confidence: 0.91 | Tags: cpu_high, memory_pressure",
    ],
    "screenshot_classification": [
        "Dashboard Type: latency_monitoring | Panels: 4 | Alert State: firing",
        "Dashboard Type: throughput_overview | Panels: 6 | Alert State: normal",
        "Dashboard Type: error_rate_tracker | Panels: 3 | Alert State: warning",
    ],
    "screenshot_summary": [
        "This Grafana dashboard shows a significant latency spike starting at 14:23 UTC. The p99 latency increased from 200ms to 4,500ms over 15 minutes. The error rate panel shows a correlated increase from 0.1% to 3.2%. The service status panel indicates 2 of 5 inference pods are unhealthy. Recommended action: investigate Gaudi memory pressure as the likely cause.",
        "The operations dashboard displays normal throughput at 850 req/s with stable latency at p50=12ms, p99=89ms. All inference lanes are green. Xeon 6 eco utilization is at 34%, performance at 52%, and Gaudi overdrive at 18%. No anomalies detected.",
    ],
    "chart_interpretation": [
        "This time-series chart shows p99 latency (blue line) increasing from 200ms to 4,500ms between 14:23 and 14:38 UTC. The request volume (grey area) remained constant at ~900 req/s, indicating the latency increase is not load-driven. The vertical red marker at 14:25 corresponds to a Gaudi health check failure. Correlation: latency spike began 2 minutes after Gaudi went offline, consistent with fallback routing to Xeon 6 Performance lane.",
    ],
    "diagram_explanation": [
        "This architecture diagram shows a dual-path inference routing system. Requests enter through a single gateway (top) which evaluates task type, token count, and priority. Three lanes branch from the gateway: Eco (Granite Tiny on Xeon 6, green), Performance (CodeLlama 7B on Xeon 6, blue), and Overdrive (Llama Scout 17B on Gaudi, orange). Fallback arrows show Overdrive failing to Performance, and Performance failing to Eco. A PostgreSQL database stores routing decisions, and a React frontend provides the dashboard.",
    ],
    "document_visual_summary": [
        "This 12-page technical document covers the Intel-Red Hat AI Inference Platform architecture. Key sections: (1) Dual-path routing across Xeon 6 and Gaudi hardware, (2) Overdrive lane evaluation with rubric-based checks, (3) Workload profiles for enterprise simulation, (4) Tokenization and cost model showing 10x savings on Xeon 6 for small tasks, (5) Failover mechanisms with zero-drop request routing. The document includes 4 architecture diagrams and 3 performance comparison charts.",
    ],
    "visual_rag_question": [
        "Based on the architecture diagram and deployment documentation: The routing engine decides between Xeon 6 and Gaudi by evaluating a routing matrix with these criteria: (1) Task type — classification and embeddings always go to Xeon 6, (2) Token count — requests under 4K tokens stay on Eco, under 16K on Performance, over 16K route to Gaudi Overdrive, (3) Priority — only high/critical priority requests qualify for Gaudi. This ensures cost efficiency: Xeon 6 handles ~70% of requests at 1/10th the cost of Gaudi.",
    ],
    "multimodal_incident_summary": [
        "Incident Summary — Gaudi Accelerator Overload (14:23-14:50 UTC)\n\nDashboard evidence: 5 screenshots analyzed. The latency dashboard shows p99 spike from 200ms to 4,500ms. The Gaudi memory panel shows HBM utilization reaching 97%. The error rate chart shows 3.2% failure rate during the incident window.\n\nRoot cause: An unthrottled batch summarization job consumed all 96GB of Gaudi HBM, preventing new inference requests. The routing engine correctly activated fallback to Xeon 6 Performance lane, but the sudden traffic shift caused temporary queue buildup.\n\nImpact: 142 requests exceeded SLA (10s p99 target). Zero requests dropped. All requests were served via Xeon 6 fallback.\n\nResolution: Batch job terminated at 14:48 UTC. Gaudi memory freed. Overdrive lane restored at 14:50 UTC.",
    ],
    "multimodal_rca": [
        "Root Cause Analysis — Multi-source evidence synthesis\n\nEvidence sources: 3 dashboard screenshots, 2 architecture diagrams, 47 log lines\n\nChain of events:\n1. Batch summarization job scheduled without resource limits (batch-job-7842)\n2. Job consumed 94GB of 96GB Gaudi HBM within 3 minutes\n3. New inference requests queued — no HBM available for model loading\n4. Health check failed at 14:25 UTC → overdrive lane marked unhealthy\n5. Routing engine activated fallback: overdrive → performance (Xeon 6)\n6. Performance lane received 4x normal traffic, p99 latency increased to 4,500ms\n7. SLA breach detected at 14:28 UTC (threshold: 10,000ms p99)\n\nRoot cause: Missing resource limits on batch generation workloads. The admission controller did not enforce a token budget for Gaudi lane.\n\nRecommendation: Add habana.ai/gaudi resource limits to batch workload manifests. Implement token budget admission controller.",
    ],
    "image_text_embedding": [
        "Embedding generated: 768 dimensions | Model: nomic-embed-multimodal | Modality: image+text | Processing: 12ms",
    ],
    "visual_similarity": [
        "Top 3 similar images: (1) dashboard-latency-spike-002 [score: 0.94], (2) grafana-error-rate-001 [score: 0.87], (3) dashboard-throughput-001 [score: 0.72]",
    ],
    "ocr_layout_extract": [
        "Extracted text: 'Inference Gateway Latency — p99: 4,521ms | p50: 234ms | Error Rate: 3.2% | Requests/sec: 847' | Layout: 3 panels, 2 charts, 1 status table | Confidence: 0.96",
    ],
}


class MockMultimodalEndpoint:
    def __init__(self, seed: int = 42):
        self._seed = seed

    def respond(self, task_type: str, request_id: str = "") -> dict:
        rng = random.Random(self._seed ^ hash(request_id))
        responses = MOCK_RESPONSES.get(task_type, ["[Synthetic multimodal response for " + task_type + "]"])
        text = responses[rng.randint(0, len(responses) - 1)]
        return {
            "response_text": text,
            "task_type": task_type,
            "endpoint": "mock_multimodal",
            "source": "synthetic",
        }
