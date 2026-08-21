"""
Shared utilities for the inference gateway.

Sanitization, similarity, and rate limiting functions used across
router, runs, chat, and semantic_router modules.
"""

import math
import os
import re
import time
from collections import defaultdict
from fastapi import HTTPException


_rate_limits: dict = defaultdict(list)
_rate_limit_last_cleanup = 0.0
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "85"))
_RATE_LIMIT_MAX_KEYS = 10000


def check_rate_limit(client_ip: str, tenant_id: str = ""):
    if not RATE_LIMIT_RPM:
        return
    key = f"{tenant_id}:{client_ip}" if tenant_id else client_ip
    now = time.time()
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < 60]
    if len(_rate_limits[key]) >= RATE_LIMIT_RPM:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _rate_limits[key].append(now)
    global _rate_limit_last_cleanup
    if now - _rate_limit_last_cleanup > 60:
        _rate_limit_last_cleanup = now
        stale = [k for k, v in _rate_limits.items() if not v]
        for k in stale:
            del _rate_limits[k]
        if len(_rate_limits) > _RATE_LIMIT_MAX_KEYS:
            _rate_limits.clear()


def sanitize_prompt(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to mitigate prompt injection in templated LLM calls."""
    if not text:
        return ""
    text = text[:max_length]
    text = re.sub(
        r'(?i)(system\s*:|assistant\s*:|<<\s*SYS\s*>>|<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\])',
        '[filtered]',
        text,
    )
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


def sanitize_chunk(text: str) -> str:
    """Sanitize RAG chunk text — same as sanitize_prompt plus context break markers."""
    text = sanitize_prompt(text)
    text = re.sub(r'===\s*END\s+CONTEXT\s*===', '[filtered]', text)
    return text


def cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
