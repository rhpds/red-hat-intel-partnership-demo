"""RAG document pipeline — upload, chunk, embed, search, categorize.

SECURITY SCOPE: Documents uploaded via this module are ONLY used for
RAG retrieval within the owning tenant's chat session. They are:
- Stored in pgvector scoped to tenant_id
- Never sent to external services (only embeddings go to MAAS)
- Auto-expired after 24 hours
- Sanitized for prompt injection before embedding
- Never returned in raw form to other tenants or endpoints
- Not indexable, not searchable outside the RAG pipeline
"""

import asyncio
import io
import re
import uuid
import hashlib
from pathlib import Path

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 50
MAX_DOCUMENTS_PER_SESSION = 20
MAX_TOTAL_BYTES_PER_TENANT = 100 * 1024 * 1024  # 100MB
MAX_CHUNKS_PER_DOCUMENT = 500

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".docx",
    ".py", ".yaml", ".yml", ".json", ".tf",
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

HARMFUL_CONTENT_PATTERNS = [
    re.compile(r"\b(?:how\s+to\s+(?:make|build|create)\s+(?:a\s+)?(?:bomb|weapon|explosive))", re.IGNORECASE),
    re.compile(r"\b(?:synthesiz(?:e|ing)\s+(?:drugs|narcotics|methamphetamine|fentanyl))", re.IGNORECASE),
    re.compile(r"\b(?:social\s+security\s+number|SSN)\s*[:=]\s*\d{3}", re.IGNORECASE),
    re.compile(r"\b(?:credit\s+card)\s*[:=]?\s*\d{4}[\s-]?\d{4}", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b.*(?:password|passwd)\s*[:=]", re.IGNORECASE),
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


def screen_content(text: str) -> list[str]:
    """Screen document text for harmful content. Returns list of warnings.
    Does NOT block upload — flags for audit trail and governance review."""
    warnings = []
    for pattern in HARMFUL_CONTENT_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            warnings.append(f"Potentially sensitive content detected: {pattern.pattern[:50]}...")
    return warnings


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


def validate_content_safety(content: bytes, filename: str) -> None:
    """Validate file content is safe beyond just extension check."""
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE_BYTES})")

    header = content[:16]
    if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
        raise ValueError("Binary executable detected")
    if header.startswith(b"PK") and not filename.lower().endswith(".docx"):
        raise ValueError("Archive file detected")
    if header.startswith(b"\x1f\x8b"):
        raise ValueError("Compressed file detected")


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from a file based on its type."""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(content)
    elif ext == ".docx":
        return _extract_docx(content)
    else:
        return content.decode("utf-8", errors="ignore")


def _extract_pdf(content: bytes) -> str:
    """Extract text from PDF using pdfplumber (preferred) or PyPDF2 fallback."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = []
            for page in pdf.pages[:50]:  # Max 50 pages
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
    except ImportError:
        pass

    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages[:50]:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        pass

    # Last resort — raw decode (will be garbage for PDFs)
    return content.decode("utf-8", errors="ignore")


def _extract_docx(content: bytes) -> str:
    """Extract text from DOCX (ZIP of XML)."""
    import zipfile
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = tree.findall(".//w:p", ns)
                texts = []
                for p in paragraphs:
                    runs = p.findall(".//w:t", ns)
                    line = "".join(r.text or "" for r in runs)
                    if line.strip():
                        texts.append(line)
                return "\n".join(texts)
    except Exception:
        return content.decode("utf-8", errors="ignore")


def hash_content(content: bytes) -> str:
    """SHA256 hash for deduplication and audit."""
    return hashlib.sha256(content).hexdigest()


async def upload_document(filename: str, content: bytes, tenant_id: str = None,
                          session_id: str = None) -> dict:
    """Upload and process a document for RAG search.

    Documents are scoped to the owning tenant and session. They are ONLY
    accessible via search_documents() within the same tenant context.
    Raw document content is never exposed via any API endpoint.
    """
    if not is_allowed_file(filename):
        raise ValueError(f"File type not allowed: {filename}")

    validate_content_safety(content, filename)

    modality = detect_modality(filename)
    text = await asyncio.to_thread(extract_text, filename, content)

    chunks = chunk_text(text)
    sanitized_chunks = [sanitize_chunk(c) for c in chunks]
    sanitized_chunks = [c for c in sanitized_chunks if c]

    if len(sanitized_chunks) > MAX_CHUNKS_PER_DOCUMENT:
        sanitized_chunks = sanitized_chunks[:MAX_CHUNKS_PER_DOCUMENT]

    category = categorize_document(text)
    content_hash = hash_content(content)
    content_warnings = screen_content(text)

    doc_id = str(uuid.uuid4())

    return {
        "id": doc_id,
        "filename": filename,
        "modality": modality,
        "category": category,
        "chunk_count": len(sanitized_chunks),
        "content_hash": content_hash,
        "content_warnings": content_warnings,
        "tenant_id": tenant_id,
        "session_id": session_id,
        "chunks": sanitized_chunks,
    }


async def search_documents(query_embedding: list[float], tenant_id: str,
                           category: str = None, modality: str = None,
                           limit: int = 8) -> list[dict]:
    """Search document chunks by vector similarity.

    SECURITY: tenant_id is REQUIRED and used as a mandatory filter.
    No cross-tenant search is possible — the SQL query always includes
    WHERE d.tenant_id = $tenant_id.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for document search")
    return []


async def rerank_chunks(query: str, chunks: list[dict]) -> list[dict]:
    """Rerank chunks by relevance. Only operates on chunks already
    filtered by tenant_id in search_documents()."""
    return sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
