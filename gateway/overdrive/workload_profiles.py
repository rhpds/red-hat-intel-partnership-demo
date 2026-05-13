"""Named workload profiles for performance demos."""

SCENARIO_PROMPTS = {
    "incident_storm": {
        "classification": [
            "Alert: Pod ocp-worker-03 CrashLoopBackOff in namespace gaudi-inference. 5 restarts in 2 minutes.",
            "Alert: Disk pressure on node ocp-virt8-host7. /var at 94% capacity. Eviction threshold approaching.",
            "Alert: SSL certificate for model-serving route expires in 18 hours.",
            "Alert: Unauthorized API access attempt from 10.130.2.55 — 403 on /v1/route 12 times in 60s.",
            "Alert: Memory utilization on gateway pod exceeded 85%. Current: 3.4Gi of 4Gi limit.",
            "Alert: LiteLLM proxy returned 5 consecutive 502 errors for codellama-7b-instruct model.",
            "Alert: Prometheus scrape target down — ServiceMonitor intel-rh-demo/gateway unreachable.",
        ],
        "embedding": [
            "Index this incident for semantic search: Production inference gateway latency spike during peak traffic window.",
            "Vectorize alert corpus: 47 alerts received in the last 15 minutes across 3 namespaces.",
            "Generate embedding for: 'Gaudi accelerator HBM utilization reached 97% causing inference queue backup.'",
        ],
        "rerank": [
            "Rerank these 8 runbook entries against the query: 'pod CrashLoopBackOff with OOMKilled exit code'",
            "Score relevance of 5 past incidents to current alert: 'inference gateway p99 latency > 10 seconds'",
        ],
        "short_summary": [
            "Summarize the last 30 minutes of alerts: 12 pod restarts, 3 node pressure warnings, 1 certificate expiry.",
            "Create executive brief: Production AI platform experienced cascading failures starting at 14:23 UTC.",
        ],
        "long_summary": [
            "Generate comprehensive incident timeline: From initial Gaudi memory pressure alert through full platform degradation, failover to Xeon 6, and recovery. Include all 47 alerts, operator actions, and automated responses.",
        ],
        "incident_rca": [
            "Root cause analysis: The Gaudi accelerator lane went offline at 14:23 UTC. 142 requests experienced SLA violations. Investigate the chain from batch_summary job consuming all HBM through cascade to gateway timeout.",
            "Deep analysis: Why did the fallback from Gaudi to Xeon 6 Performance lane take 4 minutes instead of the expected 30 seconds? Examine routing matrix evaluation, health check intervals, and connection pool state.",
        ],
        "batch_summary": [
            "Generate overnight operations report: 24-hour window covering 15,847 inference requests across 3 hardware tiers. Include route distribution, cost analysis, SLA compliance, and capacity planning recommendations.",
        ],
    },
    "rag_barrage": {
        "embedding": [
            "Embed this knowledge base article: How to configure Intel Gaudi device plugin on OpenShift 4.15+",
            "Vectorize: Red Hat OpenShift AI operator installation and KServe ServingRuntime configuration guide",
            "Generate embeddings for: 'Troubleshooting vLLM inference timeout errors on Xeon 6 with AMX optimization'",
            "Index document: Intel Gaudi2 HBM bandwidth specifications and workload sizing guidelines",
        ],
        "rerank": [
            "Rerank 10 documentation pages against: 'How to optimize model serving latency on Intel hardware'",
            "Score relevance of 6 KB articles for: 'Gaudi out of memory error during batch inference with 17B model'",
            "Cross-encoder rerank: Query='OpenShift route timeout configuration' against 8 candidate docs",
        ],
        "rag_question": [
            "Using the retrieved context, answer: What is the maximum model size that can run on a single Gaudi card without model parallelism?",
            "Based on the documentation, explain: How does the routing engine decide between Xeon 6 and Gaudi for a completion request?",
            "Answer from knowledge base: What are the recommended resource limits for a vLLM CPU inference pod on Xeon 6?",
            "RAG synthesis: Compare the throughput characteristics of Granite-tiny on Xeon 6 vs Llama-Scout-17B on Gaudi for classification tasks.",
        ],
        "document_summary": [
            "Summarize this 40-page deployment guide: Intel-Red Hat AI Inference Platform — covering architecture, hardware requirements, operator installation, model serving configuration, monitoring setup, and capacity planning.",
        ],
    },
    "token_cannon": {
        "long_summary": [
            "Generate detailed analysis of Intel Xeon 6 with AMX acceleration performance characteristics for AI inference workloads including classification, embeddings, reranking, and small model completion.",
            "Comprehensive comparison: vLLM serving on Intel Gaudi vs CPU-only deployment — covering throughput, latency, cost, power efficiency, and workload suitability across model sizes from 1B to 70B parameters.",
        ],
        "batch_summary": [
            "Weekly platform report: Aggregate 7 days of inference telemetry — 112,438 total requests, route distribution trends, cost accumulation by hardware tier, latency regression analysis, and capacity forecast.",
        ],
        "document_summary": [
            "Distill the complete Intel Gaudi2 architecture whitepaper: tensor engine specifications, HBM2E bandwidth, inter-die connectivity, software stack integration with PyTorch and vLLM, and performance benchmarks across LLM sizes.",
        ],
        "code_summary": [
            "Analyze the inference gateway codebase: router.py (routing logic), overdrive engine (lane evaluation), rubric system (check framework), database persistence, and API surface. Identify performance bottlenecks and optimization opportunities.",
            "Review and summarize the Kubernetes manifest architecture: Kustomize overlays, KServe ServingRuntime definitions, network policies, HPA configuration, and security context constraints.",
        ],
    },
    "model_race": {
        "classification": [
            "Classify: 'The GPU node is reporting thermal throttling above 85°C during sustained batch inference.'",
            "Categorize this support ticket: 'Model download fails with 403 from HuggingFace Hub behind corporate proxy.'",
        ],
        "short_summary": [
            "Quick summary: 3 alerts fired — pod restart on worker-03, high latency on gateway, certificate expiry warning.",
            "Brief: Current platform status across 3 inference lanes — eco healthy, performance at 78% utilization, overdrive idle.",
        ],
        "long_summary": [
            "Detailed performance comparison: Run identical classification, summarization, and generation tasks on Xeon 6 (eco lane) vs Xeon 6 (performance lane) vs Gaudi (overdrive lane). Report latency, throughput, and cost per token for each.",
        ],
        "document_summary": [
            "Summarize the platform architecture document covering dual-path inference routing across Intel Xeon 6 and Gaudi hardware, including the Overdrive lane evaluation engine, rubric-based decision framework, and failover mechanisms.",
        ],
    },
}

