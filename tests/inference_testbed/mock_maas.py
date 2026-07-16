"""Deterministic fake MAAS backend for inference testing.

Returns canned OpenAI-format responses per model. Implemented as an httpx
transport so it intercepts at the HTTP layer — no new dependencies needed.
"""

import json
from typing import Optional

import httpx

MODEL_RESPONSES = {
    "granite-2b-cpu": "Granite 2B CPU inference: The Intel Xeon 6 processor with AMX extensions provides efficient AI workload processing.",
    "qwen3-14b": "Qwen3 14B analysis: This engineering task requires careful consideration of the distributed system architecture.",
    "deepseek-r1-distill-qwen-14b": "DeepSeek R1 legal analysis: The contract clause in Section 4.2 addresses liability limitations under GDPR.",
    "microsoft-phi-4": "Phi-4 security scan: CVE-2024-1234 affects the authentication module. Recommend patching to version 2.1.3.",
    "llama-31-70b-cpu": "Llama 3.1 70B strategic analysis: The competitive landscape shows opportunities in hybrid cloud AI inference.",
    "phi3-mini-cpu": "Phi-3 Mini reranking: Document relevance scored and ordered by semantic similarity.",
    "default": "Default model response: Request processed successfully on Intel hardware.",
}

REASONING_MODELS = {"deepseek-r1-distill-qwen-14b"}

EMBEDDING_DIM = 768


class MockMaasTransport(httpx.AsyncBaseTransport):
    def __init__(self, empty_models: Optional[set] = None, error_models: Optional[set] = None):
        self.empty_models = empty_models or set()
        self.error_models = error_models or set()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        body = json.loads(request.content) if request.content else {}

        if path.endswith("/v1/chat/completions"):
            return self._handle_chat(body)
        elif path.endswith("/v1/embeddings"):
            return self._handle_embeddings(body)
        elif path.endswith("/v1/completions"):
            return self._handle_completions(body)
        else:
            return httpx.Response(404, json={"error": f"Unknown path: {path}"})

    def _handle_chat(self, body: dict) -> httpx.Response:
        model = body.get("model", "default")

        if model in self.error_models:
            return httpx.Response(503, json={"error": f"Model {model} unavailable"})

        if model in self.empty_models:
            return httpx.Response(200, json={
                "choices": [],
                "model": model,
                "usage": {"prompt_tokens": 10, "completion_tokens": 0},
            })

        content = MODEL_RESPONSES.get(model, MODEL_RESPONSES["default"])
        if model in REASONING_MODELS:
            message = {"role": "assistant", "content": None, "reasoning_content": content}
        else:
            message = {"role": "assistant", "content": content}
        return httpx.Response(200, json={
            "id": "mock-completion-001",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 50, "completion_tokens": len(content.split())},
        })

    def _handle_completions(self, body: dict) -> httpx.Response:
        model = body.get("model", "default")
        content = MODEL_RESPONSES.get(model, MODEL_RESPONSES["default"])
        return httpx.Response(200, json={
            "id": "mock-completion-002",
            "object": "text_completion",
            "model": model,
            "choices": [{"text": content, "index": 0, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 50, "completion_tokens": len(content.split())},
        })

    def _handle_embeddings(self, body: dict) -> httpx.Response:
        inputs = body.get("input", [])
        if isinstance(inputs, str):
            inputs = [inputs]
        data = []
        for i, _ in enumerate(inputs):
            embedding = [0.01 * (i + 1)] * EMBEDDING_DIM
            data.append({"object": "embedding", "index": i, "embedding": embedding})
        return httpx.Response(200, json={
            "object": "list",
            "model": body.get("model", "nomic-embed-text-v1-5"),
            "data": data,
            "usage": {"prompt_tokens": len(inputs) * 10, "total_tokens": len(inputs) * 10},
        })


class TimeoutTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Mock timeout")


class ConnectErrorTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Mock connection refused")
