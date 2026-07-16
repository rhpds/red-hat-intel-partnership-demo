"""Layer 1: TDD — Model Availability

Every model in departments.yaml must return non-empty content.
These are the first tests to write (RED) and the first gate for arcade readiness.
"""

import pytest

CHAT_MODELS = [
    "granite-2b-cpu",
    "qwen3-14b",
    "deepseek-r1-distill-qwen-14b",
    "microsoft-phi-4",
    "llama-31-70b-cpu",
]


class TestModelAvailability:
    """TDD RED/GREEN: Each model returns a non-empty inference response."""

    @pytest.mark.parametrize("model", CHAT_MODELS)
    def test_chat_model_returns_content(self, gateway_client, session_id, model):
        from inference_testbed.conftest import send_chat_message
        from inference_testbed.sse_parser import parse_sse, get_token_text

        resp = send_chat_message(
            gateway_client, session_id, "Hello, what can you do?",
            model_override=model,
        )
        assert resp.status_code == 200, f"Model {model} returned {resp.status_code}"

        events = parse_sse(resp.text)
        content = get_token_text(events)

        # Content must not be empty
        assert len(content.strip()) > 0, (
            f"Model {model} returned empty content. "
            f"Events: {[e['event'] for e in events]}"
        )

        # "No response generated" means the model is unreachable or returning null content.
        # "Inference error" means the backend returned an HTTP error.
        # Both indicate the model is NOT working for the arcade demo.
        assert "No response generated" not in content, (
            f"Model {model} is not generating responses — likely not deployed "
            f"or returning null content (reasoning model without content field)"
        )
        assert "Inference error" not in content, (
            f"Model {model} returned an inference error: {content[:200]}"
        )

    def test_embedding_model_returns_vectors(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "embeddings",
            "text": "What is AMX acceleration?",
        })
        assert resp.status_code == 200
        data = resp.json()
        result = data.get("result", {})
        assert "data" in result, f"Embeddings response missing 'data': {result}"
        embeddings = result["data"]
        assert len(embeddings) > 0, "No embeddings returned"
        assert len(embeddings[0]["embedding"]) > 0, "Embedding vector is empty"
