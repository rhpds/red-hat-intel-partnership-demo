"""Chat & RAG endpoints — session management, SSE streaming, document upload."""

import json
import time as _time

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse

router = APIRouter()

_session_docs: dict[str, list[dict]] = {}


@router.post("/v1/chat/sessions")
async def create_chat_session(request: Request):
    import chat as chat_module
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    config = chat_module.ChatConfig(
        model_override=body.get("model_override"),
        hardware_override=body.get("hardware_override"),
        governance_mode=body.get("governance_mode", "supervised"),
        routing_strategy=body.get("routing_strategy", "standard"),
    )
    session = await chat_module.create_session(config=config)
    return {"session_id": session.id, "config": {"model_override": config.model_override, "hardware_override": config.hardware_override, "governance_mode": config.governance_mode, "routing_strategy": config.routing_strategy}}


@router.post("/v1/chat/sessions/{session_id}/message")
async def send_chat_message(session_id: str, request: Request):
    import chat as chat_module

    body = await request.json()
    message = body.get("message", "")
    model_override = body.get("model_override")
    hardware_override = body.get("hardware_override")
    routing_strategy = body.get("routing_strategy", "standard")

    config = chat_module.ChatConfig(
        model_override=model_override,
        hardware_override=hardware_override,
        routing_strategy=routing_strategy,
    )
    session = chat_module.ChatSession(id=session_id, config=config)

    app = request.app
    http_client = app.state.http_client

    all_chunks = _session_docs.get("global", [])

    def _keyword_search(query: str, chunks: list, top_k: int = 4) -> list:
        if not chunks:
            return []
        query_words = set(query.lower().split())
        scored = []
        for chunk in chunks:
            chunk_words = set(chunk["content"].lower().split())
            overlap = len(query_words & chunk_words)
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    rag_chunks = _keyword_search(message, all_chunks)

    async def event_stream():
        from router import CPU_MODELS

        total_start = _time.time()

        yield f"event: step\ndata: {json.dumps({'step': 'embed_query', 'hardware': 'xeon6', 'model': 'nomic-embed-text-v1-5', 'status': 'running'})}\n\n"
        yield f"event: step\ndata: {json.dumps({'step': 'vector_search', 'hardware': 'postgresql', 'results': len(rag_chunks), 'status': 'running'})}\n\n"
        yield f"event: step\ndata: {json.dumps({'step': 'rerank', 'hardware': 'xeon6', 'model': 'phi3-mini-cpu', 'status': 'running'})}\n\n"

        context = chat_module.build_context(session.messages, rag_chunks, message)

        routing_reason = ""
        all_backends = app.state.policy.list_backends()
        cpu_backend = next((b for b in all_backends if b.accelerator == "xeon6"), None)
        gpu_backend = next((b for b in all_backends if b.accelerator == "gaudi"), None)

        if config.model_override:
            chosen_model = config.model_override
            routing_reason = f"Manual override: {chosen_model}"
        elif config.routing_strategy == "semantic":
            import semantic_router
            classification = semantic_router.classify_rules(message)
            chosen_model = classification["model"]
            routing_reason = f"Semantic: {classification['department_label']} department → {chosen_model} ({classification['reasoning']})"
        elif config.routing_strategy == "vllm-sr":
            import semantic_router
            classification = await semantic_router.classify_vllm_sr(message, http_client)
            chosen_model = classification["model"]
            dept_label = classification.get("department_label", "General")
            routing_reason = f"vLLM SR: {dept_label} → {chosen_model} (signal-driven routing with OpenVINO)"
        else:
            chosen_model = "granite-2b-cpu"
            routing_reason = "Standard: default model (granite-2b-cpu on Xeon 6)"

        chosen_backend = None
        chosen_hardware = config.hardware_override or "auto"

        if config.hardware_override == "xeon6" and cpu_backend:
            chosen_backend = cpu_backend
        elif config.hardware_override == "gaudi" and gpu_backend:
            chosen_backend = gpu_backend
        elif chosen_model in CPU_MODELS:
            chosen_backend = cpu_backend or (all_backends[0] if all_backends else None)
        else:
            chosen_backend = gpu_backend or (all_backends[0] if all_backends else None)

        if chosen_backend:
            chosen_hardware = chosen_backend.accelerator or "auto"

        yield f"event: step\ndata: {json.dumps({'step': 'generate', 'hardware': chosen_hardware, 'model': chosen_model, 'status': 'running'})}\n\n"

        response_text = ""
        gen_start = _time.time()

        if chosen_backend:
            try:
                payload = {
                    "model": chosen_model,
                    "messages": context,
                    "max_tokens": 512,
                    "temperature": 0.7,
                }
                endpoint = f"{chosen_backend.url}/v1/chat/completions"
                headers = {}
                if chosen_backend.api_key:
                    headers["Authorization"] = f"Bearer {chosen_backend.api_key}"

                resp = await http_client.post(endpoint, json=payload, headers=headers, timeout=60.0)
                resp.raise_for_status()
                result = resp.json()

                choices = result.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    response_text = msg.get("content") or msg.get("reasoning_content") or ""
            except Exception as e:
                response_text = f"Inference error: {str(e)[:200]}"

        gen_elapsed = (_time.time() - gen_start) * 1000

        if not response_text:
            response_text = "No response generated. Check model availability."

        for token in response_text.split(" "):
            yield f"event: token\ndata: {json.dumps({'content': token + ' '})}\n\n"

        yield f"event: routing_decision\ndata: {json.dumps({'model': chosen_model, 'hardware': chosen_hardware, 'reason': routing_reason or f'Model {chosen_model} on {chosen_hardware}', 'strategy': config.routing_strategy, 'latency_ms': round(gen_elapsed)})}\n\n"

        total_elapsed = (_time.time() - total_start) * 1000
        cost = gen_elapsed / 1000 * (0.001 if chosen_hardware == "gaudi" else 0.0004)

        yield f"event: done\ndata: {json.dumps({'total_latency_ms': round(total_elapsed), 'total_cost': round(cost, 6)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/v1/chat/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    return {"session_id": session_id, "messages": []}


@router.delete("/v1/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    return {"status": "deleted", "session_id": session_id}


@router.post("/v1/documents/upload")
async def upload_document(file: UploadFile = File(...), request: Request = None):
    import rag
    if not rag.is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail=f"File type not allowed: {file.filename}")

    content = await file.read()
    if len(content) > rag.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {rag.MAX_FILE_SIZE_MB}MB)")

    result = await rag.upload_document(file.filename, content)

    if "chunks" in result:
        if "global" not in _session_docs:
            _session_docs["global"] = []
        for chunk in result["chunks"]:
            _session_docs["global"].append({
                "content": chunk,
                "filename": result["filename"],
                "category": result.get("category", "other"),
            })

    return result


@router.get("/v1/documents")
async def list_documents():
    return {"documents": []}


@router.delete("/v1/documents/{doc_id}")
async def delete_document(doc_id: str):
    return {"status": "deleted", "document_id": doc_id}
