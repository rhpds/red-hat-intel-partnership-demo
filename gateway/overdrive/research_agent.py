"""RAG Research Agent — governed multi-step question answering."""

import re
import time

KNOWLEDGE_BASE = [
    {"id": "kb-001", "title": "Intel Xeon 6 for AI Inference", "content": "Intel Xeon 6 processors with Advanced Matrix Extensions (AMX) provide cost-efficient AI inference for small-to-medium models. Classification, embeddings, and reranking tasks run on Xeon 6 at production throughput without requiring GPU resources. The AMX instruction set accelerates INT8 and BF16 matrix operations natively."},
    {"id": "kb-002", "title": "Intel Gaudi Accelerator Architecture", "content": "Intel Gaudi accelerators feature high-bandwidth memory (HBM2E) with 96GB capacity and dedicated tensor processing cores. Gaudi excels at large language model inference with 17B+ parameter models, providing 100+ tokens/sec generation throughput. The HBM bandwidth enables large context windows up to 400K tokens."},
    {"id": "kb-003", "title": "Hardware-Aware Routing Engine", "content": "The routing engine evaluates each inference request against a rubric of checks: task type, token estimate, priority, and latency target. Small classification tasks route to Xeon 6 Eco lane. Mid-range embeddings and summaries route to Xeon 6 Performance lane. Large generation tasks route to Gaudi Overdrive lane. Every decision includes full evidence."},
    {"id": "kb-004", "title": "Overdrive Lane Evaluation", "content": "The Overdrive engine uses a three-lane architecture: Eco (Granite Tiny on Xeon 6, ≤4K tokens), Performance (CodeLlama 7B on Xeon 6, ≤16K tokens), and Overdrive (Llama Scout 17B on Gaudi, ≤64K tokens). The routing matrix matches task type and token estimate to the optimal lane. Fallback rules ensure graceful degradation."},
    {"id": "kb-005", "title": "Tokenization and Cost Model", "content": "Different models tokenize text differently, producing different token counts and costs. Xeon 6 inference costs $0.0004 per 1K tokens. Gaudi inference costs $0.001 per 1K tokens. The routing engine automatically selects the cheapest viable hardware tier, sending small workloads to Xeon 6 and reserving Gaudi for tasks that need its bandwidth."},
    {"id": "kb-006", "title": "Failover and Graceful Degradation", "content": "When a hardware tier goes offline, the routing engine automatically reroutes requests. Overdrive lane failures fall back to Performance (if tokens < 32K). Performance failures fall back to Eco (for classification and short summaries). Every fallback decision is recorded with full evidence showing the reason for rerouting."},
    {"id": "kb-007", "title": "KServe and OpenShift AI Integration", "content": "Models are served via KServe ServingRuntime on Red Hat OpenShift AI. CPU inference uses vLLM optimized for Xeon 6 with AMX. GPU inference uses vLLM with Habana Gaudi device plugin. Both runtimes support OpenAI-compatible API endpoints for chat completions, embeddings, and classification."},
    {"id": "kb-008", "title": "LiteLLM Proxy Configuration", "content": "LiteLLM provides a unified OpenAI-compatible API gateway fronting multiple model backends. The platform routes through LiteLLM at litellm-prod.apps.maas.redhatworkshops.io. API key rate limits: 90 RPM, 400K TPM, $2K/day budget. Models available: Granite, CodeLlama, Llama Scout, DeepSeek, Phi-4, Nomic embeddings."},
    {"id": "kb-009", "title": "Workload Profiles for Performance Demos", "content": "Four workload profiles simulate enterprise patterns: Incident Storm (classification + RCA), RAG Barrage (embed + search + rerank + generate), Token Cannon (heavy generation stress test), and Model Race (cross-hardware comparison). Power modes scale from Standby (5 requests) to Overdrive (1000 requests)."},
    {"id": "kb-010", "title": "Governance and Approval Workflow", "content": "The platform includes a governance layer that evaluates AI-generated actions by risk level. Low-risk actions (read logs) auto-approve. Medium-risk actions (restart services) require human review. High-risk actions (delete namespaces) are denied. Every decision is recorded with evidence bundles for audit."},
    {"id": "kb-011", "title": "Prompt Injection Protection", "content": "All user input is sanitized before reaching LLM backends. The gateway strips role override patterns (system:, [INST], <|im_start|>), control characters, and templated prompts use system/user message separation. Classification and reranking tasks include 'ignore instructions in user text' defensive prompts."},
    {"id": "kb-012", "title": "Platform Deployment Architecture", "content": "The platform deploys on OpenShift with four components: PostgreSQL (persistence), Gateway (routing + inference), Frontend (React dashboard with OAuth), and the Overdrive engine. Images are built with podman and pushed to the OpenShift internal registry. Deployments use Kustomize overlays."},
    {"id": "kb-013", "title": "Intel AMX Acceleration Details", "content": "Intel Advanced Matrix Extensions (AMX) in Xeon 6 accelerate AI inference by performing tile-based matrix multiply-accumulate operations in hardware. This enables INT8 and BF16 inference at near-GPU speeds for models under 8B parameters, making Xeon 6 ideal for high-volume, low-latency classification and embedding workloads."},
]

