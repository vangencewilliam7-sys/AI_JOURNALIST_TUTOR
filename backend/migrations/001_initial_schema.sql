-- Migration 001: Initial Schema

CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Conversation Sessions
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id UUID,
    topic TEXT,
    status TEXT DEFAULT 'active',
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Conversation Messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    input_source TEXT DEFAULT 'text',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Knowledge Sources
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    url TEXT,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Knowledge Chunks
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID,
    source_id UUID REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    location_marker TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Interview Scripts
CREATE TABLE IF NOT EXISTS interview_scripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id UUID,
    full_script JSONB NOT NULL,
    themes JSONB DEFAULT '[]'::jsonb,
    questions_completed INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    current_followup_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. Course Blueprints (formerly tacit_knowledge_reports)
CREATE TABLE IF NOT EXISTS course_blueprints (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id UUID,
    course_title TEXT,
    tutor_name TEXT,
    tutor_motivation TEXT,
    target_audience TEXT,
    north_star_outcome TEXT,
    learning_format TEXT,
    summary TEXT,
    total_modules INTEGER,
    course_modules JSONB DEFAULT '[]'::jsonb,
    learning_outcomes JSONB DEFAULT '[]'::jsonb,
    friction_points JSONB DEFAULT '[]'::jsonb,
    teaching_frameworks JSONB DEFAULT '[]'::jsonb,
    edge_cases JSONB DEFAULT '[]'::jsonb,
    evaluation_methods JSONB DEFAULT '[]'::jsonb,
    anti_patterns JSONB DEFAULT '[]'::jsonb,
    marketing_hooks JSONB DEFAULT '[]'::jsonb,
    messages_analyzed INTEGER,
    questions_completed INTEGER,
    total_questions INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ks_user_id ON knowledge_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_kc_user_id ON knowledge_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_is_user_id ON interview_scripts(user_id);
CREATE INDEX IF NOT EXISTS idx_cb_session_id ON course_blueprints(session_id);
CREATE INDEX IF NOT EXISTS idx_cb_user_id ON course_blueprints(user_id);

-- RAG Match Function
CREATE OR REPLACE FUNCTION match_knowledge_chunks (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  p_user_id uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  location_marker text,
  similarity float,
  knowledge_sources jsonb
)
LANGUAGE sql STABLE
AS $$
  SELECT
    kc.id,
    kc.content,
    kc.location_marker,
    1 - (kc.embedding <=> query_embedding) AS similarity,
    jsonb_build_object(
      'title', ks.title,
      'source_type', ks.source_type
    ) as knowledge_sources
  FROM knowledge_chunks kc
  JOIN knowledge_sources ks ON kc.source_id = ks.id
  WHERE 
    kc.user_id = p_user_id AND
    1 - (kc.embedding <=> query_embedding) > match_threshold
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
$$;
