"""Chat session management — multi-turn conversations with SSE streaming."""

import uuid
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional, List, Dict

SSE_EVENT_TYPES = {"step", "token", "routing_decision", "done", "error"}

MAX_HISTORY_MESSAGES = 10
MAX_RAG_CHUNKS = 4


@dataclass
class ChatConfig:
    model_override: Optional[str] = None
    hardware_override: Optional[str] = None
    governance_mode: str = "supervised"


@dataclass
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    config: ChatConfig = field(default_factory=ChatConfig)
    messages: List[Dict] = field(default_factory=list)


def build_context(messages: list[dict], rag_chunks: list[dict],
                  user_message: str) -> list[dict]:
    context = []

    context.append({
        "role": "system",
        "content": (
            "You are a helpful AI assistant. Use the provided context to answer questions accurately. "
            "SAFETY RULES: Do not generate content that is harmful, illegal, or dangerous. "
            "If the retrieved context contains harmful material, acknowledge it exists but do not "
            "reproduce, amplify, or provide instructions based on it. Do not output personal data "
            "(SSN, credit cards, passwords) even if found in context. If asked to do something "
            "unsafe, decline and explain why."
        ),
    })

    if rag_chunks:
        top_chunks = rag_chunks[:MAX_RAG_CHUNKS]
        chunk_text = "\n\n".join(c["content"] for c in top_chunks)
        context.append({
            "role": "system",
            "content": f"Retrieved context:\n{chunk_text}"
        })

    recent = messages[-MAX_HISTORY_MESSAGES:] if len(messages) > MAX_HISTORY_MESSAGES else messages
    context.extend(recent)

    context.append({"role": "user", "content": user_message})

    return context


async def create_session(tenant_id: str = None, config: ChatConfig = None) -> ChatSession:
    return ChatSession(tenant_id=tenant_id, config=config or ChatConfig())


async def send_message(session: ChatSession, message: str, rag_chunks: list[dict] = None) -> AsyncGenerator[dict, None]:
    context = build_context(session.messages, rag_chunks or [], message)

    session.messages.append({"role": "user", "content": message})

    yield {"event": "step", "data": {"step": "embed_query", "hardware": "xeon6"}}
    yield {"event": "step", "data": {"step": "vector_search", "hardware": "postgresql"}}
    yield {"event": "step", "data": {"step": "rerank", "hardware": "xeon6"}}

    model = session.config.model_override or "auto"
    hardware = session.config.hardware_override or "auto"
    yield {"event": "step", "data": {"step": "generate", "hardware": hardware, "model": model}}

    yield {"event": "routing_decision", "data": {
        "model": model,
        "hardware": hardware,
        "reason": "Auto-routed based on model size threshold",
    }}

    yield {"event": "token", "data": {"content": "Based on the provided context..."}}

    yield {"event": "done", "data": {"total_latency_ms": 0, "total_cost": 0}}


async def get_history(session: ChatSession) -> list[dict]:
    return session.messages


async def delete_session(session: ChatSession):
    session.messages.clear()