SCENARIO_NARRATIVES = {
    "incident_storm": {
        "title": "Enterprise Incident Storm",
        "story": "A production AI platform is under pressure. Alerts are flooding in — pod crashes, memory pressure, certificate expiry, and Gaudi accelerator overload. The platform must triage every alert (Xeon 6), find relevant runbooks (Xeon 6), generate root cause analysis (Gaudi), and produce executive summaries — all simultaneously.",
        "phases": [
            {"name": "Alert Triage", "tasks": ["classification"], "hw": "Xeon 6", "desc": "Incoming alerts are classified by severity and type on Xeon 6 — fast, cheap, no GPU needed."},
            {"name": "Knowledge Retrieval", "tasks": ["embedding", "rerank"], "hw": "Xeon 6", "desc": "Alert text is embedded and matched against runbooks using Xeon 6 with AMX acceleration."},
            {"name": "Situation Summary", "tasks": ["short_summary"], "hw": "Xeon 6", "desc": "Quick executive briefs are generated on Xeon 6 for the operations dashboard."},
            {"name": "Deep Analysis", "tasks": ["long_summary", "incident_rca"], "hw": "Gaudi", "desc": "Complex root cause analysis and detailed timelines are generated on Gaudi — these need the memory bandwidth and throughput for large context windows."},
            {"name": "Overnight Report", "tasks": ["batch_summary"], "hw": "Gaudi", "desc": "End-of-shift batch reports aggregate all incidents and generate capacity planning recommendations on Gaudi."},
        ],
    },
    "rag_barrage": {
        "title": "High-Throughput RAG Pipeline",
        "story": "An enterprise knowledge base is being queried at scale. Engineers are asking questions about Intel hardware configuration, OpenShift deployment, and model optimization. Every question triggers an embed-search-rerank-generate pipeline that spans both Xeon 6 and Gaudi.",
        "phases": [
            {"name": "Document Indexing", "tasks": ["embedding"], "hw": "Xeon 6", "desc": "Knowledge base articles are vectorized on Xeon 6 using nomic-embed for fast, parallel indexing."},
            {"name": "Relevance Scoring", "tasks": ["rerank"], "hw": "Xeon 6", "desc": "Retrieved documents are re-ranked by relevance using CodeLlama cross-encoder on Xeon 6."},
            {"name": "Answer Generation", "tasks": ["rag_question"], "hw": "Mixed", "desc": "Simple questions answered on Xeon 6. Complex multi-document synthesis routed to Gaudi for deeper reasoning."},
            {"name": "Document Distillation", "tasks": ["document_summary"], "hw": "Gaudi", "desc": "Long technical documents are condensed into actionable summaries on Gaudi's high-bandwidth memory."},
        ],
    },
    "token_cannon": {
        "title": "Maximum Generation Throughput",
        "story": "The platform is stress-tested with the heaviest generation workloads — long analyses, batch reports, document distillation, and codebase reviews. Nearly everything routes to Gaudi because these tasks demand large context windows and sustained token generation.",
        "phases": [
            {"name": "Long Analysis", "tasks": ["long_summary"], "hw": "Gaudi", "desc": "Multi-page technical analyses generated on Gaudi at 100+ tokens/sec."},
            {"name": "Batch Reports", "tasks": ["batch_summary"], "hw": "Gaudi", "desc": "Week-long telemetry aggregated into comprehensive reports on Gaudi's HBM."},
            {"name": "Document Distillation", "tasks": ["document_summary"], "hw": "Gaudi", "desc": "40+ page whitepapers condensed on Gaudi using the full 400K token context window."},
            {"name": "Code Review", "tasks": ["code_summary"], "hw": "Gaudi", "desc": "Codebase analysis and optimization recommendations generated on Gaudi."},
        ],
    },
    "model_race": {
        "title": "Cross-Hardware Performance Comparison",
        "story": "The same types of tasks are run across all three hardware tiers to demonstrate why hardware-aware routing matters. Small tasks prove Xeon 6 is faster and cheaper. Large tasks prove Gaudi is essential for throughput.",
        "phases": [
            {"name": "Small Tasks → Eco", "tasks": ["classification"], "hw": "Xeon 6 Eco", "desc": "Quick classification on the lightweight Granite model — fast response, minimal cost."},
            {"name": "Mid Tasks → Performance", "tasks": ["short_summary"], "hw": "Xeon 6 Perf", "desc": "Summaries generated on CodeLlama 7B with AMX — good throughput without GPU cost."},
            {"name": "Large Tasks → Overdrive", "tasks": ["long_summary", "document_summary"], "hw": "Gaudi", "desc": "Heavy generation on Llama Scout 17B — only viable on Gaudi's HBM bandwidth."},
        ],
    },
}

