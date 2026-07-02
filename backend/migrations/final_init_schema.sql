-- ==========================================
-- FINAL COMPLETE SCHEMA FOR AI JOURNALIST & TUTOR
-- Run this entire script in Supabase SQL Editor to spin up a fresh instance.
-- ==========================================

-- Enable pgvector extension for RAG embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ------------------------------------------------------------------------------
-- 1. EXPERTS (Linked to Supabase Auth)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experts (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    domain TEXT,
    stream_type TEXT,
    course_title TEXT,
    course_description TEXT,
    target_audience TEXT,
    expertise_streams TEXT,
    years_of_experience INTEGER,
    short_bio TEXT,
    linkedin_url TEXT,
    archetype TEXT DEFAULT 'balanced',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. EXPERT PROFILE (Synthesized traits and system prompts)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expert_profile (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    persona_traits JSONB DEFAULT '[]'::jsonb,
    war_stories JSONB DEFAULT '[]'::jsonb,
    mental_models JSONB DEFAULT '[]'::jsonb,
    edge_cases JSONB DEFAULT '[]'::jsonb,
    pattern_breaks JSONB DEFAULT '[]'::jsonb,
    tacit_insights JSONB DEFAULT '[]'::jsonb,
    teaching_style TEXT,
    linguistic_fingerprint JSONB DEFAULT '{}'::jsonb,
    system_prompt TEXT,
    structured_tacit_notes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 3. INTERVIEW SESSIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    iteration_number INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    script JSONB DEFAULT '{}'::jsonb,
    raw_transcript TEXT DEFAULT '',
    session_synthesis JSONB DEFAULT '{}'::jsonb,
    live_scratchpad JSONB DEFAULT '{}'::jsonb,
    current_block TEXT DEFAULT 'Block 1',
    snapshot JSONB DEFAULT '{}'::jsonb,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 4. HOMEWORK LEDGER
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS homework_ledger (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    iteration_number INTEGER DEFAULT 1,
    ai_open_loops JSONB DEFAULT '[]'::jsonb,
    human_manual_notes TEXT DEFAULT '',
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 5. CURRICULUM BLUEPRINTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_blueprints (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    course_title TEXT,
    report_title TEXT,
    course_modules JSONB DEFAULT '[]'::jsonb,
    structured_tacit_notes JSONB DEFAULT '[]'::jsonb,
    iteration_last_updated INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 6. EXPERT TACIT INSIGHTS (Searchable verified insights)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expert_tacit_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    classification TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    expert_quote TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 7. TOPIC PROGRESS (Tracks component completion)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS topic_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    module_id TEXT NOT NULL,
    module_title TEXT,
    topic_id TEXT NOT NULL,
    topic_title TEXT,
    components JSONB DEFAULT '{}'::jsonb,
    is_complete BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 8. KNOWLEDGE SOURCES (RAG Documents)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    title TEXT,
    url_or_identifier TEXT,
    author_or_channel TEXT,
    global_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- (Linking interview_sessions to knowledge_sources now that it exists)
ALTER TABLE interview_sessions 
ADD COLUMN live_transcript_source_id UUID REFERENCES knowledge_sources(id) ON DELETE SET NULL;

-- ------------------------------------------------------------------------------
-- 9. KNOWLEDGE CHUNKS (RAG Vectors)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    chunk_index INT,
    content TEXT NOT NULL,
    location_marker TEXT,
    embedding VECTOR(1536)
);

-- ------------------------------------------------------------------------------
-- 10. TACIT KNOWLEDGE REPORTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tacit_knowledge_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id_fk UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    report_title TEXT,
    structured_tacit_notes JSONB DEFAULT '[]'::jsonb,
    persona_snapshot JSONB DEFAULT '{}'::jsonb,
    course_structure JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 11. SUBMITTED MATERIALS (Evidence Verification)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS submitted_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    iteration_number INT DEFAULT 1,
    loop_topic TEXT NOT NULL,
    material_type TEXT NOT NULL CHECK (material_type IN ('file', 'url', 'text')),
    content_or_url TEXT NOT NULL,
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    verification_insights JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 12. KNOWLEDGE ITEMS (Atomic Tacit Knowledge Extracted Live)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    knowledge_type TEXT NOT NULL,
    topic TEXT,
    title TEXT,
    raw_quote TEXT NOT NULL, 
    clean_insight TEXT,
    signal TEXT,
    interpretation TEXT,
    expert_action TEXT,
    decision_rule TEXT,
    workflow_step JSONB DEFAULT '{}'::jsonb,
    source_or_origin TEXT,
    confidence TEXT DEFAULT 'medium',
    validation_status TEXT DEFAULT 'unvalidated',
    missing_fields TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 13. RAG MATCHING FUNCTION
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 14. ROW LEVEL SECURITY (RLS) & POLICIES
-- ------------------------------------------------------------------------------
ALTER TABLE experts ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE homework_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE curriculum_blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_tacit_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE tacit_knowledge_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE submitted_materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own experts" ON experts FOR ALL USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can manage own homework" ON homework_ledger FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);
CREATE POLICY "Users can manage own insights" ON expert_tacit_insights FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);
CREATE POLICY "Users can manage own progress" ON topic_progress FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);
CREATE POLICY "Users can view own blueprints" ON curriculum_blueprints FOR SELECT USING (auth.uid() = expert_id);
CREATE POLICY "Users can view own profiles" ON expert_profile FOR SELECT USING (auth.uid() = expert_id);
CREATE POLICY "Users can view own reports" ON tacit_knowledge_reports FOR SELECT USING (auth.uid() = expert_id);
CREATE POLICY "Users can view own sessions" ON interview_sessions FOR SELECT USING (auth.uid() = expert_id);
CREATE POLICY "Users can manage own submitted materials" ON submitted_materials FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);
CREATE POLICY "Users can manage own knowledge items" ON knowledge_items FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);

-- ------------------------------------------------------------------------------
-- 15. PERFORMANCE INDEXING
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_expert ON interview_sessions(expert_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_session ON curriculum_blueprints(session_id);
CREATE INDEX IF NOT EXISTS idx_insights_session ON expert_tacit_insights(session_id);
CREATE INDEX IF NOT EXISTS idx_progress_session ON topic_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON knowledge_chunks(source_id);
