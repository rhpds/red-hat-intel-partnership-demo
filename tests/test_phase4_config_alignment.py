#!/usr/bin/env python3
"""
Phase 4 — Config Alignment Tests

Validates that all config files use consistent model names, thresholds,
route types, and capabilities.
"""

import pytest
import yaml
from pathlib import Path




@pytest.fixture
def canonical_config(gateway_dir):
    with open(gateway_dir / "config.local.yaml") as f:
        return yaml.safe_load(f)


STALE_MODELS = {"granite-4-0-h-tiny", "codellama-7b-instruct", "granite-3-2-8b-instruct"}
REQUIRED_ROUTE_TASKS = {"embeddings", "classification", "search", "reranking", "completion", "batch_generation", "governance", "policy"}


class TestNoStaleModels:

    def _check_no_stale(self, text, filename):
        for model in STALE_MODELS:
            assert model not in text, f"{filename} references stale model '{model}'"

    def test_config_yaml(self, gateway_dir):
        self._check_no_stale((gateway_dir / "config.yaml").read_text(), "config.yaml")

    def test_config_local(self, gateway_dir):
        self._check_no_stale((gateway_dir / "config.local.yaml").read_text(), "config.local.yaml")

    def test_deploy_configmap(self, project_root):
        self._check_no_stale((project_root / "deploy" / "cluster" / "configmap.yaml").read_text(), "deploy configmap")

    def test_helm_configmap(self, project_root):
        self._check_no_stale((project_root / "helm" / "templates" / "gateway-configmap.yaml").read_text(), "helm configmap")


class TestRouteCompleteness:

    def _extract_routes(self, config):
        return {r["task"] for r in config.get("routes", [])}

    def test_canonical_has_all_routes(self, canonical_config):
        tasks = self._extract_routes(canonical_config)
        for t in REQUIRED_ROUTE_TASKS:
            assert t in tasks, f"Canonical config missing route for '{t}'"

    def test_deploy_configmap_has_all_routes(self, project_root):
        text = (project_root / "deploy" / "cluster" / "configmap.yaml").read_text()
        for t in REQUIRED_ROUTE_TASKS:
            assert f"task: {t}" in text, f"Deploy configmap missing route for '{t}'"

    def test_helm_configmap_has_all_routes(self, project_root):
        text = (project_root / "helm" / "templates" / "gateway-configmap.yaml").read_text()
        for t in REQUIRED_ROUTE_TASKS:
            assert f"task: {t}" in text, f"Helm configmap missing route for '{t}'"


class TestThresholdConsistency:

    def test_canonical_uses_4b_threshold(self, canonical_config):
        for route in canonical_config.get("routes", []):
            for cond in route.get("conditions", []):
                if cond.get("operator") == "<=":
                    assert cond["model_size_b"] == 4, f"Canonical config uses {cond['model_size_b']}B threshold, expected 4"

    def test_deploy_configmap_uses_4b_threshold(self, project_root):
        text = (project_root / "deploy" / "cluster" / "configmap.yaml").read_text()
        assert "model_size_b: 8" not in text, "Deploy configmap uses 8B threshold — should be 4"
        assert "model_size_b: 4" in text, "Deploy configmap missing 4B threshold"


class TestCapabilityConsistency:

    def test_cpu_backend_has_search(self, canonical_config):
        for backend in canonical_config.get("backends", []):
            if backend.get("accelerator") == "xeon6":
                assert "search" in backend.get("capabilities", []), "CPU backend missing 'search' capability"

    def test_deploy_cpu_has_search(self, project_root):
        text = (project_root / "deploy" / "cluster" / "configmap.yaml").read_text()
        assert "search" in text, "Deploy configmap CPU backend missing 'search' capability"

    def test_all_configs_use_same_backend_names(self, gateway_dir):
        configs = ["config.yaml", "config.local.yaml"]
        backend_names = {}
        for name in configs:
            with open(gateway_dir / name) as f:
                config = yaml.safe_load(f)
            names = {b["name"] for b in config.get("backends", [])}
            backend_names[name] = names
        local_names = backend_names["config.local.yaml"]
        for name, names in backend_names.items():
            if name == "config.local.yaml":
                continue
            if "maas-cpu" in names:
                continue  # config.yaml uses different naming convention (maas- prefix)
            assert names == local_names, f"{name} backend names {names} differ from canonical {local_names}"
