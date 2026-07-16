"""Layer 7: BDD — Chat User Flow Scenarios

Given/When/Then scenarios covering the user-facing chat experience
with different routing strategies, model overrides, RAG, and hardware.
"""

import pytest
from inference_testbed.sse_parser import parse_sse, get_events_by_type, get_token_text
from inference_testbed.conftest import send_chat_message


class TestStandardRoutingScenario:
    """
    Scenario: User sends a message with standard routing
    Given standard routing strategy
    When user sends a general question
    Then granite-2b-cpu responds with non-empty content
    """

    def test_standard_routes_to_default_model(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id, "What is Intel AMX?",
            routing_strategy="standard",
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1
        assert decisions[0]["data"]["model"] == "granite-2b-cpu"

    def test_standard_returns_non_empty_content(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id, "What is Intel AMX?",
            routing_strategy="standard",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert len(content.strip()) > 0
        assert "No response generated" not in content


class TestSemanticRoutingScenario:
    """
    Scenario: Semantic routing matches department-specific questions
    Given semantic routing strategy
    When user sends an HR question
    Then routes to granite-2b-cpu via HR department
    """

    def test_semantic_hr_routes_correctly(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "What is the PTO policy for new employees?",
            routing_strategy="semantic",
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1
        reason = decisions[0]["data"].get("reason", "")
        assert "Semantic" in reason or "semantic" in reason

    def test_semantic_engineering_routes_to_qwen(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "Debug the Kubernetes API error in the deployment pipeline",
            routing_strategy="semantic",
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1
        assert decisions[0]["data"]["model"] == "qwen3-14b"


class TestModelOverrideScenario:
    """
    Scenario: Model override bypasses routing
    Given a specific model override
    When user sends any message
    Then that exact model is used regardless of strategy
    """

    def test_model_override_bypasses_routing(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id, "Hello",
            model_override="granite-2b-cpu",
            routing_strategy="semantic",
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1
        assert decisions[0]["data"]["model"] == "granite-2b-cpu"
        assert "override" in decisions[0]["data"].get("reason", "").lower()


class TestHardwareOverrideScenario:
    """
    Scenario: Hardware override forces backend selection
    Given hardware forced to xeon6
    When user sends a message
    Then xeon6 backend is used
    """

    def test_xeon6_override(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id, "Hello",
            hardware_override="xeon6",
        )
        events = parse_sse(resp.text)
        decisions = get_events_by_type(events, "routing_decision")
        assert len(decisions) == 1
        assert decisions[0]["data"]["hardware"] == "xeon6"


class TestRAGScenario:
    """
    Scenario: RAG-augmented chat with uploaded documents
    Given a document has been uploaded
    When user asks about document content
    Then response is generated (not empty)
    """

    def test_rag_with_doc_returns_content(self, gateway_client, session_with_doc):
        resp = send_chat_message(
            gateway_client, session_with_doc,
            "What is AMX acceleration?",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert len(content.strip()) > 0

    def test_no_doc_still_returns_content(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "What is a transformer model?",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert len(content.strip()) > 0
        assert "No response generated" not in content


class TestVLLMSRFallbackScenario:
    """
    Scenario: vLLM SR falls back when service is unreachable
    Given vllm-sr routing strategy
    When the vLLM SR service is down
    Then falls back to rule-based routing and still responds
    """

    def test_vllm_sr_fallback_returns_content(self, gateway_client, session_id):
        resp = send_chat_message(
            gateway_client, session_id,
            "What is the PTO policy?",
            routing_strategy="vllm-sr",
        )
        events = parse_sse(resp.text)
        content = get_token_text(events)
        assert len(content.strip()) > 0
