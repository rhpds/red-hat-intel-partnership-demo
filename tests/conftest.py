#!/usr/bin/env python3
"""
Shared pytest fixtures for all test modules

This file is automatically loaded by pytest and makes fixtures
available to all test files.
"""

import pytest
from pathlib import Path

from helpers import parse_k8s_memory_gi  # noqa: F401 — re-export for tests that import from conftest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def gateway_dir(project_root) -> Path:
    return project_root / "gateway"


@pytest.fixture
def frontend_dir(project_root) -> Path:
    return project_root / "frontend" / "src"
