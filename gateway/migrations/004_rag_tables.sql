-- Migration 004: RAG document pipeline + chat sessions
-- Adds pgvector for semantic search, document storage, and chat history
-- pgvector is optional: if not installed, RAG tables use TEXT instead of vector columns

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pgvector not available — RAG embeddings will be stored as TEXT';
END
$$;

-- Document storage
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    session_id UUID,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    modality VARCHAR(20) NOT NULL DEFAULT 'text',
    category VARCHAR(50),
    chunk_count INTEGER DEFAULT 0,
    file_size_bytes BIGINT DEFAULT 0,
    uploaded_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT now() + INTERVAL '24 hours'
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_session ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_expires ON documents(expires_at);

-- Document chunks with embeddings (vector type if pgvector available, otherwise TEXT fallback)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            modality VARCHAR(20) NOT NULL DEFAULT 'text',
            embedding vector(768),
            metadata JSONB DEFAULT '{}'
        );
    ELSE
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            modality VARCHAR(20) NOT NULL DEFAULT 'text',
            embedding TEXT,
            metadata JSONB DEFAULT '{}'
        );
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);

-- Chat sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    created_at TIMESTAMPTZ DEFAULT now(),
    model_override VARCHAR(100),
    hardware_override VARCHAR(20),
    governance_mode VARCHAR(20) DEFAULT 'supervised'
);

CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON chat_sessions(tenant_id);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    routing_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id, created_at);
