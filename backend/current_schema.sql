-- ==========================================
-- PROTOTYPE SCHEMA FOR AI JOURNALIST & TUTOR
-- Run this entire script in Supabase SQL Editor
-- ==========================================

-- Enable pgvector extension for RAG embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Conversation Sessions (Tracks the high-level interview session)
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    topic TEXT,
    status TEXT DEFAULT 'active',
    domain TEXT DEFAULT 'Tutor',
    total_messages INT DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Interview Scripts (Stores the generated script and tutor profile)
CREATE TABLE IF NOT EXISTS interview_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    tutor_profile JSONB DEFAULT '{}'::jsonb,
    themes JSONB DEFAULT '[]'::jsonb,
    full_script JSONB DEFAULT '{}'::jsonb,
    total_questions INT DEFAULT 0,
    questions_completed INT DEFAULT 0,
    tangent_budget_remaining INT DEFAULT 2,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Conversation Messages (Tracks the turn-by-turn chat)
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    message_index INT NOT NULL,
    role TEXT NOT NULL, -- 'ai' or 'expert'
    content TEXT NOT NULL,
    input_source TEXT DEFAULT 'text',
    metadata JSONB, -- Stores decision logic / internal monologue
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Tacit Knowledge Reports (Stores the final synthesized output)
CREATE TABLE IF NOT EXISTS tacit_knowledge_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    report_title TEXT,
    expert_domain TEXT,
    interview_depth_score INT DEFAULT 0,
    total_insights_extracted INT DEFAULT 0,
    summary TEXT,
    tacit_insights JSONB DEFAULT '[]'::jsonb,
    mental_models JSONB DEFAULT '[]'::jsonb,
    pattern_breaks JSONB DEFAULT '[]'::jsonb,
    war_stories JSONB DEFAULT '[]'::jsonb,
    knowledge_gaps JSONB DEFAULT '[]'::jsonb,
    tutor_persona JSONB DEFAULT '{}'::jsonb,
    course_structure JSONB DEFAULT '{}'::jsonb,
    teaching_philosophy JSONB DEFAULT '{}'::jsonb,
    personal_journey JSONB DEFAULT '{}'::jsonb,
    messages_analyzed INT DEFAULT 0,
    questions_completed INT DEFAULT 0,
    total_questions INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Knowledge Sources (Tracks uploaded documents / YouTube links for RAG)
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL, -- e.g., 'youtube', 'pdf'
    title TEXT,
    url_or_identifier TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. Knowledge Chunks (Stores the vector embeddings for RAG)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    chunk_index INT,
    content TEXT NOT NULL,
    location_marker TEXT,
    embedding VECTOR(1536) -- 1536 dimensions for text-embedding-3-small
);

-- ==========================================
-- RAG MATCHING FUNCTION
-- ==========================================
DROP FUNCTION IF EXISTS match_knowledge_chunks(vector, float, int);

CREATE OR REPLACE FUNCTION match_knowledge_chunks(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  content text,
  location_marker text,
  similarity float,
  knowledge_sources jsonb
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    kc.id,
    kc.content,
    kc.location_marker,
    1 - (kc.embedding <=> query_embedding) AS similarity,
    to_jsonb(ks.*) as knowledge_sources
  FROM knowledge_chunks kc
  JOIN knowledge_sources ks ON ks.id = kc.source_id
  WHERE 1 - (kc.embedding <=> query_embedding) > match_threshold
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
