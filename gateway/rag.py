"""RAG document pipeline — upload, chunk, embed, search, categorize."""

import re
import uuid
from pathlib import Path

MAX_FILE_SIZE_MB = 10
MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 50

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".docx",
    ".py", ".yaml", ".yml", ".json", ".sh", ".tf",
    ".png", ".jpg", ".jpeg",
    ".mp3", ".wav", ".m4a",
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi",
    ".sh",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".dll", ".so", ".dylib",
}

MODALITY_MAP = {
    ".pdf": "text", ".txt": "text", ".md": "text", ".docx": "text",
    ".py": "code", ".yaml": "code", ".yml": "code", ".json": "code",
    ".tf": "code",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
}

INJECTION_PATTERNS = [
    re.compile(r"system\s*:\s*ignore\s+all\s+previous", re.IGNORECASE),
    re.compile(r"\[INST\].*?\[/INST\]", re.DOTALL),
    re.compile(r"<\|im_start\|>.*?<\|im_end\|>", re.DOTALL),
    re.compile(r"###\s*(?:System|Instruction)\s*:", re.IGNORECASE),
    re.compile(r"(?:forget|ignore|disregard)\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|context)", re.IGNORECASE),
]


def is_allowed_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return False
    return ext in ALLOWED_EXTENSIONS


def detect_modality(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return MODALITY_MAP.get(ext, "text")


def chunk_text(text: str, max_tokens: int = MAX_CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP_TOKENS) -> list[str]:
    words = text.split()
    if len(words) <= max_tokens:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += max_tokens - overlap
    return chunks


def sanitize_chunk(text: str) -> str:
    result = text
    for pattern in INJECTION_PATTERNS:
        result = pattern.sub("", result)
    result = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", result)
    return result.strip()


def categorize_document(text_sample: str) -> str:
    sample = text_sample[:500].lower()
    if any(w in sample for w in ["revenue", "profit", "fiscal", "quarter", "earnings", "financial"]):
        return "financial"
    if any(w in sample for w in ["api", "endpoint", "deploy", "config", "function", "class", "import"]):
        return "technical"
    if any(w in sample for w in ["agreement", "license", "warranty", "liability", "terms"]):
        return "legal"
    if any(w in sample for w in ["feature", "release", "version", "product", "specification"]):
        return "product"
    if any(w in sample for w in ["ticket", "issue", "bug", "error", "support", "incident"]):
        return "support"
    if any(w in sample for w in ["study", "hypothesis", "methodology", "findings", "abstract"]):
        return "research"
    if any(w in sample for w in ["def ", "class ", "import ", "from ", "function", "const ", "var "]):
        return "code"
    return "other"


async def upload_document(filename: str, content: bytes, tenant_id: str = None) -> dict:
    if not is_allowed_file(filename):
        raise ValueError(f"File type not allowed: {filename}")

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)")

    modality = detect_modality(filename)
    text = content.decode("utf-8", errors="ignore")

    chunks = chunk_text(text)
    sanitized_chunks = [sanitize_chunk(c) for c in chunks]
    sanitized_chunks = [c for c in sanitized_chunks if c]

    category = categorize_document(text)

    doc_id = str(uuid.uuid4())

    return {
        "id": doc_id,
        "filename": filename,
        "modality": modality,
        "category": category,
        "chunk_count": len(sanitized_chunks),
        "chunks": sanitized_chunks,
    }


async def search_documents(query_embedding: list[float], tenant_id: str = None,
                           category: str = None, modality: str = None,
                           limit: int = 8) -> list[dict]:
    return []


async def rerank_chunks(query: str, chunks: list[dict]) -> list[dict]:
    return sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
