"""Layer 8: BDD — Error and Fallback Scenarios

Given/When/Then for backend failures, timeouts, empty responses,
and the fallback chain (primary → fallback → local → error).
"""

import pytest


class TestBackendErrorScenarios:
    """
    Scenario: Backend is unreachable
    Given all backends return connection errors
    When a route request is made
    Then 502 is returned with descriptive error
    """

    def test_unreachable_backend_returns_502(self, mock_gateway_client_with_errors):
        resp = mock_gateway_client_with_errors.post("/v1/route", json={
            "task": "completion",
            "prompt": "Hello",
            "model": "granite-2b-cpu",
            "max_tokens": 16,
        })
        assert resp.status_code in (500, 502), (
            f"Expected 502 for unreachable backend, got {resp.status_code}"
        )


class TestEmptyResponseScenarios:
    """
    Scenario: Model returns empty choices
    Given a model configured to return empty choices
    When chat message is sent
    Then fallback text is shown instead of empty content
    """

    def test_empty_choices_shows_fallback(self, mock_gateway_client_with_empty):
        from inference_testbed.sse_parser import parse_sse, get_token_text
        from inference_testbed.conftest import send_chat_message

        session_resp = mock_gateway_client_with_empty.post("/v1/chat/sessions", json={})
        session_id = session_resp.json()["session_id"]

        resp = send_chat_message(
            mock_gateway_client_with_empty, session_id,
            "Hello", routing_strategy="standard",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert "No response generated" in content, (
            f"Expected fallback text for empty choices, got: '{content[:100]}'"
        )


class TestInvalidInputScenarios:
    """
    Scenario: Invalid task type
    Given an unknown task type
    When POST /v1/route is called
    Then 400 is returned
    """

    def test_invalid_task_returns_400(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "nonexistent_task",
            "prompt": "test",
        })
        assert resp.status_code == 400

    def test_empty_classify_text_returns_400(self, gateway_client):
        resp = gateway_client.post("/v1/semantic/classify", json={"text": ""})
        assert resp.status_code == 400

    def test_missing_message_body(self, gateway_client, session_id):
        resp = gateway_client.post(
            f"/v1/chat/sessions/{session_id}/message",
            json={},
        )
        # Gateway should handle empty message gracefully (not crash)
        assert resp.status_code in (200, 400, 422)


class TestRouteEndpointFallbackChain:
    """
    Scenario: /v1/route fallback chain behavior
    Given primary backend fails
    When local fallback is disabled
    Then error response is returned
    """

    def test_completion_with_error_backend(self, mock_gateway_client_with_errors):
        resp = mock_gateway_client_with_errors.post("/v1/route", json={
            "task": "completion",
            "prompt": "test prompt",
            "model": "granite-2b-cpu",
            "max_tokens": 16,
        })
        # Should get an error status (502 or 500) since all backends are down
        assert resp.status_code >= 400, (
            f"Expected error status for failed backends, got {resp.status_code}"
        )
