"""Layer 6: EDD — Semantic Routing Example-Driven Tests

Each department has a canonical prompt. The rules strategy must route
to the correct department and model. Other strategies must return
valid department/model pairs.
"""

import sys
import pytest
from pathlib import Path
from inference_testbed.conftest import DEPT_PROMPTS, DEPT_MODELS, DEPARTMENTS


@pytest.fixture
def semantic_router(project_root):
    gw = str(project_root / "gateway")
    if gw not in sys.path:
        sys.path.insert(0, gw)
    try:
        import importlib
        import semantic_router as sr
        importlib.reload(sr)
        return sr
    except ImportError:
        pytest.skip("semantic_router not importable")
    finally:
        if gw in sys.path:
            sys.path.remove(gw)


class TestRulesStrategyExamples:
    """Rules-based routing must match canonical prompts to correct departments."""

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_rules_routes_to_correct_department(self, semantic_router, dept):
        prompt = DEPT_PROMPTS[dept]
        result = semantic_router.classify_rules(prompt)
        if dept == "general":
            assert result["department"] == "general"
        else:
            assert result["department"] == dept, (
                f"Prompt '{prompt[:50]}...' routed to {result['department']}, expected {dept}"
            )

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_rules_selects_correct_model(self, semantic_router, dept):
        prompt = DEPT_PROMPTS[dept]
        result = semantic_router.classify_rules(prompt)
        expected_model = DEPT_MODELS[dept]
        if dept != "general":
            assert result["model"] == expected_model, (
                f"Department {dept} mapped to {result['model']}, expected {expected_model}"
            )

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_rules_returns_valid_confidence(self, semantic_router, dept):
        prompt = DEPT_PROMPTS[dept]
        result = semantic_router.classify_rules(prompt)
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_rules_returns_routing_ms(self, semantic_router, dept):
        prompt = DEPT_PROMPTS[dept]
        result = semantic_router.classify_rules(prompt)
        assert isinstance(result["routing_ms"], (int, float))
        assert result["routing_ms"] >= 0


class TestClassifyAllExamples:
    """classify_all via /v1/semantic/classify returns valid results for each department."""

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_all_strategies_return_valid_department(self, gateway_client, dept):
        prompt = DEPT_PROMPTS[dept]
        resp = gateway_client.post("/v1/semantic/classify", json={"text": prompt})
        assert resp.status_code == 200
        data = resp.json()
        for s in data["strategies"]:
            assert s["department"] in set(DEPARTMENTS), (
                f"Strategy {s['strategy']} returned unknown department {s['department']}"
            )

    @pytest.mark.parametrize("dept", DEPARTMENTS)
    def test_all_strategies_return_valid_model(self, gateway_client, dept):
        prompt = DEPT_PROMPTS[dept]
        resp = gateway_client.post("/v1/semantic/classify", json={"text": prompt})
        data = resp.json()
        valid_models = set(DEPT_MODELS.values()) | {"auto"}
        for s in data["strategies"]:
            assert s["model"] in valid_models, (
                f"Strategy {s['strategy']} returned unknown model {s['model']}"
            )