PROFILES = {
    "incident_storm": {
        "description": "Simulate an enterprise incident flood — classification, triage, RCA, and batch reporting.",
        "expected_lane_bias": {"eco": "classification/triage", "overdrive": "RCA and long summaries"},
        "narrative": SCENARIO_NARRATIVES["incident_storm"],
        "prompts": SCENARIO_PROMPTS["incident_storm"],
        "task_mix": [
            {"task_type": "classification", "weight": 25, "token_range": [500, 3000], "priority": "normal"},
            {"task_type": "embedding", "weight": 15, "token_range": [1000, 6000], "priority": "normal"},
            {"task_type": "rerank", "weight": 10, "token_range": [2000, 6000], "priority": "normal"},
            {"task_type": "short_summary", "weight": 15, "token_range": [2000, 12000], "priority": "high"},
            {"task_type": "long_summary", "weight": 10, "token_range": [16000, 32000], "priority": "high"},
            {"task_type": "incident_rca", "weight": 15, "token_range": [20000, 40000], "priority": "critical"},
            {"task_type": "batch_summary", "weight": 10, "token_range": [32000, 50000], "priority": "critical"},
        ],
    },
    "rag_barrage": {
        "description": "Simulate high-throughput RAG — embed, search, rerank, answer generation.",
        "expected_lane_bias": {"performance": "retrieval-side inference", "overdrive": "answer generation"},
        "narrative": SCENARIO_NARRATIVES["rag_barrage"],
        "prompts": SCENARIO_PROMPTS["rag_barrage"],
        "task_mix": [
            {"task_type": "embedding", "weight": 30, "token_range": [500, 4000], "priority": "normal"},
            {"task_type": "rerank", "weight": 25, "token_range": [1000, 6000], "priority": "normal"},
            {"task_type": "rag_question", "weight": 25, "token_range": [2000, 20000], "priority": "high"},
            {"task_type": "document_summary", "weight": 20, "token_range": [16000, 40000], "priority": "high"},
        ],
    },
    "token_cannon": {
        "description": "Maximize generated-token simulation — heavy generation across all lanes.",
        "expected_lane_bias": {"overdrive": "most heavy requests"},
        "narrative": SCENARIO_NARRATIVES["token_cannon"],
        "prompts": SCENARIO_PROMPTS["token_cannon"],
        "task_mix": [
            {"task_type": "long_summary", "weight": 30, "token_range": [16000, 50000], "priority": "high"},
            {"task_type": "batch_summary", "weight": 25, "token_range": [32000, 60000], "priority": "critical"},
            {"task_type": "document_summary", "weight": 25, "token_range": [20000, 45000], "priority": "high"},
            {"task_type": "code_summary", "weight": 20, "token_range": [16000, 40000], "priority": "high"},
        ],
    },
    "model_race": {
        "description": "Run comparable workloads across all lanes for cross-hardware comparison.",
        "expected_lane_bias": {"eco": "small tasks", "performance": "mid tasks", "overdrive": "large tasks"},
        "narrative": SCENARIO_NARRATIVES["model_race"],
        "prompts": SCENARIO_PROMPTS["model_race"],
        "task_mix": [
            {"task_type": "classification", "weight": 25, "token_range": [500, 3000], "priority": "normal"},
            {"task_type": "short_summary", "weight": 25, "token_range": [2000, 12000], "priority": "normal"},
            {"task_type": "long_summary", "weight": 25, "token_range": [16000, 32000], "priority": "high"},
            {"task_type": "document_summary", "weight": 25, "token_range": [20000, 40000], "priority": "high"},
        ],
    },
}


def list_profiles() -> list[dict]:
    return [{"name": name, "description": p["description"]} for name, p in PROFILES.items()]
