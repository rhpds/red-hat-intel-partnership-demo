"""Layer 9: CBT — Full Combination Matrix

Parametrized cartesian product: 5 models x 3 strategies x 2 RAG modes x 3 hardware = 90 tests.
Each combination sends a chat message and validates the SSE stream.
"""

import pytest
from inference_testbed.sse_parser import parse_sse, get_events_by_type, get_token_text
from inference_testbed.conftest import send_chat_message, CPU_MODELS

MODELS = [
    "granite-2b-cpu",
    "qwen3-14b",
    "deepseek-r1-distill-qwen-14b",
    "microsoft-phi-4",
    "llama-31-70b-cpu",
]

STRATEGIES = ["standard", "semantic", "vllm-sr"]

RAG_MODES = ["no_rag", "with_rag"]

HARDWARE = ["auto", "xeon6", "gaudi"]


def _combo_id(model, strategy, rag, hw):
    return f"{model}|{strategy}|{rag}|{hw}"


def _make_params():
    params = []
    for model in MODELS:
        for strategy in STRATEGIES:
            for rag in RAG_MODES:
                for hw in HARDWARE:
                    combo_id = _combo_id(model, strategy, rag, hw)
                    params.append(pytest.param(model, strategy, rag, hw, id=combo_id))
    return params


class TestCombinationMatrix:
    """Full cartesian product of model x strategy x RAG x hardware."""

    @pytest.mark.parametrize("model,strategy,rag,hw", _make_params())
    def test_combination_produces_valid_sse_stream(
        self, gateway_client, model, strategy, rag, hw,
    ):
        # Create session
        session_resp = gateway_client.post("/v1/chat/sessions", json={})
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session_id"]

        # Upload doc if RAG mode
        if rag == "with_rag":
            import io
            doc = io.BytesIO(b"Intel Xeon 6 AMX accelerates AI inference workloads.")
            upload_resp = gateway_client.post(
                "/v1/documents/upload",
                files={"file": ("test.txt", doc, "text/plain")},
            )
            assert upload_resp.status_code == 200

        # Send message with model override (bypasses strategy routing)
        resp = send_chat_message(
            gateway_client, session_id,
            "Explain Intel hardware for AI inference.",
            model_override=model,
            hardware_override=hw if hw != "auto" else None,
            routing_strategy=strategy,
        )
        assert resp.status_code == 200, (
            f"Combo {model}|{strategy}|{rag}|{hw} returned {resp.status_code}"
        )

        # Parse SSE stream
        events = parse_sse(resp.text)

        # Validate: must have at least one step event
        steps = get_events_by_type(events, "step")
        assert len(steps) >= 1, (
            f"Combo {model}|{strategy}|{rag}|{hw}: no step events"
        )

        # Validate: must have routing_decision
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1, (
            f"Combo {model}|{strategy}|{rag}|{hw}: "
            f"expected 1 routing_decision, got {len(decisions)}"
        )

        # Validate: routing_decision has the overridden model
        assert decisions[0]["data"]["model"] == model

        # Validate: must have done event
        done = get_events_by_type(events, "done")
        assert len(done) == 1, (
            f"Combo {model}|{strategy}|{rag}|{hw}: no done event"
        )

        # Validate: token content is non-empty (or is the fallback text)
        content = get_token_text(events)
        assert len(content.strip()) > 0, (
            f"Combo {model}|{strategy}|{rag}|{hw}: empty content"
        )
