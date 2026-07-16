"""Layer 5: EDD — Route Endpoint Example-Driven Tests

Concrete input/output examples for governance, policy, classification,
search, embeddings, reranking, and completion tasks.
"""

import pytest


class TestGovernanceExamples:
    """Governance task returns correct risk assessment for known inputs."""

    def test_destructive_action_denied(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "governance",
            "prompt": "Delete production database",
            "model": "granite-2b-cpu",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert result["risk_level"] == "critical"
        assert result["decision"] == "deny"

    def test_read_action_approved(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "governance",
            "prompt": "Read the pod logs",
            "model": "granite-2b-cpu",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert result["risk_level"] == "low"
        assert result["decision"] == "approve"

    def test_production_restart_escalated(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "governance",
            "prompt": "Restart production pods",
            "model": "granite-2b-cpu",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert result["risk_level"] == "high"
        assert result["decision"] == "escalate"


class TestPolicyExamples:
    """Policy task validates compliance for known action types."""

    def test_destructive_action_fails(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "policy",
            "prompt": "Drop the users table in production",
            "model": "granite-2b-cpu",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert result["verdict"] == "fail"
        assert result["compliant"] is False
        assert len(result["violations"]) > 0

    def test_read_action_passes(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "policy",
            "prompt": "View pod status in staging",
            "model": "granite-2b-cpu",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert result["verdict"] == "pass"
        assert result["compliant"] is True


class TestEmbeddingsExamples:
    """Embeddings task returns correct-dimension vectors."""

    def test_single_text_embedding(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "embeddings",
            "text": "What is AMX acceleration?",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert len(result["data"]) == 1
        assert len(result["data"][0]["embedding"]) > 100

    def test_multiple_text_embeddings(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "embeddings",
            "texts": ["First text", "Second text", "Third text"],
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert len(result["data"]) == 3


class TestSearchExamples:
    """Search task returns ranked results."""

    def test_search_returns_ranked_results(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "search",
            "prompt": "What is vLLM PagedAttention?",
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert "results" in result
        assert len(result["results"]) > 0
        for r in result["results"]:
            assert "score" in r
            assert "text" in r


class TestCompletionExamples:
    """Completion task returns non-empty text."""

    def test_completion_returns_content(self, gateway_client):
        resp = gateway_client.post("/v1/route", json={
            "task": "completion",
            "prompt": "Explain the Intel Gaudi 3 architecture in one sentence.",
            "model": "granite-2b-cpu",
            "max_tokens": 64,
        })
        assert resp.status_code == 200
        result = resp.json()["result"]
        choices = result.get("choices", [])
        assert len(choices) > 0, "No choices in completion result"
        content = choices[0].get("message", {}).get("content", "") or choices[0].get("text", "")
        assert len(content.strip()) > 0, "Completion returned empty content"
