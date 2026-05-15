#!/usr/bin/env python3
"""Agent Swarm — TDD Red Phase"""

import sys
import time
import pytest


@pytest.fixture(autouse=True)
def setup(project_root, monkeypatch):
    p = str(project_root / "gateway")
    if p not in sys.path:
        sys.path.insert(0, p)
    monkeypatch.setenv("LITELLM_API_BASE", "https://litellm-test.example.com")


class TestSwarmModels:

    def test_swarm_agent_has_fields(self):
        from overdrive.swarm import SwarmAgent
        a = SwarmAgent(id="a1", name="Triage", role="classify", hardware_lane="xeon_eco", task_type="classification")
        assert a.id == "a1"
        assert a.hardware_lane == "xeon_eco"

    def test_incident_swarm_has_5_agents(self):
        from overdrive.swarm import INCIDENT_SWARM
        assert len(INCIDENT_SWARM["agents"]) == 5

    def test_incident_swarm_has_3_waves(self):
        from overdrive.swarm import INCIDENT_SWARM
        assert len(INCIDENT_SWARM["waves"]) == 3

    def test_wave_1_has_3_parallel_agents(self):
        from overdrive.swarm import INCIDENT_SWARM
        assert len(INCIDENT_SWARM["waves"][0]["agents"]) == 3

    def test_wave_2_depends_on_wave_1(self):
        from overdrive.swarm import INCIDENT_SWARM
        assert INCIDENT_SWARM["waves"][1]["depends_on"] == 0


class TestSwarmHardware:

    def test_triage_on_xeon_eco(self):
        from overdrive.swarm import INCIDENT_SWARM
        agents = {a["id"]: a for a in INCIDENT_SWARM["agents"]}
        assert agents["triage"]["hardware_lane"] == "xeon_eco"

    def test_rca_on_gaudi(self):
        from overdrive.swarm import INCIDENT_SWARM
        agents = {a["id"]: a for a in INCIDENT_SWARM["agents"]}
        assert agents["rca"]["hardware_lane"] == "gaudi_overdrive"

    def test_reporter_on_gaudi(self):
        from overdrive.swarm import INCIDENT_SWARM
        agents = {a["id"]: a for a in INCIDENT_SWARM["agents"]}
        assert agents["reporter"]["hardware_lane"] == "gaudi_overdrive"


class TestSwarmExecution:

    def test_run_completes(self):
        from overdrive.swarm import run_swarm
        result = run_swarm("incident", seed=42)
        assert result["status"] == "completed"

    def test_all_agents_complete(self):
        from overdrive.swarm import run_swarm
        result = run_swarm("incident", seed=42)
        for agent_result in result["agent_results"]:
            assert agent_result["status"] == "done"

    def test_deterministic(self):
        from overdrive.swarm import run_swarm
        a = run_swarm("incident", seed=42)
        b = run_swarm("incident", seed=42)
        for ar, br in zip(a["agent_results"], b["agent_results"]):
            assert ar["output"] == br["output"]

    def test_has_timeline(self):
        from overdrive.swarm import run_swarm
        result = run_swarm("incident", seed=42)
        assert "timeline" in result
        assert len(result["timeline"]) >= 5

    def test_has_final_report(self):
        from overdrive.swarm import run_swarm
        result = run_swarm("incident", seed=42)
        assert "final_report" in result
        assert len(result["final_report"]) > 100


class TestSwarmAPI:

    def test_endpoint_exists(self):
        from fastapi.testclient import TestClient
        from router import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post("/v1/swarm/run", json={"scenario": "incident", "seed": 42})
            assert resp.status_code == 200
            assert "run_id" in resp.json()

    def test_status_endpoint(self):
        from fastapi.testclient import TestClient
        from router import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post("/v1/swarm/run", json={"scenario": "incident", "seed": 42})
            run_id = resp.json()["run_id"]
            time.sleep(1)
            status = client.get(f"/v1/swarm/status/{run_id}")
            assert status.status_code == 200


class TestFrontend:

    def test_page_exists(self, project_root):
        assert (project_root / "frontend" / "src" / "pages" / "SwarmDemo.tsx").exists()

    def test_route_exists(self, project_root):
        assert "/swarm" in (project_root / "frontend" / "src" / "App.tsx").read_text()

    def test_nav_exists(self, project_root):
        assert "/swarm" in (project_root / "frontend" / "src" / "components" / "AppLayout.tsx").read_text()

    def test_api_method(self, project_root):
        assert "swarm" in (project_root / "frontend" / "src" / "api" / "client.ts").read_text()
