"""
Shared utilities for the inference gateway.

Sanitization and similarity functions used across router, chat,
and semantic_router modules.
"""

import math
import re


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
