"""Layer 4: CDD — Semantic Routing Contract Validation

The classify and compare endpoints must return well-formed responses
with exactly 4 strategies, valid departments, and agreement metrics.
"""

import pytest
from inference_testbed.conftest import DEPT_PROMPTS, DEPARTMENTS


VALID_STRATEGIES = {"rules", "embedding", "llm", "vllm-sr"}
VALID_DEPARTMENTS = set(DEPARTMENTS)


class TestSemanticClassifyContract:
    """POST /v1/semantic/classify must return 4 strategy results."""

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_classify_returns_4_strategies(self, gateway_client, dept):
        prompt = DEPT_PROMPTS[dept]
        resp = gateway_client.post("/v1/semantic/classify", json={"text": prompt})
        assert resp.status_code == 200
        data = resp.json()
        strategies = data.get("strategies", [])
        assert len(strategies) == 4, f"Expected 4 strategies, got {len(strategies)}"

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_classify_strategy_fields(self, gateway_client, dept):
        prompt = DEPT_PROMPTS[dept]
        resp = gateway_client.post("/v1/semantic/classify", json={"text": prompt})
        data = resp.json()
        for s in data["strategies"]:
            assert s["strategy"] in VALID_STRATEGIES, f"Unknown strategy: {s['strategy']}"
            assert s["department"] in VALID_DEPARTMENTS, f"Unknown department: {s['department']}"
            assert "model" in s and len(s["model"]) > 0
            assert 0 <= s["confidence"] <= 1
            assert isinstance(s["routing_ms"], (int, float))

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_classify_agreement_field(self, gateway_client, dept):
        prompt = DEPT_PROMPTS[dept]
        resp = gateway_client.post("/v1/semantic/classify", json={"text": prompt})
        data = resp.json()
        assert "agreement" in data
        assert isinstance(data["agreement"], int)
        assert 1 <= data["agreement"] <= 4
        assert "all_agree" in data
        assert isinstance(data["all_agree"], bool)


class TestSemanticCompareContract:
    """POST /v1/semantic/compare must include inference responses."""

    def test_compare_returns_strategies_with_responses(self, gateway_client):
        resp = gateway_client.post("/v1/semantic/compare", json={
            "text": "What is the PTO policy?",
        })
        assert resp.status_code == 200
        data = resp.json()
        strategies = data.get("strategies", [])
        assert len(strategies) == 4
        for s in strategies:
            assert "response" in s, f"Strategy {s['strategy']} missing 'response'"
            assert "inference_ms" in s
            assert "total_ms" in s
            assert isinstance(s["inference_ms"], (int, float))

    def test_compare_validates_input(self, gateway_client):
        resp = gateway_client.post("/v1/semantic/compare", json={"text": ""})
        assert resp.status_code == 400
