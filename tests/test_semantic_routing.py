"""
Stage 15: Semantic Department Routing — EDD Red/Green Rubric Tests

Validates department taxonomy, 4 classification strategies, routing accuracy,
cost comparison, null safety, and model alignment across all components.
"""

import sys
import yaml
import pytest
from pathlib import Path


@pytest.fixture
def gateway_dir(project_root) -> Path:
    return project_root / "gateway"


@pytest.fixture
def departments(gateway_dir):
    with open(gateway_dir / "departments.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def overdrive_config(gateway_dir):
    with open(gateway_dir / "overdrive" / "config.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def semantic_router(gateway_dir):
    sys.path.insert(0, str(gateway_dir))
    try:
        import importlib
        import semantic_router as sr
        importlib.reload(sr)
        return sr
    finally:
        if str(gateway_dir) in sys.path:
            sys.path.remove(str(gateway_dir))


# =========================================================================
# Department Taxonomy
# =========================================================================

class TestDepartmentTaxonomy:

    def test_departments_yaml_exists(self, gateway_dir):
        assert (gateway_dir / "departments.yaml").exists()

    def test_has_six_plus_departments(self, departments):
        depts = departments.get("departments", {})
        assert len(depts) >= 6, f"Expected 6+ departments, got {len(depts)}"

    def test_each_dept_has_model(self, departments):
        for dept_id, dept in departments.get("departments", {}).items():
            assert "model" in dept, f"Department '{dept_id}' missing model"
            assert dept["model"], f"Department '{dept_id}' has empty model"

    def test_each_dept_has_keywords(self, departments):
        for dept_id, dept in departments.get("departments", {}).items():
            if dept_id == "general":
                continue
            keywords = dept.get("keywords", [])
            assert len(keywords) > 0, f"Department '{dept_id}' has no keywords"

    def test_each_dept_has_label(self, departments):
        for dept_id, dept in departments.get("departments", {}).items():
            assert "label" in dept, f"Department '{dept_id}' missing label"

    def test_has_opus_baseline(self, departments):
        baseline = departments.get("opus_baseline", {})
        assert "cost_per_m_input" in baseline
        assert "cost_per_m_output" in baseline


# =========================================================================
# Classification Strategies
# =========================================================================

class TestClassifyRules:

    def test_rules_returns_dict(self, semantic_router):
        result = semantic_router.classify_rules("What is the PTO policy?")
        assert isinstance(result, dict)

    def test_rules_has_required_fields(self, semantic_router):
        result = semantic_router.classify_rules("test query")
        for field in ("strategy", "department", "department_label", "model", "confidence", "routing_ms"):
            assert field in result, f"Missing field: {field}"

    def test_rules_strategy_is_rules(self, semantic_router):
        result = semantic_router.classify_rules("test")
        assert result["strategy"] == "rules"

    def test_rules_routes_hr(self, semantic_router):
        result = semantic_router.classify_rules("What is the PTO policy?")
        assert result["department"] == "hr"
        assert result["model"] == "granite-2b-cpu"

    def test_rules_routes_engineering(self, semantic_router):
        result = semantic_router.classify_rules("Debug the Kafka consumer error")
        assert result["department"] == "engineering"
        assert result["model"] == "qwen3-14b"

    def test_rules_routes_legal(self, semantic_router):
        result = semantic_router.classify_rules("Review the contract for compliance issues")
        assert result["department"] == "legal"

    def test_rules_routes_finance(self, semantic_router):
        result = semantic_router.classify_rules("What is the quarterly revenue forecast?")
        assert result["department"] == "finance"

    def test_rules_routes_security(self, semantic_router):
        result = semantic_router.classify_rules("Check for CVE vulnerabilities in our firewall")
        assert result["department"] == "security"

    def test_rules_routes_executive(self, semantic_router):
        result = semantic_router.classify_rules("What is our competitive strategy roadmap?")
        assert result["department"] == "executive"

    def test_rules_fallback_to_general(self, semantic_router):
        result = semantic_router.classify_rules("Tell me a joke about cats")
        assert result["department"] == "general"

    def test_rules_sub_millisecond(self, semantic_router):
        result = semantic_router.classify_rules("test classification speed")
        assert result["routing_ms"] < 5, f"Rules should be fast, got {result['routing_ms']}ms"


class TestFallbackResult:

    def test_fallback_returns_general(self, semantic_router):
        result = semantic_router._fallback_result("test", 0.001)
        assert result["department"] == "general"
        assert result["confidence"] == 0.0
        assert result["strategy"] == "test"


# =========================================================================
# Cost Comparison
# =========================================================================

class TestCostComparison:

    def test_annual_savings_returns_dict(self, semantic_router):
        result = semantic_router.calculate_annual_savings("hr")
        assert isinstance(result, dict)

    def test_annual_savings_has_fields(self, semantic_router):
        result = semantic_router.calculate_annual_savings("engineering")
        for field in ("department", "model", "daily_cost", "opus_daily_cost", "annual_savings"):
            assert field in result, f"Missing field: {field}"

    def test_opus_costs_more(self, semantic_router):
        result = semantic_router.calculate_annual_savings("hr")
        assert result["opus_daily_cost"] > result["daily_cost"]
        assert result["annual_savings"] > 0


# =========================================================================
# Null Safety
# =========================================================================

class TestNullSafety:

    def test_fallback_on_none_backend(self, semantic_router):
        result = semantic_router._fallback_result("embedding", 0.001)
        assert result["department"] == "general"
        assert result["model"] == "granite-3-2-8b-instruct"

    def test_model_to_dept_populated(self, semantic_router):
        mapping = semantic_router._MODEL_TO_DEPT
        assert len(mapping) >= 5, f"Expected 5+ model-to-dept entries, got {len(mapping)}"
        assert "granite-2b-cpu" in mapping
        assert "granite-3-2-8b-instruct" in mapping


# =========================================================================
# Model Alignment
# =========================================================================

class TestModelAlignment:

    def test_overdrive_config_models(self, overdrive_config):
        lanes = overdrive_config.get("lanes", {})
        assert lanes["eco"]["model"] == "granite-2b-cpu"
        assert lanes["performance"]["model"] == "phi3-mini-cpu"
        assert lanes["overdrive"]["model"] == "deepseek-r1-distill-qwen-14b"

    def test_router_model_map_matches(self, gateway_dir):
        content = (gateway_dir / "router.py").read_text()
        assert '"eco": "granite-2b-cpu"' in content
        assert '"performance": "phi3-mini-cpu"' in content
        assert '"overdrive": "deepseek-r1-distill-qwen-14b"' in content

    def test_timing_provider_uses_correct_models(self, gateway_dir):
        sys.path.insert(0, str(gateway_dir))
        try:
            from overdrive.timing_provider import TASK_TO_LITELLM_MODEL
            assert TASK_TO_LITELLM_MODEL["classification"] == "granite-2b-cpu"
            assert TASK_TO_LITELLM_MODEL["rerank"] == "phi3-mini-cpu"
            assert TASK_TO_LITELLM_MODEL["incident_rca"] == "deepseek-r1-distill-qwen-14b"
        finally:
            if str(gateway_dir) in sys.path:
                sys.path.remove(str(gateway_dir))

    def test_frontend_overdrive_uses_correct_models(self, project_root):
        content = (project_root / "frontend" / "src" / "pages" / "Overdrive.tsx").read_text()
        assert "granite-2b-cpu" in content
        assert "phi3-mini-cpu" in content
        assert "deepseek-r1-distill-qwen-14b" in content

    def test_no_old_model_names_in_frontend(self, project_root):
        frontend_src = project_root / "frontend" / "src"
        for f in frontend_src.rglob("*.tsx"):
            content = f.read_text()
            assert "granite-4-0-h-tiny" not in content, f"Old model name in {f.name}"
            assert "codellama-7b-instruct" not in content, f"Old model name in {f.name}"

    def test_no_old_model_names_in_gateway(self, gateway_dir):
        for f in gateway_dir.rglob("*.py"):
            if "__pycache__" in str(f):
                continue
            content = f.read_text()
            assert "granite-4-0-h-tiny" not in content, f"Old model name in {f.name}"
            assert "codellama-7b-instruct" not in content, f"Old model name in {f.name}"

    def test_tokenizer_models_match(self, gateway_dir):
        content = (gateway_dir / "router.py").read_text()
        assert '"granite-2b-cpu":' in content
        assert '"phi3-mini-cpu":' in content
        assert '"deepseek-r1-distill-qwen-14b":' in content
