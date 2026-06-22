CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS experts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    iteration_number INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    script JSONB DEFAULT '{}'::jsonb,
    raw_transcript TEXT DEFAULT '',
    session_synthesis JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS homework_ledger (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID NOT NULL,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    iteration_number INTEGER DEFAULT 1,
    ai_open_loops JSONB DEFAULT '[]'::jsonb,
    human_manual_notes TEXT DEFAULT '',
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS curriculum_blueprints (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    course_modules JSONB DEFAULT '[]'::jsonb,
    iteration_last_updated INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    title TEXT,
    url_or_identifier TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    chunk_index INT,
    content TEXT NOT NULL,
    location_marker TEXT,
    embedding VECTOR(1536)
);
