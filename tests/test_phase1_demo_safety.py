#!/usr/bin/env python3
"""
Phase 1 — Demo Safety Tests

Validates memory leak fix (run dict cleanup) and constant consolidation
in gateway/router.py.
"""

import ast
import pytest
from pathlib import Path


@pytest.fixture
def gateway_dir(project_root) -> Path:
    return project_root / "gateway"


@pytest.fixture
def router_source(gateway_dir):
    return (gateway_dir / "router.py").read_text()


@pytest.fixture
def router_ast(router_source):
    return ast.parse(router_source)


class TestConsolidatedConstants:

    def test_cpu_models_is_module_level(self, router_ast):
        names = [n.targets[0].id for n in ast.walk(router_ast)
                 if isinstance(n, ast.Assign) and n.targets and isinstance(n.targets[0], ast.Name)]
        assert "CPU_MODELS" in names

    def test_cpu_models_has_four_entries(self, router_source):
        assert "granite-2b-cpu" in router_source
        assert "phi3-mini-cpu" in router_source
        assert "qwen25-3b-cpu" in router_source
        assert "llama-31-70b-cpu" in router_source

    def test_lane_model_map_is_module_level(self, router_ast):
        names = [n.targets[0].id for n in ast.walk(router_ast)
                 if isinstance(n, ast.Assign) and n.targets and isinstance(n.targets[0], ast.Name)]
        assert "LANE_MODEL_MAP" in names

    def test_lane_model_map_covers_three_lanes(self, router_source):
        idx = router_source.find("LANE_MODEL_MAP")
        section = router_source[idx:idx + 200]
        for lane in ("eco", "performance", "overdrive"):
            assert lane in section

    def test_risk_score_map_is_module_level(self, router_ast):
        names = [n.targets[0].id for n in ast.walk(router_ast)
                 if isinstance(n, ast.Assign) and n.targets and isinstance(n.targets[0], ast.Name)]
        assert "RISK_SCORE_MAP" in names

    def test_risk_score_map_has_all_levels(self, router_source):
        idx = router_source.find("RISK_SCORE_MAP")
        section = router_source[idx:idx + 200]
        for level in ("low", "medium", "high", "critical", "pass", "fail"):
            assert f'"{level}"' in section

    def test_no_inline_cpu_models_set(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        count = source.count('cpu_models = {')
        assert count == 0, f"Found {count} inline cpu_models definitions — should use CPU_MODELS constant"

    def test_no_inline_model_map_dict(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        count = source.count('model_map = {')
        assert count == 0, f"Found {count} inline model_map definitions — should use LANE_MODEL_MAP constant"

    def test_no_inline_risk_score_dict(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        count = source.count('risk_score = {')
        assert count == 0, f"Found {count} inline risk_score definitions — should use RISK_SCORE_MAP constant"


class TestRunDictCleanup:

    def test_all_run_dicts_declared_together(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        lines = source.splitlines()
        decl_lines = [i for i, l in enumerate(lines)
                      if l.strip().startswith(("_workload_runs:", "_agent_runs:", "_training_runs:", "_swarm_runs:"))]
        assert len(decl_lines) == 4, f"Expected 4 run dict declarations, found {len(decl_lines)}"
        spread = max(decl_lines) - min(decl_lines)
        assert spread <= 5, f"Run dict declarations spread across {spread} lines — should be co-located"

    def test_cleanup_references_all_stores(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        cleanup_start = source.find("def _cleanup_old_runs")
        assert cleanup_start != -1, "_cleanup_old_runs function not found"
        next_def = source.find("\ndef ", cleanup_start + 1)
        cleanup_body = source[cleanup_start:next_def] if next_def != -1 else source[cleanup_start:]
        for name in ("_workload_runs", "_agent_runs", "_swarm_runs", "_training_runs"):
            assert name in cleanup_body, f"_cleanup_old_runs does not reference {name}"

    def test_agent_run_has_started_at(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        agent_section = source[source.find("agent_research"):]
        run_state_line = agent_section[:agent_section.find("_agent_runs[run_id]")]
        assert "started_at" in run_state_line, "Agent run_state missing started_at timestamp"

    def test_swarm_run_has_started_at(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        swarm_section = source[source.find("swarm_run"):]
        run_state_line = swarm_section[:swarm_section.find("_swarm_runs[run_id]")]
        assert "started_at" in run_state_line, "Swarm run_state missing started_at timestamp"

    def test_training_run_has_started_at(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        training_section = source[source.find("training_run"):]
        run_state_line = training_section[:training_section.find("_training_runs[run_id]")]
        assert "started_at" in run_state_line, "Training run_state missing started_at timestamp"

    def test_cleanup_only_removes_finished_runs(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        cleanup_start = source.find("def _cleanup_old_runs")
        next_def = source.find("\ndef ", cleanup_start + 1)
        cleanup_body = source[cleanup_start:next_def] if next_def != -1 else source[cleanup_start:]
        for status in ("complete", "completed", "error"):
            assert status in cleanup_body, f"Cleanup should check for '{status}' status before removing"

    def test_no_duplicate_run_dict_declarations(self, gateway_dir):
        source = (gateway_dir / "router.py").read_text()
        for name in ("_agent_runs: dict", "_training_runs: dict", "_swarm_runs: dict"):
            count = source.count(name)
            assert count == 1, f"Found {count} declarations of {name} — expected exactly 1"
