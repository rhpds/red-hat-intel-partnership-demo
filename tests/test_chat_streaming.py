#!/usr/bin/env python3
"""Stage 14: Chat & Streaming — TDD RED phase.

Tests for chat sessions, SSE streaming, context management, and model switching.
All tests should FAIL until gateway/chat.py is implemented.
"""

import pytest
from pathlib import Path


@pytest.fixture
def chat_module(project_root):
    import importlib.util
    spec = importlib.util.spec_from_file_location("chat", project_root / "gateway" / "chat.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── Chat Module Structure ───


class TestChatModuleExists:

    def test_chat_module_loads(self, chat_module):
        assert chat_module is not None

    def test_has_create_session(self, chat_module):
        assert hasattr(chat_module, "create_session")

    def test_has_send_message(self, chat_module):
        assert hasattr(chat_module, "send_message")

    def test_has_get_history(self, chat_module):
        assert hasattr(chat_module, "get_history")

    def test_has_delete_session(self, chat_module):
        assert hasattr(chat_module, "delete_session")

    def test_has_build_context(self, chat_module):
        assert hasattr(chat_module, "build_context")


# ─── SSE Event Types ───


class TestSSEEventTypes:

    def test_defines_step_event(self, chat_module):
        assert "step" in chat_module.SSE_EVENT_TYPES

    def test_defines_token_event(self, chat_module):
        assert "token" in chat_module.SSE_EVENT_TYPES

    def test_defines_routing_event(self, chat_module):
        assert "routing_decision" in chat_module.SSE_EVENT_TYPES

    def test_defines_done_event(self, chat_module):
        assert "done" in chat_module.SSE_EVENT_TYPES


# ─── Context Building ───


class TestContextBuilding:

    def test_build_context_with_no_history(self, chat_module):
        context = chat_module.build_context(
            messages=[],
            rag_chunks=[],
            user_message="Hello"
        )
        assert isinstance(context, list)
        assert any(m["role"] == "user" and m["content"] == "Hello" for m in context)

    def test_build_context_includes_history(self, chat_module):
        history = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI is..."},
        ]
        context = chat_module.build_context(
            messages=history,
            rag_chunks=[],
            user_message="Tell me more"
        )
        assert len([m for m in context if m["role"] == "user"]) == 2

    def test_build_context_includes_rag_chunks(self, chat_module):
        chunks = [
            {"content": "Revenue grew 12% in Q3.", "score": 0.95},
            {"content": "The product launched in June.", "score": 0.87},
        ]
        context = chat_module.build_context(
            messages=[],
            rag_chunks=chunks,
            user_message="What about revenue?"
        )
        context_text = " ".join(m["content"] for m in context)
        assert "Revenue grew 12%" in context_text

    def test_context_limits_history(self, chat_module):
        history = [{"role": "user", "content": f"Message {i}"} for i in range(20)]
        context = chat_module.build_context(
            messages=history,
            rag_chunks=[],
            user_message="Latest"
        )
        user_messages = [m for m in context if m["role"] == "user"]
        assert len(user_messages) <= 11

    def test_context_limits_rag_chunks(self, chat_module):
        chunks = [{"content": f"Chunk {i}", "score": 0.9 - i * 0.01} for i in range(10)]
        context = chat_module.build_context(
            messages=[],
            rag_chunks=chunks,
            user_message="Search"
        )
        context_text = " ".join(m["content"] for m in context)
        assert "Chunk 0" in context_text
        assert "Chunk 9" not in context_text


# ─── Safety System Prompt ───


class TestSafetyPrompt:

    def test_context_has_safety_rules(self, chat_module):
        context = chat_module.build_context([], [], "hello")
        system_msg = [m for m in context if m["role"] == "system"][0]
        assert "SAFETY" in system_msg["content"]

    def test_context_blocks_pii_reproduction(self, chat_module):
        context = chat_module.build_context([], [], "hello")
        system_msg = [m for m in context if m["role"] == "system"][0]
        assert "personal data" in system_msg["content"].lower() or "credentials" in system_msg["content"].lower()

    def test_context_blocks_harmful_content(self, chat_module):
        context = chat_module.build_context([], [], "hello")
        system_msg = [m for m in context if m["role"] == "system"][0]
        assert "harmful" in system_msg["content"].lower()


# ─── Model Override ───


class TestModelOverride:

    def test_default_is_auto(self, chat_module):
        config = chat_module.ChatConfig()
        assert config.model_override is None
        assert config.hardware_override is None

    def test_can_set_model_override(self, chat_module):
        config = chat_module.ChatConfig(model_override="granite-2b-cpu")
        assert config.model_override == "granite-2b-cpu"

    def test_can_set_hardware_override(self, chat_module):
        config = chat_module.ChatConfig(hardware_override="xeon6")
        assert config.hardware_override == "xeon6"

    def test_can_set_governance_mode(self, chat_module):
        config = chat_module.ChatConfig(governance_mode="locked")
        assert config.governance_mode == "locked"


# ─── Validation Matrix Tracker ───


def test_validation_matrix_chat_streaming(project_root):
    matrix_file = project_root / "tests" / "validation_matrix.yaml"
    if not matrix_file.exists():
        pytest.skip("Validation matrix not found")
    assert True, "See individual tests for validation matrix criteria"
