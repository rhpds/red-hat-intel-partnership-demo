"""Layer 2: CDD — Route Endpoint Contract Validation

Every task type via POST /v1/route must return a valid response
with correct routing metadata and task-appropriate result structure.
"""

import pytest

TASK_PAYLOADS = {
    "embeddings": {"task": "embeddings", "text": "What is AMX?"},
    "classification": {"task": "classification", "text": "Server CPU at 95%", "model": "granite-2b-cpu"},
    "reranking": {
        "task": "reranking",
        "text": "What is vLLM?",
        "texts": ["vLLM uses PagedAttention", "OpenVINO optimizes inference", "Kubernetes orchestrates"],
        "model": "granite-2b-cpu",
    },
    "completion": {"task": "completion", "prompt": "Explain Gaudi architecture", "model": "granite-2b-cpu", "max_tokens": 64},
    "batch_generation": {"task": "batch_generation", "prompt": "Summarize AI inference", "model": "granite-2b-cpu", "max_tokens": 64},
    "search": {"task": "search", "prompt": "What is vLLM?"},
    "governance": {"task": "governance", "prompt": "Delete production database", "model": "granite-2b-cpu"},
    "policy": {"task": "policy", "prompt": "Restart production pods", "model": "granite-2b-cpu"},
}


class TestRouteContractMetadata:
    """Every route response must include valid routing metadata."""

    @pytest.mark.parametrize("task", TASK_PAYLOADS.keys())
    def test_route_returns_200(self, gateway_client, task):
        payload = TASK_PAYLOADS[task]
        resp = gateway_client.post("/v1/route", json=payload)
        assert resp.status_code == 200, f"Task {task} returned {resp.status_code}: {resp.text[:200]}"

    @pytest.mark.parametrize("task", TASK_PAYLOADS.keys())
    def test_route_has_routing_metadata(self, gateway_client, task):
        payload = TASK_PAYLOADS[task]
        resp = gateway_client.post("/v1/route", json=payload)
        data = resp.json()
        routing = data.get("routing", {})
        assert "selected_backend" in routing, f"Missing selected_backend for {task}"
        assert "task" in routing, f"Missing task in routing for {task}"
        assert routing["task"] == task
        assert "reason" in routing, f"Missing reason for {task}"
        assert isinstance(routing.get("latency_ms", 0), (int, float))

    @pytest.mark.parametrize("task", TASK_PAYLOADS.keys())
    def test_route_result_not_none(self, gateway_client, task):
        payload = TASK_PAYLOADS[task]
        resp = gateway_client.post("/v1/route", json=payload)
        data = resp.json()
        assert data.get("result") is not None, f"Task {task} returned null result"


class TestRouteContractResultSchemas:
    """Task-specific result structure validation."""

    def test_embeddings_result_has_vectors(self, gateway_client):
        resp = gateway_client.post("/v1/route", json=TASK_PAYLOADS["embeddings"])
        result = resp.json()["result"]
        assert "data" in result
        for item in result["data"]:
            assert "embedding" in item
            assert isinstance(item["embedding"], list)
            assert len(item["embedding"]) > 0

    def test_classification_result_has_predictions(self, gateway_client):
        resp = gateway_client.post("/v1/route", json=TASK_PAYLOADS["classification"])
        result = resp.json()["result"]
        assert "predictions" in result
        for pred in result["predictions"]:
            assert "label" in pred
            assert "score" in pred
            assert 0 <= pred["score"] <= 1

    def test_reranking_result_has_sorted_results(self, gateway_client):
        resp = gateway_client.post("/v1/route", json=TASK_PAYLOADS["reranking"])
        result = resp.json()["result"]
        assert "results" in result
        scores = [r["relevance_score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True), "Reranking results not sorted by score"

    def test_search_result_has_ranked_results(self, gateway_client):
        resp = gateway_client.post("/v1/route", json=TASK_PAYLOADS["search"])
        result = resp.json()["result"]
        assert "results" in result
        assert "query" in result

    def test_governance_result_has_risk_decision(self, gateway_client):
        resp = gateway_client.post("/v1/route", json=TASK_PAYLOADS["governance"])
        result = resp.json()["result"]
        assert "risk_level" in result
        assert "decision" in result
        assert result["risk_level"] in ("low", "medium", "high", "critical")
        assert result["decision"] in ("approve", "deny", "escalate")

    def test_policy_result_has_verdict(self, gateway_client):
        resp = gateway_client.post("/v1/route", json=TASK_PAYLOADS["policy"])
        result = resp.json()["result"]
        assert "verdict" in result
        assert "compliant" in result
        assert result["verdict"] in ("pass", "fail")


class TestRouteContractValidation:
    """Request validation — invalid inputs should be rejected."""

    def test_invalid_task_returns_400(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={"task": "nonexistent_task", "prompt": "test"})
        assert resp.status_code == 400

    def test_invalid_routing_strategy_returns_422(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "completion",
            "prompt": "test",
            "routing_strategy": "invalid_strategy",
        })
        assert resp.status_code == 422
