"""Shared fixtures for inference test bed.

Supports mock mode (CI, default) and live mode (pre-demo validation).
Set TESTBED_MODE=live and provide LITELLM_API_KEY to run against real MAAS.
"""

import os
import sys
import pytest
from pathlib import Path

TESTBED_MODE = os.getenv("TESTBED_MODE", "mock")

CHAT_MODELS = [
    "granite-2b-cpu",
    "qwen3-14b",
    "deepseek-r1-distill-qwen-14b",
    "microsoft-phi-4",
    "llama-31-70b-cpu",
]

EMBEDDING_MODELS = ["nomic-embed-text-v1-5"]

ALL_MODELS = CHAT_MODELS + EMBEDDING_MODELS

DEPARTMENTS = ["hr", "engineering", "legal", "finance", "security", "executive", "general"]

DEPT_MODELS = {
    "hr": "granite-2b-cpu",
    "engineering": "qwen3-14b",
    "legal": "deepseek-r1-distill-qwen-14b",
    "finance": "qwen3-14b",
    "security": "microsoft-phi-4",
    "executive": "llama-31-70b-cpu",
    "general": "granite-2b-cpu",
}

DEPT_PROMPTS = {
    "hr": "What is the PTO policy for new employees?",
    "engineering": "Debug the Kubernetes API error in the pipeline",
    "legal": "Review the contract for GDPR compliance",
    "finance": "What is the quarterly revenue forecast?",
    "security": "Check for CVE vulnerabilities in the firewall",
    "executive": "What is our competitive strategy roadmap?",
    "general": "Tell me a joke about cats",
}

ROUTING_STRATEGIES = ["standard", "semantic", "vllm-sr"]

TASK_TYPES = [
    "embeddings", "classification", "reranking", "completion",
    "batch_generation", "search", "governance", "policy",
]

CPU_MODELS = {"granite-2b-cpu", "phi3-mini-cpu", "qwen25-3b-cpu", "llama-31-70b-cpu"}


def pytest_configure(config):
    config.addinivalue_line("markers", "live: requires real MAAS backend")
    config.addinivalue_line("markers", "mock_only: runs only in mock mode")
    config.addinivalue_line("markers", "slow: long-running inference call")


def pytest_collection_modifyitems(config, items):
    if TESTBED_MODE == "live":
        skip_mock = pytest.mark.skip(reason="mock-only test skipped in live mode")
        for item in items:
            if "mock_gateway_client_with_empty" in item.fixturenames or \
               "mock_gateway_client_with_errors" in item.fixturenames:
                item.add_marker(skip_mock)


@pytest.fixture(scope="session")
def is_live():
    return TESTBED_MODE == "live"


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def gateway_dir(project_root) -> Path:
    return project_root / "gateway"


def _ensure_gateway_path(gateway_dir):
    gw = str(gateway_dir)
    if gw not in sys.path:
        sys.path.insert(0, gw)
    return gw


def _get_app(gateway_dir):
    _ensure_gateway_path(gateway_dir)
    from router import app
    return app


@pytest.fixture
def gateway_client(gateway_dir, is_live, monkeypatch):
    """FastAPI TestClient with mock or live MAAS backend."""
    if not is_live:
        monkeypatch.setenv("LITELLM_API_BASE", "https://mock-maas.test")
        monkeypatch.setenv("LITELLM_API_KEY", "mock-test-key")

    try:
        from fastapi.testclient import TestClient
        import httpx as _httpx
        app = _get_app(gateway_dir)

        with TestClient(app, raise_server_exceptions=False) as client:
            if not is_live:
                from inference_testbed.mock_maas import MockMaasTransport
                app.state.http_client = _httpx.AsyncClient(
                    transport=MockMaasTransport(), timeout=300.0
                )
            yield client
    except ImportError as e:
        pytest.skip(f"Gateway dependencies not available: {e}")


@pytest.fixture
def mock_gateway_client_with_empty(gateway_dir, monkeypatch):
    """Gateway client where specific models return empty responses."""
    monkeypatch.setenv("LITELLM_API_BASE", "https://mock-maas.test")
    monkeypatch.setenv("LITELLM_API_KEY", "mock-test-key")

    try:
        from fastapi.testclient import TestClient
        import httpx as _httpx
        from inference_testbed.mock_maas import MockMaasTransport
        app = _get_app(gateway_dir)

        with TestClient(app, raise_server_exceptions=False) as client:
            app.state.http_client = _httpx.AsyncClient(
                transport=MockMaasTransport(empty_models={"granite-2b-cpu"}),
                timeout=300.0,
            )
            yield client
    except ImportError as e:
        pytest.skip(f"Gateway dependencies not available: {e}")


@pytest.fixture
def mock_gateway_client_with_errors(gateway_dir, monkeypatch):
    """Gateway client where backends return errors."""
    monkeypatch.setenv("LITELLM_API_BASE", "https://mock-maas.test")
    monkeypatch.setenv("LITELLM_API_KEY", "mock-test-key")

    try:
        from fastapi.testclient import TestClient
        import httpx as _httpx
        from inference_testbed.mock_maas import ConnectErrorTransport
        app = _get_app(gateway_dir)

        with TestClient(app, raise_server_exceptions=False) as client:
            app.state.http_client = _httpx.AsyncClient(
                transport=ConnectErrorTransport(), timeout=300.0
            )
            yield client
    except ImportError as e:
        pytest.skip(f"Gateway dependencies not available: {e}")


@pytest.fixture
def session_id(gateway_client):
    """Create a chat session and return its ID."""
    resp = gateway_client.post("/v1/chat/sessions", json={})
    assert resp.status_code == 200
    return resp.json()["session_id"]


@pytest.fixture
def session_with_doc(gateway_client, session_id):
    """Session with a test document uploaded for RAG."""
    content = (
        "Intel Xeon 6 processors feature Advanced Matrix Extensions (AMX) "
        "for AI inference acceleration. The AMX instruction set provides "
        "hardware-level INT8 and BF16 matrix operations. Gaudi 3 accelerators "
        "offer 96GB HBM2e memory for large model inference."
    )
    import io
    file_obj = io.BytesIO(content.encode("utf-8"))
    resp = gateway_client.post(
        "/v1/documents/upload",
        files={"file": ("test_doc.txt", file_obj, "text/plain")},
    )
    assert resp.status_code == 200
    return session_id


def send_chat_message(client, session_id, message, model_override=None,
                      hardware_override=None, routing_strategy="standard"):
    """Helper to send a chat message and return raw response."""
    body = {"message": message, "routing_strategy": routing_strategy}
    if model_override:
        body["model_override"] = model_override
    if hardware_override:
        body["hardware_override"] = hardware_override
    return client.post(f"/v1/chat/sessions/{session_id}/message", json=body)