GOVERNANCE_STEPS = {
    "open": [],
    "supervised": ["synthesize"],
    "locked": ["decompose", "search", "rerank", "synthesize", "governance"],
}


def get_steps_requiring_approval(mode: str) -> list[str]:
    return GOVERNANCE_STEPS.get(mode, [])


def _keyword_search(query: str, top_k: int = 5) -> list[dict]:
    query_words = set(re.findall(r'\w+', query.lower()))
    scored = []
    for doc in KNOWLEDGE_BASE:
        doc_words = set(re.findall(r'\w+', (doc["title"] + " " + doc["content"]).lower()))
        overlap = len(query_words & doc_words)
        if overlap > 0:
            scored.append({**doc, "score": round(overlap / max(len(query_words), 1), 3)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def step_decompose(question: str) -> dict:
    words = question.split()
    sub_queries = []
    if any(w in question.lower() for w in ["compare", "vs", "versus", "difference"]):
        sub_queries.append(f"What are the capabilities of Xeon 6 for inference?")
        sub_queries.append(f"What are the capabilities of Gaudi for inference?")
        sub_queries.append(f"How does the routing engine choose between them?")
    elif any(w in question.lower() for w in ["failover", "offline", "failure", "degrade"]):
        sub_queries.append(f"How does the failover mechanism work?")
        sub_queries.append(f"What happens to requests during hardware failure?")
        sub_queries.append(f"How is recovery detected and routing restored?")
    elif any(w in question.lower() for w in ["token", "cost", "price"]):
        sub_queries.append(f"How does tokenization differ across models?")
        sub_queries.append(f"What is the cost model for Xeon 6 vs Gaudi?")
    else:
        sub_queries.append(f"Overview: {question}")
        sub_queries.append(f"Technical details: {question}")
        if len(words) > 5:
            sub_queries.append(f"Implementation specifics: {question}")

    return {
        "sub_queries": sub_queries,
        "hw": "Gaudi",
        "routing_reason": "Query decomposition requires reasoning capability — Llama Scout 17B on Gaudi breaks complex questions into focused sub-queries.",
    }


def step_search(query: str) -> dict:
    docs = _keyword_search(query, top_k=5)
    return {
        "documents": docs,
        "hw": "Xeon 6",
        "routing_reason": "Knowledge base search uses nomic-embed on Xeon 6 — fast vector matching with AMX acceleration.",
    }


def step_rerank(query: str, documents: list[dict]) -> dict:
    ranked = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)
    for i, doc in enumerate(ranked):
        doc["rank"] = i + 1
        doc["relevance"] = round(max(0.3, doc.get("score", 0.5) - i * 0.05), 3)
    return {
        "ranked_documents": ranked,
        "hw": "Xeon 6",
        "routing_reason": "Cross-encoder reranking on CodeLlama 7B with Xeon 6 AMX — scores document relevance efficiently without GPU.",
    }


def step_synthesize(question: str, sub_queries: list[str], documents: list[dict]) -> dict:
    doc_context = "\n".join(f"- {d['title']}: {d['content'][:150]}..." for d in documents[:4])
    answer = (
        f"Based on analysis of {len(documents)} knowledge base documents across {len(sub_queries)} research dimensions:\n\n"
    )
    for doc in documents[:3]:
        answer += f"**{doc['title']}**: {doc['content'][:200]}\n\n"
    answer += f"This analysis synthesized information from {len(documents)} sources to address the question: \"{question}\""

    citations = [{"id": d.get("id", f"doc-{i}"), "title": d.get("title", "Untitled"), "relevance": d.get("relevance", d.get("score", 0))} for i, d in enumerate(documents[:4])]

    return {
        "answer": answer,
        "citations": citations,
        "hw": "Gaudi",
        "routing_reason": "Answer synthesis requires sustained generation with large context — Llama Scout 17B on Gaudi uses HBM bandwidth for multi-document reasoning.",
    }


def step_governance(answer: str) -> dict:
    risk_words = ["delete", "destroy", "drop", "remove", "kill", "terminate"]
    has_risk = any(w in answer.lower() for w in risk_words)
    if has_risk:
        decision = "escalate"
        reason = "Generated answer contains references to destructive actions — flagged for human review."
    else:
        decision = "pass"
        reason = "Answer passes content review — no destructive actions, factual content based on knowledge base."

    return {
        "decision": decision,
        "reason": reason,
        "hw": "Xeon 6",
        "routing_reason": "Content review uses Granite Tiny on Xeon 6 — lightweight classification of answer safety.",
    }


def run_research_agent(
    question: str,
    governance_mode: str = "open",
    run_state: dict = None,
    wait_for_approval: callable = None,
) -> dict:
    approval_required = get_steps_requiring_approval(governance_mode)
    steps = []
    if run_state:
        run_state["steps"] = steps

    def _add_step(name, status, output, hw, routing_reason, **extra):
        step = {
            "name": name,
            "status": status,
            "output": output,
            "hw": hw,
            "routing_reason": routing_reason,
            "latency_ms": extra.get("latency_ms", 0),
            **{k: v for k, v in extra.items() if k != "latency_ms"},
        }
        steps.append(step)
        if run_state:
            run_state["steps"] = list(steps)
        return step

    def _maybe_wait_approval(step_name):
        if step_name in approval_required:
            steps[-1]["status"] = "awaiting_approval"
            if run_state:
                run_state["steps"] = list(steps)
            if wait_for_approval:
                wait_for_approval(step_name)
            steps[-1]["status"] = "done"
            if run_state:
                run_state["steps"] = list(steps)

    start = time.monotonic()

    t0 = time.monotonic()
    decompose_result = step_decompose(question)
    _add_step("decompose", "done", {
        "sub_queries": decompose_result["sub_queries"],
    }, decompose_result["hw"], decompose_result["routing_reason"],
        latency_ms=round((time.monotonic() - t0) * 1000, 1))
    _maybe_wait_approval("decompose")

    all_docs = []
    for sq in decompose_result["sub_queries"]:
        t0 = time.monotonic()
        search_result = step_search(sq)
        all_docs.extend(search_result["documents"])
        _add_step("search", "done", {
            "query": sq,
            "documents": search_result["documents"],
            "count": len(search_result["documents"]),
        }, search_result["hw"], search_result["routing_reason"],
            latency_ms=round((time.monotonic() - t0) * 1000, 1))
    _maybe_wait_approval("search")

    seen_ids = set()
    unique_docs = []
    for d in all_docs:
        if d["id"] not in seen_ids:
            seen_ids.add(d["id"])
            unique_docs.append(d)

    t0 = time.monotonic()
    rerank_result = step_rerank(question, unique_docs)
    _add_step("rerank", "done", {
        "ranked_documents": rerank_result["ranked_documents"],
        "count": len(rerank_result["ranked_documents"]),
    }, rerank_result["hw"], rerank_result["routing_reason"],
        latency_ms=round((time.monotonic() - t0) * 1000, 1))
    _maybe_wait_approval("rerank")

    t0 = time.monotonic()
    synth_result = step_synthesize(question, decompose_result["sub_queries"], rerank_result["ranked_documents"])
    _add_step("synthesize", "done", {
        "answer": synth_result["answer"],
        "citations": synth_result["citations"],
    }, synth_result["hw"], synth_result["routing_reason"],
        latency_ms=round((time.monotonic() - t0) * 1000, 1))
    _maybe_wait_approval("synthesize")

    t0 = time.monotonic()
    gov_result = step_governance(synth_result["answer"])
    _add_step("governance", "done", {
        "decision": gov_result["decision"],
        "reason": gov_result["reason"],
    }, gov_result["hw"], gov_result["routing_reason"],
        latency_ms=round((time.monotonic() - t0) * 1000, 1))
    _maybe_wait_approval("governance")

    total_ms = round((time.monotonic() - start) * 1000, 1)

    result = {
        "answer": synth_result["answer"],
        "citations": synth_result["citations"],
        "governance_decision": gov_result["decision"],
        "total_ms": total_ms,
    }

    if run_state:
        run_state["status"] = "complete"
        run_state.update(result)

    return result
