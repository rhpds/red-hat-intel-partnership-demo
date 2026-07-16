"""Layer 3: CDD — Chat SSE Stream Contract Validation

The chat endpoint must emit a well-formed SSE event stream with
step, token, routing_decision, and done events in the correct order.
"""

import pytest
from inference_testbed.sse_parser import parse_sse, get_events_by_type, get_token_text
from inference_testbed.conftest import send_chat_message, ROUTING_STRATEGIES


class TestChatSSEContract:
    """SSE stream must contain all required event types."""

    @pytest.mark.parametrize("strategy", ROUTING_STRATEGIES)
    def test_stream_has_step_events(self, gateway_client, session_id, strategy):
        resp = send_chat_message(
            gateway_client, session_id, "What is Intel AMX?",
            routing_strategy=strategy,
        )
        assert resp.status_code == 200
        events = parse_sse(resp.text)
        steps = get_events_by_type(events, "step")
        assert len(steps) >= 1, f"No step events in SSE stream for strategy={strategy}"

    @pytest.mark.parametrize("strategy", ROUTING_STRATEGIES)
    def test_stream_has_token_events(self, gateway_client, session_id, strategy):
        resp = send_chat_message(
            gateway_client, session_id, "What is Intel AMX?",
            routing_strategy=strategy,
        )
        events = parse_sse(resp.text)
        tokens = get_events_by_type(events, "token")
        assert len(tokens) >= 1, f"No token events for strategy={strategy}"

    @pytest.mark.parametrize("strategy", ROUTING_STRATEGIES)
    def test_stream_has_routing_decision(self, gateway_client, session_id, strategy):
        resp = send_chat_message(
            gateway_client, session_id, "What is Intel AMX?",
            routing_strategy=strategy,
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1, f"Expected 1 routing_decision, got {len(decisions)}"
        data = decisions[0]["data"]
        assert "model" in data, "routing_decision missing 'model'"
        assert "hardware" in data, "routing_decision missing 'hardware'"
        assert "reason" in data, "routing_decision missing 'reason'"

    @pytest.mark.parametrize("strategy", ROUTING_STRATEGIES)
    def test_stream_has_done_event(self, gateway_client, session_id, strategy):
        resp = send_chat_message(
            gateway_client, session_id, "What is Intel AMX?",
            routing_strategy=strategy,
        )
        events = parse_sse(resp.text)
        done = get_events_by_type(events, "done")
        assert len(done) == 1, f"Expected 1 done event, got {len(done)}"
        data = done[0]["data"]
        assert "total_latency_ms" in data
        assert data["total_latency_ms"] >= 0


class TestChatSSEContentContract:
    """Token content must be non-empty for valid model selections."""

    def test_default_model_returns_content(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id, "Hello, explain Intel Xeon 6 features.",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert len(content.strip()) > 0, "Default model returned empty content"
        assert "No response generated" not in content, (
            "Got fallback text instead of real inference"
        )

    def test_routing_decision_includes_strategy(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id, "test",
            routing_strategy="semantic",
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1
        assert decisions[0]["data"].get("strategy") == "semantic"
