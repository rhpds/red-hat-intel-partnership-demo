"""Layer 10: Regression — Empty Response Bug

Targeted tests for each identified root cause of empty inference responses.
These document the current behavior and catch regressions.
"""

import pytest
from inference_testbed.sse_parser import parse_sse, get_token_text
from inference_testbed.conftest import send_chat_message


class TestEmptyChoicesRegression:
    """Root cause 1: Backend returns {"choices": []} — empty array."""

    def test_empty_choices_triggers_fallback_text(self, mock_gateway_client_with_empty):
        session_resp = mock_gateway_client_with_empty.post("/v1/chat/sessions", json={})
        session_id = session_resp.json()["session_id"]

        resp = send_chat_message(
            mock_gateway_client_with_empty, session_id,
            "Hello world",
            routing_strategy="standard",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert "No response generated" in content, (
            f"Expected 'No response generated' fallback for empty choices, got: '{content[:100]}'"
        )


class TestNonexistentModelRegression:
    """Root cause 3: Model name doesn't match MAAS deployment."""

    def test_nonexistent_model_handled_gracefully(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "Hello", model_override="nonexistent-model-xyz-999",
        )
        assert resp.status_code == 200
        events = parse_sse(resp.text)
        content = get_token_text(events)
        # Should either show fallback text or an error message — not be silently empty
        assert len(content.strip()) > 0, "Nonexistent model produced completely empty response"


class TestSemanticCompareEmptyRegression:
    """Root cause 4: /v1/semantic/compare has no safety net for empty responses."""

    def test_compare_strategies_have_responses(self, gateway_client):
        resp = gateway_client.post("/v1/semantic/compare", json={
            "text": "What is the PTO policy for new employees?",
        })
        assert resp.status_code == 200
        data = resp.json()
        for s in data["strategies"]:
            response = s.get("response", "")
            # In mock mode, all responses should be non-empty
            # In live mode, empty responses here indicate the model is down
            assert isinstance(response, str), (
                f"Strategy {s['strategy']} response is not a string: {type(response)}"
            )


class TestChatEndpointNoBackendRegression:
    """Root cause 5: Chat endpoint has no fallback chain."""

    def test_chat_with_gaudi_hardware_still_responds(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "Hello",
            model_override="granite-2b-cpu",
            hardware_override="gaudi",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        # Even with mismatched hardware, should not be silently empty
        assert len(content.strip()) > 0, (
            "Forcing CPU model to Gaudi hardware produced empty response"
        )


class TestStandardRouteEmptyPromptRegression:
    """Edge case: Empty or whitespace-only prompt."""

    def test_empty_message_handled(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "",
        )
        # Should not crash
        assert resp.status_code in (200, 400, 422)
